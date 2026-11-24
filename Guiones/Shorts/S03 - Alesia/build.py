"""S03 Alesia — render propio cuadro a cuadro (mapa neón + dron Blender + Stick 3D).
python build.py --prep          -> recortes de capas, mapa de la Galia y bases del mapa local (en _prep/)
python build.py --frame 1.2     -> un cuadro de prueba (_prep/test_XX.jpg)
python build.py                 -> sfx.wav + Render/Shorts/S03_Alesia.mp4 + S03_upload.mp4
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageChops
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CAP = os.path.join(ROOT, "Imagenes", "Shorts", "S03", "capas")
T = os.path.join(HERE, "terreno"); R3 = os.path.join(HERE, "render3d"); PREP = os.path.join(HERE, "_prep")
NE1 = os.path.join(ROOT, "Recursos", "naturalearth", "NE1_HR_LC_SR_W_DR", "NE1_HR_LC_SR_W_DR.tif")
SHP = os.path.join(ROOT, "Recursos", "naturalearth", "ne_10m_admin_0_countries", "ne_10m_admin_0_countries.shp")
FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FONT = os.environ.get("S03_FONT", r"C:\Windows\Fonts\ariblk.ttf")
HFONT = os.environ.get("S03_HFONT", FONT); SFONT = os.environ.get("S03_SFONT", FONT)
HSTROKE = int(os.environ.get("S03_HSTROKE", 13)); SSTROKE = int(os.environ.get("S03_SSTROKE", 11))
W, H, FPS = 1080, 1920, 30
YEL, WHITE = (255, 214, 40), (255, 255, 255)
RED_IN, RED_OUT, BLUE = (255, 70, 40), (255, 40, 30), (70, 160, 255)

TL = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
SC = {s["id"]: (s["start"], s["start"] + s["dur"]) for s in TL["timeline"]}
WORDS = TL["words"]; TOTAL = TL["total"] + 0.6
def wt(scene, word, n=0):
    ws = [w for w in WORDS if w["scene"] == scene and w["w"].lower().strip(".,?'") == word.lower()]
    return ws[n]["s"]

# ---------------- utilidades ----------------
def ease(x, kind="cubic"):
    x = min(1.0, max(0.0, x))
    if kind == "back":
        c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == "sine": return -(math.cos(math.pi * x) - 1) / 2
    if kind == "inout": return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind="inout"): return ease((t - t0) / max(1e-6, t1 - t0), kind)

def cutout(path, thr=245):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).copy()
    white = (a[..., :3] >= thr).all(-1)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    alpha = np.asarray(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    a[..., 3] = alpha
    out = Image.fromarray(a); return out.crop(out.getbbox())

# ---------------- PREP ----------------
def prep():
    os.makedirs(PREP, exist_ok=True)
    for f in os.listdir(CAP):
        if f.startswith(("ic_", "char_")) and f.endswith(".png"):
            cutout(os.path.join(CAP, f)).save(os.path.join(PREP, "cut_" + f)); print("cut", f)
    # --- mapa local: base oscura + oppidum azul / gris, con relleno por reflejo para zoom/temblor ---
    meta = json.load(open(os.path.join(T, "meta.json")))
    src = Image.open(os.path.join(T, "color.png")).convert("RGB")
    src = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(src).enhance(0.9)).enhance(1.15)).enhance(0.62)
    Hm = np.load(os.path.join(T, "height.npy")); cx, cy = meta["center_px"]
    hc = Hm[int(cy), int(cx)]
    lab, _ = ndimage.label(Hm > hc - 16); m = lab == lab[int(cy), int(cx)]
    m = ndimage.binary_closing(m, iterations=4)
    mk = Image.fromarray((m * 255).astype(np.uint8)).resize(src.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    edge = ImageChops.subtract(mk, mk.filter(ImageFilter.MinFilter(9))).filter(ImageFilter.GaussianBlur(2))
    def tint(col, a_fill, a_edge):
        im = Image.composite(Image.new("RGB", src.size, col), src, mk.point(lambda v: int(v * a_fill)))
        return Image.composite(Image.new("RGB", src.size, tuple(min(255, c + 90) for c in col)), im, edge.point(lambda v: min(255, int(v * a_edge))))
    P = 700
    for name, im in (("local_blue", tint(BLUE, 0.42, 1.6)), ("local_grey", tint((140, 140, 150), 0.38, 1.0))):
        a = np.pad(np.asarray(im), ((P, P), (P, P), (0, 0)), mode="reflect")
        Image.fromarray(a).save(os.path.join(PREP, name + ".png")); print(name)
    # --- Galia: relieve NE1 oscuro + máscara Francia/Bélgica/Luxemburgo/Suiza (≈ Galia) ---
    Image.MAX_IMAGE_PIXELS = None
    LON0, LON1, LAT1, LAT0 = -5.5, 10.5, 57.0, 37.6
    ne = Image.open(NE1)
    box = (int((LON0 + 180) * 60), int((90 - LAT1) * 60), int((LON1 + 180) * 60), int((90 - LAT0) * 60))
    g = ne.crop(box).convert("RGB"); GW, GH = 1620, 2880
    g = g.resize((GW, GH), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 60, 2))
    g = ImageEnhance.Brightness(ImageEnhance.Color(g).enhance(0.75)).enhance(0.55)
    g.save(os.path.join(PREP, "gaul_base.png"))
    import shapefile
    rd = shapefile.Reader(SHP); fields = [f[0] for f in rd.fields[1:]]; ia = fields.index("ADMIN")
    mask = Image.new("L", (GW, GH), 0); d = ImageDraw.Draw(mask)
    G = lambda lon, lat: ((lon - LON0) / (LON1 - LON0) * GW, (LAT1 - lat) / (LAT1 - LAT0) * GH)
    for sr in rd.iterShapeRecords():
        if sr.record[ia] not in ("France", "Belgium", "Luxembourg", "Switzerland"): continue
        pts = sr.shape.points; parts = list(sr.shape.parts) + [len(pts)]
        for a_, b_ in zip(parts, parts[1:]):
            ring = pts[a_:b_]; mlon = np.mean([p[0] for p in ring]); mlat = np.mean([p[1] for p in ring])
            if not (LON0 < mlon < LON1 and 41.5 < mlat < LAT1): continue
            if mlon > 8.3 and mlat < 43.3: continue            # Córcega
            d.polygon([G(*p) for p in ring], fill=255)
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(7)))
    glow = Image.new("RGB", (GW, GH), (0, 0, 0)); glow.paste(BLUE, mask=edge)
    glow = ImageChops.add(glow.filter(ImageFilter.GaussianBlur(14)), glow.filter(ImageFilter.GaussianBlur(5)))
    lit = Image.composite(Image.new("RGB", (GW, GH), (40, 110, 220)), g, mask.point(lambda v: int(v * 0.30)))
    lit = ImageChops.add(lit, glow); lit = ImageChops.add(lit, ImageChops.add(glow, glow))
    lit.paste((225, 240, 255), mask=edge.point(lambda v: int(v * 0.55)))
    lit.save(os.path.join(PREP, "gaul_lit.png"))
    json.dump({"GW": GW, "GH": GH, "lon0": LON0, "lon1": LON1, "lat0": LAT0, "lat1": LAT1, "pad": P}, open(os.path.join(PREP, "meta.json"), "w"))
    print("prep ok")

# ---------------- datos por worker ----------------
D = {}
def init():
    if D: return
    pm = json.load(open(os.path.join(PREP, "meta.json"))); D["pm"] = pm
    D["meta"] = meta = json.load(open(os.path.join(T, "meta.json")))
    rings = json.load(open(os.path.join(T, "rings.json")))
    cx, cy = meta["center_px"]; mpp = meta["mpp"]
    order = [(90 - i) % 360 for i in range(360)]           # empieza al norte y gira en sentido horario
    for k in ("inner", "outer"):
        r = rings[k]; D[k] = [(cx + r[i][0] / mpp, cy - r[i][1] / mpp) for i in order]
    D["c"] = (cx, cy)
    for n in ("local_blue", "local_grey", "gaul_base", "gaul_lit"):
        D[n] = Image.open(os.path.join(PREP, n + ".png")).convert("RGB")
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((-260, -180, W + 260, H + 180), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(170)).point(lambda v: int(95 + v * 160 / 255))
    D["vig"] = Image.merge("RGB", (vig, vig, vig))
    D["icons"] = {}; D["texts"] = {}; D["bg"] = {}; D["r3"] = {}
    D["subs"] = build_subs()

def icon(name, size, flip=False):
    key = (name, int(size), flip)
    if key not in D["icons"]:
        im = Image.open(os.path.join(PREP, "cut_" + name + ".png"))
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = size / max(im.size); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        sh = im.getchannel("A").point(lambda v: int(v * 0.55)).filter(ImageFilter.GaussianBlur(max(2, size / 30)))
        D["icons"][key] = (im, sh)
        if len(D["icons"]) > 120: D["icons"].clear(); D["icons"][key] = (im, sh)
    return D["icons"][key]

def put_icon(can, name, size, xy, t, t0, t1=None, flip=False, bob=True):
    """Ícono con 'pop' de entrada (easeOutBack) y salida encogiendo."""
    if t < t0 or (t1 is not None and t >= t1 + 0.2): return
    k = ease((t - t0) / 0.28, "back")
    if t1 is not None and t > t1: k *= 1 - ease((t - t1) / 0.2)
    if k <= 0.03: return
    sz = size * k if k < 0.999 or k > 1.001 else size
    im, sh = icon(name, round(sz / 4) * 4 if abs(k - 1) > 1e-3 else size, flip)
    x, y = xy
    if bob: y += 5 * math.sin(2 * math.pi * 0.7 * (t - t0))
    x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    can.paste((0, 0, 0), (x0 + int(size / 24), y0 + int(size / 14)), sh)
    can.paste(im, (x0, y0), im)

def text_img(s, size, fill, stroke=10, font=None):
    font = font or FONT; key = (s, size, fill, stroke, font)
    if key not in D["texts"]:
        f = ImageFont.truetype(font, size); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
        ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        D["texts"][key] = im
    return D["texts"][key]

def put_text(can, s, size, fill, cx, cy, t, t0, stroke=10, pop=True, font=None):
    im = text_img(s, size, fill, stroke, font)
    if pop and t - t0 < 0.22:
        k = max(0.05, ease((t - t0) / 0.22, "back")); im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
    can.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

# ---------------- titulares y subtítulos ----------------
HEAD = [(0.0, "2 WALLS"), (SC["03"][0], "52 BC"), (SC["04"][0], "INNER LINE"), (SC["05"][0], "\u224815 KM"),
        (SC["06"][0], "RELIEF ARMY"), (SC["07"][0], "OUTER LINE"), (wt("07", "twenty-one"), "\u224821 KM"),
        (SC["08"][0], "BOTH SIDES"), (SC["09"][0], "DITCHES"), (wt("09", "towers"), "& TOWERS"),
        (SC["10"][0], "SURRENDER"), (SC["11"][0], "TRAPPED"), (wt("11", "protected"), "& PROTECTED"),
        (wt("11", "genius"), "GENIUS?"), (wt("11", "or"), "OR DESPERATION?")]
def headline(can, t):
    cur = None
    for t0, s in HEAD:
        if t >= t0: cur = (t0, s)
    if not cur: return
    t0, s = cur; size = 150
    while ImageFont.truetype(HFONT, size).getlength(s) > 960: size -= 6
    put_text(can, s, size, YEL, W / 2, 300, t, t0, stroke=HSTROKE, pop=t0 > 0, font=HFONT)

REPL = {"fifty-two": "52", "fifteen": "15", "twenty-one": "21"}
def build_subs():
    groups = []; cur = []
    for w in WORDS:
        txt = REPL.get(w["w"].lower(), w["w"]).upper()
        if cur and (cur[-1]["scene"] != w["scene"] or len(cur) >= 3 or len(" ".join(c["txt"] for c in cur)) + len(txt) > 15):
            groups.append(cur); cur = []
        cur.append(dict(w, txt=txt))
    groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        end = groups[i + 1][0]["s"] if i + 1 < len(groups) else TOTAL
        end = min(end, SC[g[0]["scene"]][1] if g[-1]["scene"] != "11" else TOTAL)
        end = max(end, g[-1]["e"] + 0.15)
        out.append((g[0]["s"], end, g))
    return out

def subtitle(can, t):
    for s0, s1, g in D["subs"]:
        if s0 <= t < s1: break
    else: return
    hi = max(i for i, w in enumerate(g) if w["s"] <= t + 0.02)
    key = ("sub", tuple(w["txt"] for w in g), hi)
    if key not in D["texts"]:
        f = ImageFont.truetype(SFONT, 80 if SFONT != FONT else 86); sp = f.getlength(" ")
        ws = [f.getlength(w["txt"]) for w in g]; tw = int(sum(ws) + sp * (len(g) - 1)) + 30
        im = Image.new("RGBA", (tw, 140)); d = ImageDraw.Draw(im); x = 15
        for i, w in enumerate(g):
            d.text((x, 20), w["txt"], font=f, fill=YEL if i == hi else WHITE, stroke_width=SSTROKE, stroke_fill=(0, 0, 0)); x += ws[i] + sp
        D["texts"][key] = im
    im = D["texts"][key]
    if im.width > W - 40: im = im.resize((W - 40, int(im.height * (W - 40) / im.width)), Image.BILINEAR)
    can.paste(im, (int(W / 2 - im.width / 2), int(H * 0.70 - im.height / 2)), im)

# ---------------- neón ----------------
class Neon:
    def __init__(self): self.items = []
    def line(self, pts, col, w=7, closed=False, k=1.0): self.items.append(("l", pts, col, w, closed, k))
    def dot(self, xy, col, r, k=1.0): self.items.append(("d", xy, col, r, k))
    def draw(self, can):
        if not self.items: return can
        gl = Image.new("RGB", (W // 2, H // 2)); gd = ImageDraw.Draw(gl)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = pts + [pts[0]] if closed else pts
                gd.line([(x / 2, y / 2) for x, y in p], fill=tuple(int(c * k) for c in col), width=max(3, int(w * 0.9)), joint="curve")
            else:
                _, (x, y), col, r, k = it; r2 = r * 1.4 / 2
                gd.ellipse((x / 2 - r2, y / 2 - r2, x / 2 + r2, y / 2 + r2), fill=tuple(int(c * k) for c in col))
        g1 = gl.filter(ImageFilter.GaussianBlur(10)); g2 = gl.filter(ImageFilter.GaussianBlur(3))
        glow = ImageChops.add(ImageChops.add(g1, g1), g2).resize((W, H), Image.BILINEAR)
        can = ImageChops.add(can, glow); d = ImageDraw.Draw(can)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = pts + [pts[0]] if closed else pts
                d.line(p, fill=tuple(int(lerp(c, 255, 0.15)) for c in col), width=w, joint="curve")
                d.line(p, fill=(255, 235, 225), width=2, joint="curve")
            else:
                _, (x, y), col, r, k = it
                d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=(255, 250, 245))
        return can

def partial(pts, frac):
    """Primeros `frac` de una polilínea (con punta interpolada)."""
    if frac >= 0.999: return pts, True
    n = frac * len(pts); i = int(n)
    if i < 1: return pts[:1], False
    out = pts[:i]; a = pts[i - 1]; b = pts[i % len(pts)]; f = n - i
    out = out + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
    return out, False

def arrow(neon, p0, p1, frac, col, w=10, bend=0.18):
    """Flecha curva neón dibujándose de p0 a p1."""
    if frac <= 0: return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c = (mx - dy * bend, my + dx * bend)
    n = 30; pts = []
    for i in range(int(n * frac) + 1):
        u = i / n; pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]))
    if len(pts) < 2: return
    neon.line(pts, col, w)
    (ax, ay), (bx, by) = pts[-2], pts[-1]; ang = math.atan2(by - ay, bx - ax); L = w * 3.2
    head = [(bx + math.cos(ang + a) * L, by + math.sin(ang + a) * L) for a in (2.6, math.pi, -2.6)]
    neon.line([head[0], (bx + math.cos(ang) * L * 0.6, by + math.sin(ang) * L * 0.6), head[2]], col, w)

# ---------------- mapa local ----------------
def local_map(t, vw, vc=None, grey=0.0):
    pad = D["pm"]["pad"]; cx, cy = vc or D["c"]; vh = vw * H / W; k = 2
    box = ((cx - vw / 2) * k + pad, (cy - vh / 2) * k + pad, (cx + vw / 2) * k + pad, (cy + vh / 2) * k + pad)
    im = D["local_blue"].crop(tuple(int(b) for b in box)).resize((W, H), Image.BILINEAR)
    if grey > 0:
        im = Image.blend(im, D["local_grey"].crop(tuple(int(b) for b in box)).resize((W, H), Image.BILINEAR), min(1, grey))
    im = ImageChops.multiply(im, D["vig"])
    s = W / vw
    S = lambda p: ((p[0] - (cx - vw / 2)) * s, (p[1] - (cy - vh / 2)) * s)
    return im, S, s

def ring_pts(S, name, frac=1.0):
    pts = [S(p) for p in D[name]]
    return partial(pts, frac)

def around(S, name, idx, f=1.0):
    """Punto del anillo `name` en el índice (0 = norte, sentido horario), escalado f desde el centro."""
    cx, cy = D["c"]; p = D[name][idx % 360]
    return S((cx + (p[0] - cx) * f, cy + (p[1] - cy) * f))

def between(S, idx):
    a = D["inner"][idx % 360]; b = D["outer"][idx % 360]
    return S(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))

# ---------------- mapa Galia ----------------
def gaul_geo(lon, lat):
    pm = D["pm"]; return ((lon - pm["lon0"]) / (pm["lon1"] - pm["lon0"]) * pm["GW"], (pm["lat1"] - lat) / (pm["lat1"] - pm["lat0"]) * pm["GH"])

def gaul_map(t, gx, gy, gw, lit):
    pm = D["pm"]; gh = gw * H / W
    gx = min(max(gx, gw / 2), pm["GW"] - gw / 2); gy = min(max(gy, gh / 2), pm["GH"] - gh / 2)
    box = tuple(int(v) for v in (gx - gw / 2, gy - gh / 2, gx + gw / 2, gy + gh / 2))
    if lit >= 0.999: im = D["gaul_lit"].crop(box).resize((W, H), Image.BILINEAR)
    elif lit <= 0.001: im = D["gaul_base"].crop(box).resize((W, H), Image.BILINEAR)
    else: im = Image.blend(D["gaul_base"].crop(box).resize((W, H), Image.BILINEAR), D["gaul_lit"].crop(box).resize((W, H), Image.BILINEAR), lit)
    im = ImageChops.multiply(im, D["vig"]); s = W / gw
    return im, (lambda lon, lat: ((gaul_geo(lon, lat)[0] - (gx - gw / 2)) * s, (gaul_geo(lon, lat)[1] - (gy - gh / 2)) * s))

# ---------------- personajes ----------------
def char_bg(name, t, t0, t1, z0=1.0, z1=1.09):
    if name not in D["bg"]:
        im = Image.open(os.path.join(CAP, name + ".png")).convert("RGB"); s = H * 1.1 / im.height
        D["bg"][name] = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    big = D["bg"][name]; z = lerp(z0, z1, ramp(t, t0, t1, "sine")) * 1.1
    cw, ch = big.width / z * (W / big.width) * (big.width / W), 0
    vw = W * 1.1 / z; vh = H * 1.1 / z; cx, cy = big.width / 2, big.height / 2
    return big.crop((int(cx - vw / 2), int(cy - vh / 2), int(cx + vw / 2), int(cy + vh / 2))).resize((W, H), Image.BILINEAR)

def put_char(can, name, t, t0, h=1120, x=W / 2, flip=False, enter="up"):
    lt = t - t0; im, sh = icon(name, h, flip)
    if im.height != h: pass
    dy = 0; sy = 1.0
    if enter == "up": dy = (1 - ease(lt / 0.38, "back")) * 900
    sy = 1 + 0.012 * math.sin(2 * math.pi * 1.1 * lt)
    if sy != 1: im = im.resize((im.width, int(im.height * sy)), Image.BILINEAR)
    x0 = int(x - im.width / 2); y0 = int(H - 40 - im.height + dy)
    shadow = Image.new("L", (W, H)); ImageDraw.Draw(shadow).ellipse((x - 240, H - 120, x + 240, H - 40), fill=120)
    can.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(20)))
    can.paste(im, (x0, y0), im)

# ---------------- efectos globales ----------------
CUTS = [SC[k][0] for k in sorted(SC)][1:]
SHAKES = []; FLASHES = []
def post(can, t):
    s = 1.0
    for c in CUTS:
        if 0 <= t - c < 0.2: s = 1 + 0.06 * (1 - ease((t - c) / 0.2))
    dx = dy = 0.0
    for t0, amp in SHAKES:
        if 0 <= t - t0 < 0.5:
            a = amp * math.exp(-(t - t0) * 9); dx += a * math.sin(t * 91); dy += a * math.cos(t * 77)
    if s > 1.001 or abs(dx) + abs(dy) > 0.5:
        s = max(s, 1.035); big = can.resize((int(W * s), int(H * s)), Image.BILINEAR)
        x0 = (big.width - W) / 2 + dx; y0 = (big.height - H) / 2 + dy
        can = big.crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
    for t0, dur, a in FLASHES:
        if 0 <= t - t0 < dur:
            can = Image.blend(can, Image.new("RGB", (W, H), (255, 255, 255)), a * (1 - (t - t0) / dur))
    return can

# ---------------- escenas ----------------
SFX = []
def ev(t, kind, vol=None):
    e = {"t": round(t, 3), "type": kind}
    if vol is not None: e["vol"] = vol
    SFX.append(e)

def scene_01_02(t):
    a, b = SC["01"][0], SC["02"][1]
    vw = lerp(560, 640, ramp(t, a, b, "sine"))
    can, S, s = local_map(t, vw, (D["c"][0], D["c"][1] + 10))
    n = Neon()
    pin, _ = ring_pts(S, "inner"); n.line(pin, RED_IN, 6, True, 0.9)
    close = 1.20
    fr = min(1.0, 0.18 + 0.82 * ease(t / close, "inout"))
    pout, closed = ring_pts(S, "outer", fr)
    pulse = 1 + 0.6 * math.exp(-max(0, t - close) * 4) if t >= close else 1
    n.line(pout, RED_OUT, 9, closed, min(1.6, pulse))
    if not closed and len(pout) > 1: n.dot(pout[-1], (255, 200, 160), 26)
    # "second wall": pulso del anillo exterior
    sw = wt("01", "second")
    if sw <= t < sw + 0.6: n.line(pout, RED_OUT, 12, True, 0.8 * (1 - (t - sw) / 0.6))
    # 02: interrogantes azules afuera
    if t >= SC["02"][0]:
        for j, idx in enumerate((292, 68, 0)):
            t0 = wt("02", "keeping") + j * 0.12
            if t >= t0: n.dot(around(S, "outer", idx, 1.2), BLUE, 70, 0.8)
    can = n.draw(can)
    put_icon(can, "ic_gaul", 170, S(D["c"]), t, 0.0)
    army = wt("01", "army")
    for j, idx in enumerate((235, 320, 80)):
        put_icon(can, "ic_army_red", 150, between(S, idx), t, army + j * 0.09)
    if t >= SC["02"][0]:
        for j, idx in enumerate((292, 68, 0)):
            t0 = wt("02", "keeping") + j * 0.12; x, y = around(S, "outer", idx, 1.2)
            if t >= t0: put_text(can, "?", 130, (225, 240, 255), x, y, t, t0, stroke=9)
    return can

def scene_03(t):
    a, b = SC["03"]
    t_cut = wt("03", "Alesia") + 0.05
    if t >= t_cut:
        vw = lerp(700, 600, ramp(t, t_cut, b, "cubic"))
        can, S, s = local_map(t, vw)
        n = Neon(); n.dot(S(D["c"]), RED_OUT, 40, 0.6 + 0.4 * math.sin(t * 9)); can = n.draw(can)
        put_icon(can, "ic_gaul", 170, S(D["c"]), t, t_cut, bob=False)
        return can
    al = (4.50, 47.54)
    tz = wt("03", "trapped")
    zk = ramp(t, tz, t_cut, "inout")
    gc0 = gaul_geo(2.4, 46.6); gc1 = gaul_geo(*al)
    gx, gy = lerp(gc0[0], gc1[0], zk), lerp(gc0[1], gc1[1], zk)
    gw = lerp(lerp(1560, 1420, ramp(t, a, tz, "sine")), 560, zk)
    lit = ramp(t, wt("03", "In"), wt("03", "In") + 0.35, "cubic")
    can, G = gaul_map(t, gx, gy, gw, lit)
    n = Neon(); pa = G(*al)
    tc = wt("03", "Caesar")
    if t >= tc - 0.2:
        n.dot(pa, RED_OUT, 30 + 8 * math.sin(t * 8))
        start = G(6.3, 43.7); fr = ramp(t, tc, tc + 0.6, "cubic")
        arrow(n, start, (lerp(start[0], pa[0], 0.86), lerp(start[1], pa[1], 0.86)), fr, RED_OUT, 11, -0.2)
    ti = wt("03", "inside")
    if t >= ti:
        fr = ramp(t, ti, ti + 0.45, "cubic"); r = 95 * W / gw * 1.0
        pts = [(pa[0] + math.cos(math.radians(-90 + 3.6 * i)) * r * 1.0, pa[1] + math.sin(math.radians(-90 + 3.6 * i)) * r) for i in range(100)]
        p, cl = partial(pts, fr); n.line(p, RED_OUT, 9, cl)
    can = n.draw(can)
    tg = wt("03", "In") + 0.2
    gl = G(1.6, 46.0); put_text(can, "GAUL", 100, (200, 228, 255), gl[0], gl[1], t, tg, stroke=8, font=HFONT)
    if t >= tc - 0.2:
        start = G(6.3, 43.7); fr = ramp(t, tc, tc + 0.6, "cubic")
        put_icon(can, "ic_roman", 150, (lerp(start[0], pa[0], 0.86 * fr), lerp(start[1], pa[1], 0.86 * fr) + 40), t, tc - 0.2, bob=False)
    put_icon(can, "ic_vercingetorix", 220, (pa[0], pa[1] - 190 * 1420 / gw * 0.8), t, wt("03", "Vercingetorix"))
    put_icon(can, "ic_army_blue", 170, (pa[0] - 210 * 1420 / gw * 0.8, pa[1] - 40), t, wt("03", "Gallic"))
    return can

def scene_3d(t):
    a = SC["04"][0]; i = min(204, max(1, int((t - a) * FPS) + 1))
    p = os.path.join(R3, f"f_{i:04d}.png")
    if not os.path.exists(p): p = os.path.join(R3, "still_0150.png")
    im = Image.open(p).convert("RGB")
    arr = np.asarray(im).astype(np.int16)
    m = ((arr[..., 0] > 150) & (arr[..., 1] < 110) & (arr[..., 2] < 100) & (arr[..., 0] - arr[..., 1] > 90)).astype(np.uint8) * 255
    mk = Image.fromarray(m, "L")
    glow = Image.new("RGB", (W, H)); glow.paste(RED_OUT, mask=mk)
    small = glow.resize((W // 2, H // 2), Image.BILINEAR)
    g = ImageChops.add(small.filter(ImageFilter.GaussianBlur(9)), small.filter(ImageFilter.GaussianBlur(3))).resize((W, H), Image.BILINEAR)
    im = ImageChops.add(im, ImageChops.add(g, g))
    vig = D["vig"].point(lambda v: min(255, v + 40)); im = ImageChops.multiply(im, vig)
    tcut = wt("04", "cut")
    put_icon(im, "ic_supplies", 230, (W * 0.74, H * 0.42), t, tcut, SC["04"][1] - 0.1)
    put_icon(im, "ic_blocked", 170, (W * 0.74, H * 0.42), t, wt("04", "supplies"), SC["04"][1] - 0.1, bob=False)
    return im

def scene_06(t):
    a, b = SC["06"]; can = char_bg("bg_relief_army", t, a, b, 1.0, 1.12)
    put_char(can, "char_B_worried", t, a + 0.05, 1100)
    return can

def scene_07(t):
    a, b = SC["07"]
    vw = lerp(680, 600, ramp(t, a, b, "sine"))
    can, S, s = local_map(t, vw)
    n = Neon(); pin, _ = ring_pts(S, "inner"); n.line(pin, RED_IN, 6, True, 0.8)
    t0, t1 = wt("07", "outer"), wt("07", "long") + 0.2
    fr = ramp(t, t0, t1, "inout")
    if fr > 0:
        p, cl = ring_pts(S, "outer", fr); n.line(p, RED_OUT, 9, cl, 1.0 + (0.5 * math.exp(-(t - t1) * 4) if t > t1 else 0))
        if not cl: n.dot(p[-1], (255, 200, 160), 26)
    tf = wt("07", "facing")
    for j, idx in enumerate(range(0, 360, 45)):
        tj = tf + j * 0.05
        if t >= tj:
            p0 = around(S, "outer", idx, 1.04); p1 = around(S, "outer", idx, 1.22)
            arrow(n, p0, p1, ramp(t, tj, tj + 0.25, "cubic"), RED_OUT, 8, 0.0)
    can = n.draw(can)
    put_icon(can, "ic_gaul", 150, S(D["c"]), t, a - 1, bob=False)
    tb = wt("07", "Romans")
    for j, idx in enumerate((235, 320, 80)):
        put_icon(can, "ic_army_red", 130, between(S, idx), t, tb + j * 0.08)
    pb = around(S, "outer", 318, 1.16)
    put_icon(can, "ic_army_blue", 200, (lerp(-200, pb[0], ramp(t, a, a + 0.9, "cubic")), lerp(pb[1] - 200, pb[1], ramp(t, a, a + 0.9, "cubic"))), t, a, bob=True)
    return can

def scene_08(t):
    a, b = SC["08"]; can = char_bg("bg_rampart", t, a, b, 1.0, 1.08)
    flip = False
    for k, tw in enumerate((wt("08", "both"), wt("08", "sides"))):
        if t >= tw: flip = not flip
    put_char(can, "char_C_side", t, a, 1100, flip=flip, enter="up" if t - a < 0.5 else None)
    ta = wt("08", "against")
    if t >= ta:
        n = Neon(); fr = ramp(t, ta, ta + 0.45, "cubic")
        arrow(n, (-60, 760), (330, 900), fr, BLUE, 14, 0.15)
        arrow(n, (W + 60, 760), (W - 330, 900), fr, BLUE, 14, -0.15)
        can = n.draw(can)
        put_icon(can, "ic_army_blue", 220, (120, 620), t, ta, bob=True)
        put_icon(can, "ic_army_blue", 220, (W - 120, 620), t, ta + 0.08, flip=True, bob=True)
    return can

def scene_09(t):
    a, b = SC["09"]; tt = wt("09", "towers")
    if t < tt: can = char_bg("bg_ditch", t, a, tt, 1.0, 1.06)
    else: can = char_bg("bg_tower", t, tt, b, 1.06, 1.0)
    put_char(can, "char_A_neutral", t, a, 1080, x=W * 0.5, enter="up" if t - a < 0.5 else None)
    put_icon(can, "ic_wall", 260, (W * 0.78, H * 0.36), t, tt)
    return can

def scene_10_11(t):
    a10, b10 = SC["10"]; a11 = SC["11"][0]
    tsur = wt("10", "surrendered")
    grey = ramp(t, tsur, tsur + 0.4, "cubic")
    vw = lerp(620, 560, ramp(t, a11, TOTAL, "sine")) if t >= a11 else lerp(640, 620, ramp(t, a10, b10, "sine"))
    can, S, s = local_map(t, vw, grey=grey)
    n = Neon()
    ti = wt("11", "trapped") if t >= a11 else 1e9; tp = wt("11", "protected") if t >= a11 else 1e9
    ki = 0.9 + (0.9 * math.exp(-(t - ti) * 3) if t >= ti else 0)
    ko = 1.0 + (0.9 * math.exp(-(t - tp) * 3) if t >= tp else 0)
    pin, _ = ring_pts(S, "inner"); n.line(pin, RED_IN, 6 if t < ti else 8, True, ki)
    pout, _ = ring_pts(S, "outer"); n.line(pout, RED_OUT, 9 if t < tp else 11, True, ko)
    ta, tf = wt("10", "relief"), wt("10", "failed")
    if a10 <= t < a11:
        for j, idx in enumerate((320, 40, 115)):
            p0 = around(S, "outer", idx, 1.75); p1 = around(S, "outer", idx, 1.08)
            arrow(n, p0, p1, ramp(t, ta + j * 0.07, tf, "cubic"), BLUE, 12, 0.12)
    can = n.draw(can)
    if a10 <= t < a11:
        for j, idx in enumerate((320, 40, 115)):
            put_icon(can, "ic_blocked", 120, around(S, "outer", idx, 1.08), t, tf + j * 0.06, bob=False)
    tv = wt("10", "Vercingetorix")
    put_icon(can, "ic_gaul", 150, S(D["c"]), t, a10 - 1, tv, bob=False)
    put_icon(can, "ic_vercingetorix", 220, S(D["c"]), t, tv, tsur)
    put_icon(can, "ic_sword_down", 210, S(D["c"]), t, tsur + 0.1)
    if t >= a11:
        for j, idx in enumerate((235, 320, 80)):
            put_icon(can, "ic_army_red", 130, between(S, idx), t, a11 + 0.1 + j * 0.08)
        put_icon(can, "ic_roman", 170, between(S, 140), t, tp)
    return can

def frame(t):
    init()
    if t < SC["03"][0]: can = scene_01_02(t)
    elif t < SC["04"][0]: can = scene_03(t)
    elif t < SC["06"][0]: can = scene_3d(t)
    elif t < SC["07"][0]: can = scene_06(t)
    elif t < SC["08"][0]: can = scene_07(t)
    elif t < SC["09"][0]: can = scene_08(t)
    elif t < SC["10"][0]: can = scene_09(t)
    else: can = scene_10_11(t)
    headline(can, t); subtitle(can, t)
    return post(can, t)

def plan_fx():
    """Temblores, destellos y SFX sincronizados (mismo orden que las escenas)."""
    SHAKES.extend([(1.20, 16), (wt("10", "failed"), 14), (wt("08", "against") + 0.45, 12), (wt("06", "break"), 8), (wt("10", "surrendered"), 8)])
    FLASHES.extend([(1.20, 0.18, 0.55), (wt("03", "Alesia"), 0.22, 0.7)])
    ev(0.0, "click", 0.18); ev(1.18, "boom", 0.36); ev(0.05, "pop")
    for j in range(3): ev(wt("01", "army") + j * 0.09, "pop")
    ev(wt("01", "second"), "click", 0.15)
    for j in range(3): ev(wt("02", "keeping") + j * 0.12, "pop")
    ev(wt("03", "In") + 0.05, "click", 0.18); ev(wt("03", "Caesar"), "mg", 0.06)
    ev(wt("03", "Vercingetorix"), "pop"); ev(wt("03", "Gallic"), "pop"); ev(wt("03", "Alesia"), "boom", 0.22)
    ev(SC["04"][0] + 0.1, "creak", 0.06); ev(wt("04", "cut"), "pop"); ev(wt("04", "supplies"), "click", 0.2)
    ev(wt("06", "break"), "boom", 0.2)
    ev(wt("07", "outer"), "creak", 0.07); ev(wt("07", "long"), "boom", 0.22)
    for j in range(8): ev(wt("07", "facing") + j * 0.05, "pop", 0.05)
    ev(wt("08", "against") + 0.45, "boom", 0.28); ev(wt("08", "both"), "click", 0.15); ev(wt("08", "sides"), "click", 0.15)
    ev(wt("09", "towers"), "pop")
    ev(wt("10", "failed"), "boom", 0.3); ev(wt("10", "Vercingetorix"), "pop"); ev(wt("10", "surrendered"), "boom", 0.2)
    ev(wt("11", "trapped"), "click", 0.18); ev(wt("11", "protected"), "click", 0.18); ev(wt("11", "genius"), "pop")
plan_fx()

def seg(args):
    i, f0, f1, out = args
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - f0) % 60 == 0: print(f"seg{i}: {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    a = sys.argv
    if "--prep" in a: prep(); sys.exit()
    if "--frame" in a:
        for v in a[a.index("--frame") + 1:]:
            frame(float(v)).save(os.path.join(PREP, f"test_{float(v):05.2f}.jpg"), quality=88)
        sys.exit()
    json.dump({"music": True, "bpm": 96, "music_vol": 0.09, "whoosh_cuts": True, "events": SFX}, open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "short_sfx.py"), HERE], check=True)
    F1 = int(TOTAL * FPS); nw = 7; step = math.ceil(F1 / nw)
    tmp = tempfile.mkdtemp(prefix="s03_")
    jobs = [(i, i * step, min(F1, (i + 1) * step), os.path.join(tmp, f"s{i:02d}.mp4")) for i in range(nw)]
    with Pool(nw) as pool: parts = pool.map(seg, jobs)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "video.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    out = os.path.join(ROOT, "Render", "Shorts", os.environ.get("S03_OUT", "S03_Alesia") + ".mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", vid, "-i", os.path.join(HERE, "voz.wav"), "-i", os.path.join(HERE, "sfx.wav"),
                    "-filter_complex", "[1:a]apad[v];[v][2:a]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-t", str(TOTAL), out], check=True)
    up = os.path.join(ROOT, "Render", "Shorts", os.environ.get("S03_OUT", "S03_Alesia").replace("Alesia", "upload") + ".mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", out, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", up], check=True)
    print("listo", out, os.path.getsize(up) // 1024, "KB upload")

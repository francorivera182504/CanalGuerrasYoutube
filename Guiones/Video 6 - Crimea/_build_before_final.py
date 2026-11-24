"""Video 6 — Why Russia Wants Crimea (1920x1080): mapa neón + Stick 2D + puente 3D de Blender.
python build.py --prep          -> recortes de capas (stickers) en _prep/
python build.py --frame 1.2 ... -> cuadros de prueba (_prep/test_XXX.jpg)
python build.py [--from S --to S] -> sfx.wav + Render/Video6_Crimea.mp4
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mapa as M
from mapa import View, Neon, W, H, RED, BLUE, GREEN, GOLD, GREY
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CAP = os.path.join(ROOT, "Imagenes", "Video6", "capas"); PREP = os.path.join(HERE, "_prep"); R3 = os.path.join(HERE, "render3d")
FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\ariblk.ttf"
FPS = 30
YEL, WHITE, ORANGE, CYAN, LBLUE = (255, 214, 40), (255, 255, 255), (255, 140, 40), (60, 200, 255), (190, 225, 255)

TL = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
SC = {s["id"]: (s["start"], s["start"] + s["dur"]) for s in TL["timeline"]}
G = {s["id"]: s for s in json.load(open(os.path.join(HERE, "guion.json"), encoding="utf-8"))["scenes"]}
WORDS = TL["words"]; TOTAL = TL["total"] + 1.2
def clean(w): return w.lower().strip(".,?'’:;!\"")
def wt(scene, word, n=0):
    ws = [w for w in WORDS if w["scene"] == scene and (clean(w["w"]) == word.lower() or word.lower() in clean(w["w"]).split("-") or clean(w["w"]).startswith(word.lower()))]
    return ws[n]["s"]

# ---------------- utilidades ----------------
def ease(x, kind="cubic"):
    x = min(1.0, max(0.0, x))
    if kind == "back": c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == "sine": return -(math.cos(math.pi * x) - 1) / 2
    if kind == "inout": return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind="inout"): return ease((t - t0) / max(1e-6, t1 - t0), kind)
def lerpv(v0, v1, k): return View(lerp(v0.lon, v1.lon, k), lerp(v0.lat, v1.lat, k), math.exp(lerp(math.log(v0.wdeg), math.log(v1.wdeg), k)))

def cutout(path, thr=242):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).copy()
    white = (a[..., :3] >= thr).all(-1); lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    a[..., 3] = np.asarray(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)))
    out = Image.fromarray(a); out = out.crop(out.getbbox())
    # borde blanco tipo sticker para que resalte sobre el mapa oscuro
    pad = 14; big = Image.new("RGBA", (out.width + 2 * pad, out.height + 2 * pad)); big.paste(out, (pad, pad))
    al = big.getchannel("A"); ring = al.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(1.2))
    st = Image.new("RGBA", big.size, (255, 255, 255, 0)); st.putalpha(ring)
    return Image.alpha_composite(st, big)

def prep():
    os.makedirs(PREP, exist_ok=True)
    for f in sorted(os.listdir(CAP)):
        if f.startswith("el_") and f.endswith(".png"):
            cutout(os.path.join(CAP, f)).save(os.path.join(PREP, "cut_" + f)); print("cut", f)

# ---------------- datos por worker ----------------
D = {}
def init():
    if D: return
    M.load(); D["icons"] = {}; D["texts"] = {}; D["subs"] = build_subs(); D["masks"] = {}
    D["ussr"] = [r for n in ("Russia", "Ukraine", "Belarus", "Moldova", "Lithuania", "Latvia", "Estonia", "Georgia", "Armenia", "Azerbaijan",
                             "Kazakhstan", "Uzbekistan", "Turkmenistan", "Kyrgyzstan", "Tajikistan") for r in M.country(n)]

def icon(name, size, flip=False):
    key = (name, int(size), flip)
    if key not in D["icons"]:
        p = os.path.join(PREP, "cut_" + name + ".png")
        im = Image.open(p) if os.path.exists(p) else placeholder(name)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = size / max(im.size); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        sh = im.getchannel("A").point(lambda v: int(v * 0.6)).filter(ImageFilter.GaussianBlur(max(2, size / 25)))
        if len(D["icons"]) > 200: D["icons"].clear()
        D["icons"][key] = (im, sh)
    return D["icons"][key]

def placeholder(name):
    im = Image.new("RGBA", (300, 300)); d = ImageDraw.Draw(im); d.ellipse((10, 10, 290, 290), fill=(255, 255, 255, 230))
    d.text((40, 130), name[3:15], fill=(0, 0, 0), font=ImageFont.truetype(FONT, 28)); return im

def put_icon(can, name, size, xy, t, t0, t1=None, flip=False, bob=True, rot=0):
    if t < t0 or (t1 is not None and t >= t1 + 0.2): return
    k = ease((t - t0) / 0.3, "back")
    if t1 is not None and t > t1: k *= 1 - ease((t - t1) / 0.2)
    if k <= 0.03: return
    sz = size * k if abs(k - 1) > 1e-3 else size
    im, sh = icon(name, round(sz / 4) * 4 if abs(k - 1) > 1e-3 else size, flip)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BILINEAR); sh = sh.rotate(rot, expand=True)
    x, y = xy
    if bob: y += 4 * math.sin(2 * math.pi * 0.7 * (t - t0))
    x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    can.paste((0, 0, 0), (x0 + int(size / 22), y0 + int(size / 14)), sh)
    can.paste(im, (x0, y0), im)

def text_img(s, size, fill, stroke=8):
    key = (s, size, fill, stroke)
    if key not in D["texts"]:
        f = ImageFont.truetype(FONT, size); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
        ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        D["texts"][key] = im
    return D["texts"][key]

def put_text(can, s, size, fill, cx, cy, t, t0, stroke=8, pop=True, t1=None):
    if t < t0 or (t1 is not None and t > t1): return
    im = text_img(s, size, fill, stroke)
    if pop and t - t0 < 0.22:
        k = max(0.05, ease((t - t0) / 0.22, "back")); im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
    can.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def label(can, s, xy, t, t0, col=LBLUE, size=40, t1=None): put_text(can, s, size, col, xy[0], xy[1], t, t0, stroke=7, t1=t1)

# ---------------- titulares y subtítulos ----------------
def headline(can, t):
    sid = None
    for k in sorted(SC):
        if t >= SC[k][0]: sid = k
    if not sid: return
    s = G[sid]["headline"]; t0 = SC[sid][0]; size = 96
    while ImageFont.truetype(FONT, size).getlength(s) > 1500: size -= 6
    put_text(can, s, size, YEL, W / 2, 92, t, t0, stroke=11, pop=t0 > 0)

REPL = {"seventeenth": "17TH", "nineteen": "19", "seventeen": "17", "eighty-three": "83", "forty-four": "44", "fifty-four": "54",
        "ninety-one": "91", "twenty": "20", "eighteen": "18", "twenty-two": "22", "twenty-three": "23", "twenty-five": "25",
        "twenty-six": "26", "fourteen": "14"}
YEARS = {("seventeen", "eighty-three"): "1783", ("nineteen", "forty-four"): "1944", ("nineteen", "fifty-four"): "1954",
         ("nineteen", "ninety-one"): "1991", ("twenty", "fourteen"): "2014", ("twenty", "eighteen"): "2018", ("twenty", "nineteen"): "2019",
         ("twenty", "twenty-two"): "2022", ("twenty", "twenty-three"): "2023", ("twenty", "twenty-five"): "2025", ("twenty", "twenty-six"): "2026",
         ("nineteen", "ninety-seven"): "1997", ("twenty", "ten"): "2010", ("twenty", "forty-two"): "2042", ("twenty", "fifteen"): "2015"}
MULTI = {("one", "hundred", "ninety", "thousand"): "190,000", ("one", "hundred"): "100", ("nineteen-eighties",): "1980S",
         ("three", "billion"): "$3 BILLION"}
def merged_words():
    out = []; i = 0
    while i < len(WORDS):
        w = WORDS[i]; c = clean(w["w"])
        if i + 1 < len(WORDS) and (c, clean(WORDS[i + 1]["w"])) in YEARS and WORDS[i + 1]["scene"] == w["scene"]:
            n = WORDS[i + 1]; tail = n["w"][len(n["w"].rstrip(".,?")):]
            out.append(dict(w, w=YEARS[(c, clean(n["w"]))] + tail, e=n["e"])); i += 2; continue
        if c == "nineteen" and i + 1 < len(WORDS) and clean(WORDS[i + 1]["w"]) == "kilometres": out.append(dict(w, w="19")); i += 1; continue
        hit = None
        for k, rep in MULTI.items():
            seq = [clean(x["w"]) for x in WORDS[i:i + len(k)]]
            if tuple(seq) == k and all(x["scene"] == w["scene"] for x in WORDS[i:i + len(k)]): hit = (k, rep); break
        if hit:
            k, rep = hit; last = WORDS[i + len(k) - 1]; tail = last["w"][len(last["w"].rstrip(".,?")):]
            out.append(dict(w, w=rep + tail, e=last["e"])); i += len(k); continue
        out.append(w); i += 1
    return out

def build_subs():
    groups = []; cur = []
    for w in merged_words():
        txt = w["w"].replace("’", "'").upper()
        if cur and (cur[-1]["scene"] != w["scene"] or len(cur) >= 4 or len(" ".join(c["txt"] for c in cur)) + len(txt) > 24
                    or cur[-1]["w"].endswith((".", "?", ":"))):
            groups.append(cur); cur = []
        cur.append(dict(w, txt=txt))
    groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        end = groups[i + 1][0]["s"] if i + 1 < len(groups) else TOTAL
        out.append((g[0]["s"], max(min(end, SC[g[0]["scene"]][1]), g[-1]["e"] + 0.2), g))
    return out

def subtitle(can, t):
    for s0, s1, g in D["subs"]:
        if s0 <= t < s1: break
    else: return
    hi = max(i for i, w in enumerate(g) if w["s"] <= t + 0.02)
    key = ("sub", tuple(w["txt"] for w in g), hi)
    if key not in D["texts"]:
        f = ImageFont.truetype(FONT, 62); sp = f.getlength(" ")
        ws = [f.getlength(w["txt"]) for w in g]; tw = int(sum(ws) + sp * (len(g) - 1)) + 30
        im = Image.new("RGBA", (tw, 110)); d = ImageDraw.Draw(im); x = 15
        for i, w in enumerate(g):
            d.text((x, 14), w["txt"], font=f, fill=YEL if i == hi else WHITE, stroke_width=9, stroke_fill=(0, 0, 0)); x += ws[i] + sp
        D["texts"][key] = im
    im = D["texts"][key]
    can.paste(im, (int(W / 2 - im.width / 2), int(H - 125 - im.height / 2)), im)

# ---------------- geografía ----------------
SEV, SIMF, KERCH, PEREK, CHON = (33.52, 44.60), (34.10, 44.95), (36.47, 45.36), (33.70, 46.13), (34.42, 46.05)
KHERSON, MELIT, MARIU, ROSTOV, NKAKH, DZHAN, ARMI = (32.62, 46.64), (35.37, 46.85), (37.55, 47.10), (39.72, 47.23), (33.36, 46.76), (34.40, 45.71), (33.69, 46.11)
BRIDGE = [(36.475, 45.330), (36.53, 45.310), (36.585, 45.285), (36.65, 45.255), (36.72, 45.228)]; ARCH_LL = (36.515, 45.316)
CANAL = [(33.37, 46.76), (33.48, 46.52), (33.62, 46.28), (33.72, 46.12), (33.98, 45.94), (34.35, 45.74), (34.9, 45.55), (35.5, 45.43), (36.1, 45.36)]
CORRIDOR = [(39.72, 47.23), (38.9, 47.2), (37.55, 47.10), (36.8, 46.85), (35.37, 46.85), (34.95, 46.4), (34.50, 46.08), (34.40, 45.71), (34.10, 44.95)]
FRONT = [(31.9, 46.45), (32.7, 46.56), (33.4, 46.80), (34.3, 47.25), (35.2, 47.45), (35.9, 47.55), (36.6, 47.72), (37.3, 47.95), (37.8, 48.3), (38.0, 48.8), (37.9, 49.5), (37.6, 50.1)]
VARNA, KALAMITA, CENTRAL_ASIA = (27.9, 43.2), (33.6, 44.95), (64.0, 41.3)

def V_CRIMEA(): return View(34.4, 45.45, 6.2)
def V_KERCH(): return View(36.56, 45.31, 1.6)
def V_REGION(): return View(35.4, 46.4, 11.5)

def geomask(v, key, rings):
    k = (key, round(v.lon, 3), round(v.lat, 3), round(v.wdeg, 3))
    if k not in D["masks"]:
        if len(D["masks"]) > 40: D["masks"].clear()
        D["masks"][k] = M.mask(v, rings)
    return D["masks"][k]

def hatch_mask():
    if "hatch" not in D:
        hm = Image.new("L", (W, H)); hd = ImageDraw.Draw(hm)
        for x in range(-H, W, 34): hd.line([(x, H), (x + H, 0)], fill=255, width=12)
        D["hatch"] = hm
    return D["hatch"]

def base_map(v, crimea=BLUE, ua=BLUE, ru=RED, a_cr=0.32, a_ua=0.18, a_ru=0.14, edges=True, ussr=False, extra=(), occ=False):
    cr = geomask(v, "cr", M.G["crimea"]); fills = []
    if ussr:
        um = geomask(v, "ussr", D["ussr"]); fills.append((um, RED, 0.2))
    else:
        if ua: fills.append((geomask(v, "ua", M.country("Ukraine")), ua, a_ua))
        if ru: fills.append((geomask(v, "ru", M.country("Russia")), ru, a_ru))
    if crimea: fills.append((cr, crimea, a_cr))
    fills += list(extra)
    can, n = M.render(v, fills)
    if occ: can = Image.composite(Image.new("RGB", (W, H), RED), can, ImageChops.multiply(cr, hatch_mask()).point(lambda x: int(x * 0.45)))
    if edges:
        if crimea: n.edge(cr, RED if occ else crimea, 1.0)
        if not ussr:
            if ua: n.edge(geomask(v, "ua", M.country("Ukraine")), ua, 0.45)
            if ru: n.edge(geomask(v, "ru", M.country("Russia")), ru, 0.4)
        else: n.edge(geomask(v, "ussr", D["ussr"]), RED, 0.7)
    return can, n, cr

def path_px(v, ll, n=40):
    pts = [v.P(*p) for p in ll]; out = []
    for a, b in zip(pts, pts[1:]):
        for i in range(n // len(pts) + 2): u = i / (n // len(pts) + 2); out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
    return out + [pts[-1]]

def partial(pts, frac):
    if frac >= 0.999: return pts
    n = max(2, int(frac * len(pts))); return pts[:n]

def arrow(neon, pts, frac, col, w=10):
    if frac <= 0: return
    p = partial(pts, frac)
    if len(p) < 2: return
    neon.line(p, col, w)
    (ax, ay), (bx, by) = p[-2], p[-1]; ang = math.atan2(by - ay, bx - ax); Lh = w * 3.0
    neon.line([(bx + math.cos(ang + 2.5) * Lh, by + math.sin(ang + 2.5) * Lh), (bx, by), (bx + math.cos(ang - 2.5) * Lh, by + math.sin(ang - 2.5) * Lh)], col, w)

def curve(p0, p1, bend=0.2, n=40):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; dx, dy = p1[0] - p0[0], p1[1] - p0[1]; c = (mx - dy * bend, my + dx * bend)
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]) for u in [i / n for i in range(n + 1)]]

def dashes(neon, pts, col, w, t, speed=60, dash=26, gap=18, k=1.0):
    acc = 0.0; off = (t * speed) % (dash + gap); seg = []
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); s = 0.0
        while s < L:
            e = min(L, s + 4); pos = (acc + s - off) % (dash + gap)
            if pos < dash: seg.append((lerp(a[0], b[0], s / L), lerp(a[1], b[1], s / L)))
            elif len(seg) > 1: neon.line(seg, col, w, k=k); seg = []
            else: seg = []
            s = e
        acc += L
    if len(seg) > 1: neon.line(seg, col, w, k=k)

def at_path(pts, u):
    u = min(0.999, max(0.0, u)); f = u * (len(pts) - 1); i = int(f); a, b = pts[i], pts[i + 1]
    return (lerp(a[0], b[0], f - i), lerp(a[1], b[1], f - i))

def bridge(n, v, col=GOLD, broken=0.0, t=0.0, k=1.0):
    pts = path_px(v, BRIDGE, 30)
    if broken <= 0: n.line(pts, col, 9, k=k); return pts
    ax, ay = v.P(*ARCH_LL); gap = 26 * broken * max(1.0, 1.6 / v.wdeg)
    left = [p for p in pts if p[0] < ax - gap]; right = [p for p in pts if p[0] > ax + gap]
    n.line(left, col, 9, k=k); n.line(right, col, 9, k=k)
    return pts

def ring_wave(n, xy, t, t0, col=CYAN, r0=20, r1=220, period=1.4):
    for j in range(3):
        u = ((t - t0) / period + j / 3) % 1.0
        if t < t0: return
        r = lerp(r0, r1, u); pts = [(xy[0] + math.cos(a / 30 * 2 * math.pi) * r, xy[1] + math.sin(a / 30 * 2 * math.pi) * r * 0.75) for a in range(31)]
        n.line(pts, col, 4, k=1 - u)

def crimea_outline(v):
    return [v.P(*p) for p in max(M.G["crimea"], key=len)]

def date_chip(can, s, t, t0):
    put_text(can, s, 44, WHITE, 180, 190, t, t0, stroke=7)

# ---------------- 3D ----------------
def frame3d(shot, i):
    d = os.path.join(R3, shot)
    p = os.path.join(d, f"f_{max(1, i):04d}.png")
    if not os.path.exists(p):
        fs = sorted(f for f in os.listdir(d) if f.startswith(("f_", "still_"))) if os.path.isdir(d) else []
        if not fs: return Image.new("RGB", (W, H), (20, 25, 35))
        p = os.path.join(d, fs[min(len(fs) - 1, max(0, i - 1))])
    im = Image.open(p).convert("RGB")
    if im.size != (W, H): im = im.resize((W, H), Image.BILINEAR)
    small = im.resize((W // 2, H // 2), Image.BILINEAR)
    hi = small.point(lambda v: max(0, v - 170) * 3)
    g = ImageChops.add(hi.filter(ImageFilter.GaussianBlur(10)), hi.filter(ImageFilter.GaussianBlur(3))).resize((W, H), Image.BILINEAR)
    im = ImageChops.add(im, g)
    return ImageChops.multiply(im, M.G["vig"].point(lambda v: min(255, v + 50)))

def small_tag(can, s, t, t0=0):
    put_text(can, s, 26, (220, 220, 220), 230, H - 40, t, t0, stroke=5, pop=False)

# ---------------- escenas ----------------
def s01(t):
    a, b = SC["01"]; f = int((t - a) * FPS) + 1; can = frame3d("hook", f)
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def s02(t):
    a, b = SC["02"]; k = ramp(t, a, a + 1.4, "inout")
    v = lerpv(V_KERCH(), V_REGION(), k)
    can, n, cr = base_map(v, occ=True)
    bridge(n, v, RED, broken=1.0)
    ta = wt("02", "another")
    if t >= ta: arrow(n, path_px(v, CORRIDOR[:-1], 60), ramp(t, ta, ta + 0.9, "cubic"), GOLD, 9)
    can = n.draw(can)
    bx, by = v.P(*ARCH_LL); put_icon(can, "el_explosion", 120, (bx, by), t, a, a + 1.2, bob=False)
    if t >= ta: label(can, "LAND ROUTE", v.P(36.8, 47.25), t, ta + 0.5, GOLD, 38)
    tm = wt("02", "matter")
    put_text(can, "?", 160, YEL, bx + 40, by - 120, t, tm, stroke=10)
    return can

def s03(t):
    a, b = SC["03"]; v = lerpv(View(36.56, 45.33, 2.6), View(36.56, 45.31, 2.0), ramp(t, a, b, "sine"))
    can, n, cr = base_map(v, ru=RED, occ=True)
    tc = wt("03", "collapsed"); br = ramp(t, tc, tc + 0.3, "cubic")
    bridge(n, v, GOLD, broken=br)
    rail = path_px(v, [(p[0], p[1] - 0.012) for p in BRIDGE], 30); n.line(rail, CYAN, 6, k=0.9)
    bx, by = v.P(*ARCH_LL)
    if tc <= t < tc + 2.5: ring_wave(n, (bx, by + 10), t, tc, CYAN, 15, 200, 1.0)
    can = n.draw(can)
    label(can, "KERCH STRAIT", v.P(36.62, 45.12), t, a + 0.3, LBLUE, 40)
    label(can, "CRIMEA", v.P(36.2, 45.38), t, a + 0.2, WHITE, 46); label(can, "RUSSIA", v.P(36.95, 45.27), t, a + 0.2, (255, 170, 160), 46)
    tr = wt("03", "rail"); tres = wt("03", "resumed")
    if t >= tr:
        u = 0.15 + 0.25 * ramp(t, tr, tr + 1.0) + 0.5 * ramp(t, tres, tres + 1.5)
        put_icon(can, "el_fuel_train", 170, at_path(rail, u), t, tr, bob=False)
        if t < tres: put_text(can, "II", 70, (255, 80, 60), at_path(rail, u)[0], at_path(rail, u)[1] - 90, t, wt("03", "interrupted"), stroke=8)
    return can

def char_scene(t, a, b, sid):
    """General ruso sostiene Crimea en la palma; hilos de suministro desde la izquierda."""
    v = View(36.0, 46.2, 13); can, n, cr = base_map(v, a_cr=0.15, a_ua=0.08, a_ru=0.08, edges=False)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.55).filter(ImageFilter.GaussianBlur(3))
    n = Neon()
    gx, gy = W * 0.66, H * 0.60
    put_icon(can, "el_general", 640, (gx, gy), t, a + 0.1, bob=False)
    # silueta de Crimea flotando sobre la palma (a la derecha del general)
    px, py = gx - 235, gy - 200 + 8 * math.sin(t * 2.2)
    if t >= a + 0.4:
        cv = View(34.4, 45.4, 4.6); ol = crimea_outline(cv); s = 0.16
        poly = [(px + (x - W / 2) * s, py + (y - H / 2) * s) for x, y in ol]
        m = Image.new("L", (W, H)); ImageDraw.Draw(m).polygon(poly, fill=255)
        can = Image.composite(Image.new("RGB", (W, H), (40, 90, 170)), can, m.point(lambda v_: int(v_ * 0.7)))
        n.line(poly, BLUE, 5, True, 1.0)
    # hilos de suministro
    snap = 1e9
    if sid == "29":
        try: snap = wt("29", "depends")
        except Exception: snap = b - 2
    if sid == "04": tl = wt("04", "vulnerable")
    else: tl = a + 0.6
    for j, (y0, col) in enumerate(((H * 0.35, GOLD), (H * 0.55, CYAN), (H * 0.72, GOLD))):
        if t < tl - 0.6: break
        fr = ramp(t, tl - 0.6 + j * 0.12, tl + j * 0.12, "cubic")
        wob = 6 * math.sin(t * 7 + j)
        pts = curve((-20, y0), (px - 50, py + 30 + j * 12), 0.08 + wob / 200, 30)
        if j == 1 and t >= snap:
            cut = int(len(pts) * 0.55); kk = 1 - ramp(t, snap, snap + 0.5)
            n.line(pts[:cut - 3], col, 5, k=1.0); n.line(pts[cut + 3:], col, 5, k=kk)
        else: n.line(partial(pts, fr), col, 5, k=0.9)
    can = n.draw(can)
    if sid == "04":
        put_icon(can, "el_anchor", 130, (px + 10, py - 140), t, wt("04", "military"))
        put_icon(can, "el_truck", 120, (W * 0.18, H * 0.35 - 50), t, wt("04", "supplied"))
        put_icon(can, "el_fuel_train", 150, (W * 0.18, H * 0.55 - 50), t, wt("04", "supplied") + 0.15)
    else:
        for j, (nm, w0) in enumerate((("el_anchor", "naval"), ("el_little_green", "symbol"), ("el_general", "launch"))):
            if nm == "el_general": nm = "el_warship"
            put_icon(can, nm, 120, (W * 0.18 + j * 160, H * 0.28), t, wt("29", w0))
        if t >= snap: put_icon(can, "el_explosion", 140, (W * 0.30, H * 0.55), t, snap, snap + 0.8, bob=False)
    return can

def s04(t): a, b = SC["04"]; return char_scene(t, a, b, "04")
def s29(t): a, b = SC["29"]; return char_scene(t, a, b, "29")

def s05(t):
    a, b = SC["05"]; v = lerpv(View(34.4, 45.6, 9.0), V_CRIMEA(), ramp(t, a, a + 2.5, "inout"))
    can, n, cr = base_map(v, crimea=None)
    ol = crimea_outline(v); fr = ramp(t, a + 0.2, a + 2.2, "inout")
    n.line(partial(ol + [ol[0]], fr), BLUE, 7, False, 1.1)
    tp = wt("05", "Perekop")
    if t >= tp: n.dot(v.P(*PEREK), YEL, 34 + 10 * math.sin(t * 9)); n.dot(v.P(*CHON), YEL, 24, 0.7)
    can = n.draw(can)
    label(can, "CRIMEA", v.P(34.2, 45.3), t, a + 0.6, WHITE, 60)
    label(can, "BLACK SEA", v.P(32.6, 44.6), t, wt("05", "Black"), LBLUE, 48)
    label(can, "SEA OF AZOV", v.P(35.9, 46.1), t, wt("05", "Azov"), LBLUE, 48)
    label(can, "PEREKOP", (v.P(*PEREK)[0] - 170, v.P(*PEREK)[1] - 10), t, tp, YEL, 40)
    label(can, "UKRAINE", v.P(34.0, 46.7), t, wt("05", "mainland"), (170, 210, 255), 50)
    return can

def s06(t):
    a, b = SC["06"]; v = lerpv(V_CRIMEA(), View(33.75, 44.75, 2.4), ramp(t, a, a + 1.6, "inout"))
    can, n, cr = base_map(v)
    sx, sy = v.P(*SEV); ring_wave(n, (sx - 40, sy + 40), t, wt("06", "base") if t > a + 1 else 1e9, CYAN, 30, 520, 2.0)
    n.dot((sx, sy), CYAN, 30 + 6 * math.sin(t * 7))
    can = n.draw(can)
    label(can, "SEVASTOPOL", (sx + 40, sy - 80), t, wt("06", "Sevastopol"), WHITE, 50)
    put_icon(can, "el_anchor", 150, (sx + 140, sy + 40), t, wt("06", "harbour"))
    xs = lerp(-200, sx - 260, ramp(t, wt("06", "navy"), wt("06", "navy") + 1.4, "cubic"))
    put_icon(can, "el_warship", 230, (xs, sy + 160 + 6 * math.sin(t * 2)), t, wt("06", "navy") - 0.1)
    return can

def s07_08(t):
    a7, b7 = SC["07"]; a8, b8 = SC["08"]; v = V_CRIMEA() if t < a8 else lerpv(V_CRIMEA(), View(33.9, 45.0, 4.0), ramp(t, a8 + 3.5, b8, "inout"))
    t83 = wt("08", "seventeen") if t >= a8 else 1e9
    red = ramp(t, t83, t83 + 0.6, "cubic")
    can, n, cr = base_map(v, crimea=None, ua=None, ru=None)
    col = tuple(int(lerp(g, r, red)) for g, r in zip(GREEN, RED))
    ext = []
    m = geomask(v, "cr", M.G["crimea"]); can = Image.composite(Image.new("RGB", (W, H), col), can, m.point(lambda x: int(x * 0.32)))
    n.edge(m, col, 1.0)
    if t >= a8:
        sx, sy = v.P(*SEV); tb = wt("08", "built")
        if t >= tb: n.dot((sx, sy), CYAN, 26)
    can = n.draw(can)
    put_icon(can, "el_tatar", 300, (W * 0.80, H * 0.55), t, wt("07", "Tatars"), t83)
    label(can, "CRIMEAN KHANATE", v.P(34.3, 45.35), t, wt("07", "Khanate"), (170, 255, 200), 56, t1=t83)
    if t >= a8:
        label(can, "RUSSIAN EMPIRE", (W * 0.5, H * 0.22), t, t83 + 0.2, (255, 170, 160), 56)
        put_icon(can, "el_empress", 330, (W * 0.80, H * 0.55), t, wt("08", "Catherine"))
        tb = wt("08", "built"); sx, sy = v.P(*SEV)
        xs = lerp(-150, sx - 120, ramp(t, tb, tb + 2.0, "cubic"))
        put_icon(can, "el_sailship", 200, (xs, sy + 120 + 5 * math.sin(t * 2)), t, tb - 0.2)
        put_icon(can, "el_anchor", 110, (sx + 20, sy - 70), t, wt("08", "naval"))
    return can

def s09(t):
    a, b = SC["09"]; v = lerpv(View(32.0, 43.6, 15.0), View(33.6, 44.8, 4.2), ramp(t, wt("09", "besieged") - 0.3, wt("09", "besieged") + 0.9, "inout"))
    can, n, cr = base_map(v, crimea=RED, ua=None, ru=None, a_cr=0.25)
    sx, sy = v.P(*SEV)
    tl = wt("09", "landed")
    names = (("el_redcoat", "Britain"), ("el_french1854", "France"), ("el_ottoman1854", "Ottoman"))
    tbes = wt("09", "besieged")
    if t < tbes:
        for j in range(3):
            p0 = v.P(VARNA[0] + 0.5 * j, VARNA[1] + 0.3 - 0.6 * j); arrow(n, curve(p0, v.P(33.5, 45.0), 0.15 - 0.1 * j), ramp(t, tl - 0.2 + j * 0.15, tl + 1.0 + j * 0.15, "cubic"), (255, 230, 120), 8)
    else:
        fr = ramp(t, tbes, tbes + 0.8, "cubic"); r = 150
        ring = [(sx + math.cos(math.radians(200 + i * 1.6)) * r * 1.2, sy + math.sin(math.radians(200 + i * 1.6)) * r) for i in range(int(110 * fr) + 1)]
        if len(ring) > 1: n.line(ring, (255, 230, 120), 9)
        n.dot((sx, sy), RED, 30 + 8 * math.sin(t * 8))
    can = n.draw(can)
    for j, (nm, w0) in enumerate(names):
        tj = wt("09", w0)
        if t < tbes: put_icon(can, nm, 200, (W * 0.16 + j * 190, H * 0.62), t, tj, tbes - 0.2)
        else: put_icon(can, nm, 170, (sx - 260 + j * 30, sy - 140 + j * 120), t, tbes + 0.2 + j * 0.1)
    if t >= tbes:
        put_icon(can, "el_cannon1854", 150, (sx - 330, sy + 60), t, tbes + 0.5)
        for j in range(4):
            tp = tbes + 0.8 + j * 0.9
            put_icon(can, "el_smoke", 110, (sx - 200 + 40 * j, sy - 30 + 25 * (j % 2)), t, tp, tp + 0.7, bob=False)
        put_icon(can, "el_russian1854", 180, (sx + 60, sy + 20), t, tbes + 0.3)
        tlost = wt("09", "lost")
        if t >= tlost: put_text(can, "X", 170, (255, 60, 50), sx + 60, sy + 20, t, tlost, stroke=10)
        label(can, "SIEGE OF SEVASTOPOL", (W / 2, H * 0.22), t, tbes + 0.2, WHITE, 52)
    else:
        label(can, "CRIMEAN WAR 1853–56", (W / 2, H * 0.22), t, a + 0.3, WHITE, 52)
    return can

def s10(t):
    a, b = SC["10"]; v = lerpv(View(36.0, 45.5, 14), View(48.0, 45.0, 44), ramp(t, a + 0.3, wt("10", "deportation") + 0.6, "inout"))
    can, n, cr = base_map(v, crimea=GREEN, ua=None, ru=None, a_cr=0.3)
    td = wt("10", "deportation")
    if t >= td:
        p0 = v.P(34.4, 45.4)
        for j, dst in enumerate(((64.0, 41.3), (68.0, 40.5), (58.0, 52.0))):
            arrow(n, curve(p0, v.P(*dst), -0.12 - 0.05 * j, 50), ramp(t, td + j * 0.25, td + 1.8 + j * 0.25, "cubic"), GREY, 9 if j < 2 else 6)
    can = n.draw(can)
    if t >= td:
        pts = curve(v.P(34.4, 45.4), v.P(64.0, 41.3), -0.12, 50)
        put_icon(can, "el_freight_wagon", 130, at_path(pts, ramp(t, td, td + 3.0, "inout")), t, td, bob=False)
    put_icon(can, "el_family", 260, (W * 0.20, H * 0.66), t, wt("10", "Tatar"))
    label(can, "CENTRAL ASIA", v.P(64.0, 43.0), t, wt("10", "Central"), (220, 220, 220), 46)
    return can

def s11_12(t):
    a11, b11 = SC["11"]; a12, b12 = SC["12"]
    v = lerpv(View(40.0, 51.0, 44), View(34.5, 47.5, 20), ramp(t, a11 + 4.0, a11 + 6.0, "inout"))
    if t >= a12: v = lerpv(View(34.5, 47.5, 20), View(33.5, 48.3, 17), ramp(t, a12, b12, "sine"))
    tcol = wt("12", "collapsed") if t >= a12 else 1e9
    split = ramp(t, tcol, tcol + 0.5, "cubic")
    ru_m = geomask(v, "ru", M.country("Russia")); ua_m = geomask(v, "ua", M.country("Ukraine")); us = geomask(v, "ussr", D["ussr"])
    ttr = wt("11", "transferred")
    cr_col = BLUE if t >= ttr + 0.3 else (210, 70, 60)
    fills = [(us, (200, 50, 45), 0.22 * (1 - split)), (ru_m, RED, 0.10 + 0.08 * split), (ua_m, (80, 120, 220), 0.16 + 0.06 * split)]
    can, n = M.render(v, fills)
    cr = geomask(v, "cr", M.G["crimea"])
    can = Image.composite(Image.new("RGB", (W, H), cr_col), can, cr.point(lambda x: int(x * 0.4)))
    n.edge(us, RED, 0.8 * (1 - split))
    # línea interna Rusia–Ucrania: punteada (1954) → frontera neón (1991)
    edge_ua = M.edge_of(ua_m, 5)
    if split < 1:
        dash = Image.new("L", (W, H)); dd = ImageDraw.Draw(dash)
        for x in range(0, W, 28): dd.rectangle((x, 0, x + 14, H), fill=255)
        can.paste((235, 235, 235), mask=ImageChops.multiply(edge_ua, dash).point(lambda x: int(x * (1 - split))))
    if split > 0: n.edge(ua_m, BLUE, split); n.edge(ru_m, RED, 0.6 * split)
    n.edge(cr, cr_col, 1.0)
    can = n.draw(can)
    label(can, "SOVIET UNION", v.P(48.0, 55.0) if t < a11 + 4 else v.P(38.5, 52.5), t, a11 + 0.3, (255, 170, 160), 56, t1=tcol)
    label(can, "RUSSIAN SSR", v.P(38.8, 50.3), t, wt("11", "Russian"), (255, 170, 160), 40, t1=tcol)
    label(can, "UKRAINIAN SSR", v.P(31.0, 49.3), t, wt("11", "Ukrainian"), (170, 210, 255), 40, t1=tcol)
    put_icon(can, "el_soviet_official", 280, (W * 0.84, H * 0.62), t, wt("11", "Soviet"), tcol)
    if t >= ttr:
        cx, cy = v.P(34.2, 45.3); put_text(can, "→", 90, YEL, cx - 10, cy - 80, t, ttr, stroke=8, t1=ttr + 1.5)
    if t >= a12:
        label(can, "UKRAINE", v.P(31.5, 49.0), t, wt("12", "independent"), (170, 210, 255), 60)
        label(can, "RUSSIA", v.P(38.6, 49.6), t, tcol + 0.4, (255, 170, 160), 60)
        label(can, "BORDER", v.P(37.6, 49.3), t, wt("12", "border"), WHITE, 40)
    return can

def s13(t):
    a, b = SC["13"]; v = View(33.7, 44.75, 2.6); can, n, cr = base_map(v)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.5)
    sx, sy = v.P(*SEV); n.dot((sx, sy), CYAN, 26); can = n.draw(can)
    put_icon(can, "el_two_officials", 520, (W * 0.34, H * 0.60), t, a + 0.1, bob=False)
    put_icon(can, "el_contract", 230, (W * 0.60, H * 0.42), t, wt("13", "lease"), rot=8)
    put_text(can, "LEASE", 60, YEL, W * 0.60, H * 0.42 + 10, t, wt("13", "lease") + 0.2, stroke=8)
    put_icon(can, "el_warship", 260, (W * 0.78, H * 0.66 + 6 * math.sin(t * 2)), t, wt("13", "naval"))
    return can

def s14(t):
    a, b = SC["14"]; v = V_CRIMEA(); tan = wt("14", "annexed"); red = ramp(t, tan, tan + 0.6, "cubic")
    can, n, cr = base_map(v, crimea=BLUE, a_cr=0.3)
    if red > 0:
        hatch = Image.new("L", (W, H)); hd = ImageDraw.Draw(hatch)
        for x in range(-H, W, 34): hd.line([(x, H), (x + H, 0)], fill=255, width=12)
        can = Image.composite(Image.new("RGB", (W, H), RED), can, ImageChops.multiply(cr, hatch).point(lambda x: int(x * 0.55 * red)))
        n.edge(cr, RED, red)
    can = n.draw(can)
    ts = wt("14", "soldiers")
    for j, p in enumerate((SIMF, SEV, KERCH, (33.9, 46.0))):
        put_icon(can, "el_little_green", 150, v.P(*p), t, ts + 0.15 * j)
    label(can, "PARLIAMENT", (v.P(*SIMF)[0], v.P(*SIMF)[1] - 110), t, wt("14", "parliament"), WHITE, 34)
    put_icon(can, "el_ballot", 200, (W * 0.84, H * 0.50), t, wt("14", "referendum"))
    tr = wt("14", "rejected")
    if t >= tr: put_text(can, "X", 200, (255, 60, 50), W * 0.84, H * 0.50, t, tr, stroke=10)
    label(can, "ANNEXED", v.P(34.4, 45.2), t, tan + 0.2, (255, 170, 160), 60)
    return can

def canal_scene(t, v, state):
    """state: dict(flow=0–1 parte inicial, cut=bool, grey=0–1)."""
    can, n, cr = base_map(v, extra=state.get("extra", ()), occ=True)
    pts = path_px(v, CANAL, 80)
    cutk = state.get("cutk", 1.0)
    head = pts[:int(len(pts) * 0.24)]; tail = pts[int(len(pts) * 0.24):]
    dashes(n, head, CYAN, 8, t, 70)
    if state.get("flow", 1.0) > 0: dashes(n, tail, CYAN, 8, t, 70, k=state["flow"])
    if state.get("flow", 1.0) < 1: n.line(tail, (90, 100, 110), 5, k=1 - state["flow"])
    return can, n, pts

def s15(t):
    a, b = SC["15"]; v = lerpv(View(34.2, 45.9, 5.5), View(34.4, 45.75, 4.6), ramp(t, a, b, "sine"))
    tb = wt("15", "blocking"); flow = 1 - ramp(t, tb + 0.2, tb + 0.8)
    can, n, pts = canal_scene(t, v, {"flow": flow})
    can = n.draw(can)
    gx, gy = pts[int(len(pts) * 0.24)]
    put_icon(can, "el_sluice", 150, (gx, gy - 20), t, tb, bob=False)
    label(can, "NORTH CRIMEAN CANAL", (v.P(33.3, 46.45)[0] - 60, v.P(33.3, 46.45)[1]), t, wt("15", "North"), CYAN, 40)
    label(can, "DNIPRO", v.P(33.0, 47.0), t, a + 0.4, LBLUE, 36)
    put_text(can, "~85% OF WATER", 46, WHITE, W * 0.76, H * 0.26, t, wt("15", "most"), stroke=7)
    put_text(can, "MAINLY FARMING", 40, (170, 255, 200), W * 0.76, H * 0.33, t, wt("15", "farming"), stroke=7)
    return can

def s16(t):
    a, b = SC["16"]; v = lerpv(V_CRIMEA(), View(35.4, 45.6, 5.0), ramp(t, a, a + 2, "inout"))
    can, n, cr = base_map(v, crimea=RED, a_cr=0.24)
    tn = wt("16", "direct")
    if t >= tn:
        x0, y0 = v.P(33.4, 46.2); x1, y1 = v.P(35.3, 46.1)
        n.line([(x0, y0), (x1, y1)], RED, 8, k=0.5 + 0.5 * math.sin(t * 6) ** 2)
    can = n.draw(can)
    if t >= tn: put_text(can, "X", 140, (255, 60, 50), *v.P(34.4, 46.15), t, tn, stroke=10)
    tf = wt("16", "ferries"); kx0, ky0 = v.P(36.40, 45.33); kx1, ky1 = v.P(36.75, 45.28)
    for j in range(3):
        if t < tf: break
        u = ((t - tf) / 4.0 + j / 3) % 1.0; d = 1 if j % 2 == 0 else -1; uu = u if d > 0 else 1 - u
        put_icon(can, "el_ferry", 120, (lerp(kx0, kx1, uu), lerp(ky0, ky1, uu) + 40 * (j - 1)), t, tf + 0.1 * j, flip=d < 0, bob=True)
    label(can, "KERCH STRAIT", (kx0 + 60, ky0 + 150), t, tf, LBLUE, 36)
    return can

def fly(t, f0):
    a = SC["17"][0]; f = int((t - a) * FPS) + 1; return frame3d("fly", f)

def s17(t):
    a, b = SC["17"]; can = fly(t, 0)
    put_text(can, "ROAD · 2018", 54, ORANGE, W * 0.72, H * 0.80, t, wt("17", "opened"), stroke=8)
    put_text(can, "RAIL · 2019", 54, CYAN, W * 0.28, H * 0.80, t, wt("17", "railway"), stroke=8)
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def s18(t):
    a, b = SC["18"]; can = fly(t, 0)
    put_text(can, "ROAD", 64, ORANGE, W * 0.70, H * 0.70, t, wt("18", "cars"), stroke=9)
    put_text(can, "RAIL", 64, CYAN, W * 0.40, H * 0.46, t, wt("18", "trains"), stroke=9)
    for j, (nm, w0) in enumerate((("el_jerrycan", "fuel"), ("el_crate", "equipment"), ("el_little_green", "troops"))):
        put_icon(can, nm, 130, (W * 0.14 + j * 170, H * 0.24), t, wt("18", w0))
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def region_scene(t, v, corridor=0.0, canal=None, front=0.0, br=0.0, kak=1.0):
    can, n, cr = base_map(v, occ=True)
    if kak < 1:
        km = geomask(v, "kak", M.G["lakes"]["kakhovka"])
        can = Image.composite(Image.new("RGB", (W, H), (60, 50, 40)), can, km.point(lambda x: int(x * 0.8 * (1 - kak))))
    if canal is not None:
        pts = path_px(v, CANAL, 80); head = pts[:int(len(pts) * 0.24)]; tail = pts[int(len(pts) * 0.24):]
        dashes(n, head, CYAN, 6, t, 60, k=max(0.2, kak)); dashes(n, tail, CYAN, 6, t, 60, k=canal * kak + 0.0)
        if canal * kak < 1: n.line(tail, (90, 100, 110), 4, k=1 - canal * kak)
    if front > 0: n.line(partial(path_px(v, FRONT, 80), front), RED, 6, k=0.8)
    if corridor > 0: arrow(n, path_px(v, CORRIDOR, 80), corridor, GOLD, 8)
    bridge(n, v, GOLD, broken=br)
    return can, n

def s19(t):
    a, b = SC["19"]; v = lerpv(V_REGION(), View(34.6, 46.3, 8.5), ramp(t, a, b, "sine"))
    can, n = region_scene(t, v, canal=0.0)
    tl = wt("19", "launch")
    for j, (p0, p1) in enumerate(((ARMI, KHERSON), (CHON, MELIT), ((35.2, 45.9), (36.2, 46.75)))):
        arrow(n, curve(v.P(*p0), v.P(*p1), 0.12 - 0.1 * j, 30), ramp(t, tl - 0.3 + j * 0.2, tl + 0.8 + j * 0.2, "cubic"), RED, 11)
    can = n.draw(can)
    label(can, "KHERSON", (v.P(*KHERSON)[0] - 40, v.P(*KHERSON)[1] - 50), t, wt("19", "southern"), WHITE, 38)
    label(can, "MELITOPOL", (v.P(*MELIT)[0], v.P(*MELIT)[1] - 50), t, wt("19", "southern") + 0.2, WHITE, 38)
    put_text(can, "FEB 2022", 54, WHITE, W * 0.82, H * 0.24, t, wt("19", "February"), stroke=8)
    return can

def s20(t):
    a, b = SC["20"]; v = lerpv(View(34.6, 46.3, 8.5), View(36.0, 46.4, 9.5), ramp(t, a, a + 1.5, "inout"))
    tc = wt("20", "corridor"); tr = wt("20", "reopened")
    can, n = region_scene(t, v, corridor=ramp(t, tc - 0.4, tc + 1.6, "inout"), canal=ramp(t, tr, tr + 0.8))
    can = n.draw(can)
    label(can, "LAND CORRIDOR", v.P(37.0, 47.45), t, tc + 0.3, GOLD, 44)
    label(can, "SEA OF AZOV", v.P(36.6, 46.2), t, a + 0.3, LBLUE, 36)
    if t >= tc + 1.0:
        pts = path_px(v, CORRIDOR, 80); put_icon(can, "el_truck", 110, at_path(pts, ((t - tc - 1.0) / 5.0) % 1.0), t, tc + 1.0, bob=False)
    return can

def s21(t):
    a, b = SC["21"]; v = lerpv(View(36.0, 46.4, 9.5), View(34.0, 46.6, 5.0), ramp(t, a, a + 1.4, "inout"))
    td = wt("21", "destroyed"); kak = 1 - ramp(t, td, td + 2.0, "inout")
    can, n = region_scene(t, v, corridor=1.0, canal=1.0, kak=kak)
    can = n.draw(can)
    label(can, "KAKHOVKA DAM", (v.P(*NKAKH)[0] - 60, v.P(*NKAKH)[1] + 60), t, wt("21", "Kakhovka"), WHITE, 40)
    put_text(can, "JUN 2023", 54, WHITE, W * 0.82, H * 0.24, t, a + 0.2, stroke=8)
    if t >= td: put_icon(can, "el_explosion", 110, v.P(*NKAKH), t, td, td + 0.9, bob=False)
    return can

def s22(t):
    a, b = SC["22"]; v = lerpv(View(35.6, 45.8, 7.0), View(36.56, 45.31, 2.0), ramp(t, a, a + 2.2, "inout"))
    can, n = region_scene(t, v, corridor=1.0)
    bx, by = v.P(*ARCH_LL); tt = wt("22", "target"); r = lerp(320, 70, ramp(t, tt - 0.6, tt + 0.2, "cubic"))
    if t >= tt - 0.8:
        circ = [(bx + math.cos(i / 40 * 2 * math.pi) * r, by + math.sin(i / 40 * 2 * math.pi) * r) for i in range(41)]
        n.line(circ, RED, 6)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): n.line([(bx + dx * r * 0.6, by + dy * r * 0.6), (bx + dx * r * 1.3, by + dy * r * 1.3)], RED, 6)
    n.dot((bx, by), GOLD, 22 + 8 * math.sin(t * 6))
    can = n.draw(can)
    label(can, "SUPPLY ROUTE", (bx - 260, by - 120), t, wt("22", "supply"), GOLD, 40)
    label(can, "SYMBOL", (bx + 200, by + 120), t, wt("22", "symbol"), (255, 170, 160), 40)
    return can

def s23(t):
    a, b = SC["23"]; f = int((t - a) * FPS) + 1; can = frame3d("oct22", f)
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def kerch_attack(t, sid):
    a, b = SC[sid]; v = lerpv(View(36.50, 45.25, 2.2), View(36.56, 45.29, 1.8), ramp(t, a, b, "sine"))
    can, n = region_scene(t, v)
    bx, by = v.P(*ARCH_LL)
    if sid == "24":
        ts = wt("24", "sea"); td = wt("24", "damaged")
        if td <= t < td + 2.5: ring_wave(n, (bx, by + 10), t, td, CYAN, 15, 180, 1.0)
        for j in range(3):
            p0 = (W * (0.05 + 0.1 * j), H * (0.92 - 0.05 * j)); u = ramp(t, ts - 0.4 + j * 0.1, td, "inout")
            if t < td + 0.1:
                pass
        n.line([], RED, 2)
        can = n.draw(can)
        for j in range(3):
            p0 = (W * (0.05 + 0.1 * j), H * (0.92 - 0.05 * j)); u = ramp(t, ts - 0.4 + j * 0.1, td, "inout")
            if t < td: put_icon(can, "el_seadrone", 110, (lerp(p0[0], bx - 30 + 30 * j, u), lerp(p0[1], by + 30, u)), t, ts - 0.4, bob=True)
        put_icon(can, "el_explosion", 220, (bx, by), t, td, td + 1.0, bob=False)

    else:
        te = wt("25", "explosives"); tr = wt("25", "reopened")
        for j in range(3):
            if te + 0.12 * j <= t < te + 2.5: ring_wave(n, (bx - 80 + 80 * j, by + 20), t, te + 0.12 * j, CYAN, 10, 150, 0.9)
        can = n.draw(can)
        for j in range(3): put_icon(can, "el_explosion", 90, (bx - 80 + 80 * j, by + 30), t, te + 0.12 * j, te + 0.8, bob=False)
        label(can, "UNDERWATER CHARGES (SBU CLAIM)", (W / 2, H * 0.24), t, wt("25", "security"), WHITE, 40)
        if t >= tr: put_text(can, "REOPENED", 70, (90, 255, 140), bx, by - 140, t, tr, stroke=9)
    return can

def s24(t): return kerch_attack(t, "24")
def s25(t): return kerch_attack(t, "25")

def s26(t):
    a, b = SC["26"]; f = int((t - a) * FPS) + 1; can = frame3d("nov26", f)
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def s27_28(t):
    a27, b27 = SC["27"]; a28, b28 = SC["28"]
    v = lerpv(View(36.56, 45.31, 2.0), View(36.0, 46.6, 10.0), ramp(t, a27, a27 + 1.8, "inout"))
    if t >= a28: v = lerpv(View(36.0, 46.6, 10.0), View(35.6, 46.8, 9.0), ramp(t, a28, b28, "sine"))
    front = ramp(t, wt("28", "front"), wt("28", "front") + 1.0) if t >= a28 else 0.0
    can, n = region_scene(t, v, corridor=1.0, br=1.0, front=front)
    rail = path_px(v, [(p[0], p[1] - 0.012) for p in BRIDGE], 20); n.line(rail, CYAN, 5)
    can = n.draw(can)
    pts = path_px(v, CORRIDOR, 80); tt = wt("27", "trucks")
    for j in range(3):
        if t >= tt: put_icon(can, "el_truck", 100, at_path(pts, ((t - tt) / 7.0 + j / 3) % 1.0), t, tt + 0.1 * j, bob=False)
    ttr = wt("27", "trains"); put_icon(can, "el_fuel_train", 120, (v.P(*ARCH_LL)[0] + 40, v.P(*ARCH_LL)[1] - 70), t, ttr, bob=False)
    if t < a28: put_text(can, "NOT COMPLETELY", 56, WHITE, W * 0.24, H * 0.26, t, wt("27", "Not"), stroke=8)
    if t >= a28:
        label(can, "FRONT LINE (APPROX.)", v.P(34.6, 47.75), t, wt("28", "front"), (255, 140, 130), 38)
        ta = wt("28", "attacks")
        for j, u in enumerate((0.25, 0.45, 0.62)):
            put_icon(can, "el_explosion", 90, at_path(pts, u), t, ta + 0.15 * j, ta + 1.2 + 0.15 * j, bob=False)
        ts = wt("28", "Sevastopol"); sx, sy = v.P(*SEV)
        put_icon(can, "el_fuel_pump", 150, (sx + 20, sy - 90), t, ts)
        label(can, "FUEL LIMITS (REPORTED)", (sx + 60, sy - 190), t, wt("28", "restrictions"), WHITE, 34)
    return can

def s30(t):
    a, b = SC["30"]; v = lerpv(View(35.6, 46.8, 9.0), View(35.0, 46.0, 7.5), ramp(t, a, b, "sine"))
    can, n = region_scene(t, v, corridor=1.0, br=1.0, front=1.0)
    can = n.draw(can)
    bx, by = v.P(*ARCH_LL); put_text(can, "?", 200, YEL, bx, by - 150, t, wt("30", "supplied"), stroke=12)
    put_text(can, "COMMENT BELOW", 50, WHITE, W * 0.80, H * 0.30, t, wt("30", "comments"), stroke=8)
    return can

# ================= escenas nuevas (versión larga) =================
BOSPORUS, AEGEAN, SPB, NOVOR, KYIV, ODESA, BERD, MOSKVA_LL = (29.05, 41.1), (25.6, 38.9), (30.3, 59.9), (37.77, 44.72), (30.52, 50.45), (30.73, 46.48), (36.78, 46.75), (30.95, 45.25)

def wq(sid, word, frac=0.3, n=0):
    """wt() tolerante: si la palabra no está (guion cambiado), cae a una fracción de la escena."""
    try: return wt(sid, word, n)
    except Exception: a, b = SC[sid]; return a + frac * (b - a)

def snowflake(n, xy, r, col=LBLUE, k=1.0):
    for j in range(3):
        a = math.pi / 3 * j; dx, dy = math.cos(a) * r, math.sin(a) * r
        n.line([(xy[0] - dx, xy[1] - dy), (xy[0] + dx, xy[1] + dy)], col, 5, k=k)

def dim_bg(v, **kw):
    can, n, cr = base_map(v, **kw); return can, n, cr

def s02a(t):
    a, b = SC["02a"]; v = lerpv(V_REGION(), V_CRIMEA(), ramp(t, a, b, "sine"))
    can, n, cr = base_map(v, occ=True)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.45)
    for j, (word, txt, col) in enumerate((("map", "THE MAP", CYAN), ("history", "200 YEARS", GOLD), ("bridge", "ONE BRIDGE", ORANGE))):
        tj = wq("02a", word, 0.25 + 0.25 * j); x = W * (0.25 + 0.25 * j); y = H * 0.50
        if t >= tj:
            k = ramp(t, tj, tj + 0.35, "cubic"); r = 120 * k
            n.line([(x + math.cos(i / 40 * 2 * math.pi) * r, y + math.sin(i / 40 * 2 * math.pi) * r) for i in range(41)], col, 7)
    can = n.draw(can)
    for j, (word, txt, col, ic) in enumerate((("map", "THE MAP", CYAN, "el_anchor"), ("history", "200 YEARS", GOLD, "el_sailship"), ("bridge", "ONE BRIDGE", ORANGE, "el_truck"))):
        tj = wq("02a", word, 0.25 + 0.25 * j); x = W * (0.25 + 0.25 * j)
        put_icon(can, ic, 150, (x, H * 0.50), t, tj + 0.1)
        put_text(can, txt, 46, col, x, H * 0.50 + 175, t, tj + 0.15, stroke=7)
    return can

def s05a(t):
    a, b = SC["05a"]; v = lerpv(V_CRIMEA(), View(34.0, 46.0, 4.5), ramp(t, a, a + 1.5, "inout"))
    can, n, cr = base_map(v)
    px, py = v.P(*PEREK); td = wq("05a", "defenders", 0.25)
    if t >= td:   # flechas del norte que chocan con el istmo
        for j in range(3):
            p0 = (px - 120 + 120 * j, py - 330); p1 = (px - 40 + 40 * j, py - 70)
            arrow(n, [p0, p1], ramp(t, td + 0.15 * j, td + 0.7 + 0.15 * j, "cubic"), RED, 9)
        sh = [(px - 70, py - 60), (px + 70, py - 60), (px + 70, py + 10), (px, py + 70), (px - 70, py + 10), (px - 70, py - 60)]
        n.line(sh, CYAN, 8, k=ramp(t, td + 0.5, td + 0.9))
    ts = wq("05a", "supply", 0.6)
    lines = [[v.P(33.7, 46.7), v.P(*PEREK), v.P(34.0, 45.6)], [v.P(34.6, 46.6), v.P(*CHON), v.P(34.5, 45.6)]]
    if t >= ts:
        for j, ln in enumerate(lines):
            pts = path_px(v, [], 2) if False else []
            n.line(ln, GOLD, 8, k=1 - ramp(t, wq("05a", "cut", 0.85), wq("05a", "cut", 0.85) + 0.4) * 0.7)
    can = n.draw(can)
    tc = wq("05a", "cut", 0.85)
    if t >= tc:
        for ln in lines: put_text(can, "X", 110, (255, 60, 50), ln[1][0], ln[1][1], t, tc, stroke=10)
    label(can, "HELPS DEFENDERS", (W * 0.76, H * 0.25), t, td + 0.3, CYAN, 46)
    label(can, "HARD TO SUPPLY", (W * 0.76, H * 0.33), t, ts + 0.2, GOLD, 46)
    return can

def s06a(t):
    a, b = SC["06a"]; v = lerpv(View(36.0, 50.5, 40), View(30.8, 42.7, 22), ramp(t, wq("06a", "Sevastopol", 0.3) - 0.3, wq("06a", "Bosphorus", 0.65), "inout"))
    can, n, cr = base_map(v, a_cr=0.25)
    tf = wq("06a", "ice", 0.12)
    if t >= tf:
        for j, p in enumerate((SPB, (39.0, 47.3))):
            snowflake(n, v.P(*p), 34 * ramp(t, tf + 0.15 * j, tf + 0.5 + 0.15 * j, "back"), LBLUE)
    sx, sy = v.P(*SEV); tsv = wq("06a", "Sevastopol", 0.3)
    if t >= tsv: n.dot((sx, sy), GREEN, 30 + 6 * math.sin(t * 6))
    tts = wq("06a", "Bosphorus", 0.65)
    route = curve(v.P(*SEV), v.P(*BOSPORUS), 0.18, 40) + curve(v.P(*BOSPORUS), v.P(*AEGEAN), -0.1, 20)[1:]
    if t >= wq("06a", "route", 0.5) - 0.2:
        fr = ramp(t, wq("06a", "route", 0.5) - 0.2, tts + 1.4, "inout")
        dashes(n, partial(route, fr), GOLD, 7, t, 50)
    can = n.draw(can)
    label(can, "ICE", (v.P(*SPB)[0] + 70, v.P(*SPB)[1]), t, tf + 0.2, LBLUE, 40)
    label(can, "ICE-FREE", (sx + 20, sy - 70), t, tsv + 0.2, (150, 255, 170), 44)
    label(can, "TURKEY CONTROLS", v.P(31.2, 42.6), t, wq("06a", "controls", 0.95), GOLD, 42)
    label(can, "TURKISH STRAITS", (v.P(*BOSPORUS)[0] + 40, v.P(*BOSPORUS)[1] + 60), t, tts, WHITE, 38)
    label(can, "MEDITERRANEAN", (v.P(*AEGEAN)[0] + 30, v.P(*AEGEAN)[1] - 60), t, wq("06a", "Mediterranean", 0.85), LBLUE, 40)
    return can

def s06b(t):
    a, b = SC["06b"]; v = lerpv(View(31.0, 45.0, 22), View(33.5, 43.8, 16), ramp(t, a, a + 1.5, "inout"))
    can, n, cr = base_map(v)
    sx, sy = v.P(*SEV); tw = wq("06b", "watching", 0.2)
    ring_wave(n, (sx, sy), t, tw if t >= tw else 1e9, CYAN, 30, 700, 2.4)
    n.dot((sx, sy), CYAN, 26)
    route = curve(v.P(*SEV), v.P(*BOSPORUS), 0.18, 40)
    tsd = wq("06b", "warships", 0.65)
    if t >= tsd: dashes(n, partial(route, ramp(t, tsd, tsd + 2.0)), GOLD, 6, t, 50, k=0.7)
    can = n.draw(can)
    if t >= tsd: put_icon(can, "el_warship", 170, at_path(route, ramp(t, tsd, tsd + 2.6, "inout")), t, tsd - 0.1)
    label(can, "BLACK SEA", v.P(34.5, 43.2), t, a + 0.3, LBLUE, 48)
    put_text(can, "WARTIME: STRAITS CLOSED", 52, (255, 150, 140), W * 0.5, H * 0.24 + 40, t, wq("06b", "Turkey", 0.65), stroke=8)
    return can

def s09a(t):
    a, b = SC["09a"]; v = lerpv(View(34.2, 46.2, 8.5), View(33.9, 45.0, 5.0), ramp(t, a + 1.0, a + 3.0, "inout"))
    tr = wq("09a", "retook", 0.75)
    can, n, cr = base_map(v, crimea=RED, ua=None, ru=None, a_cr=0.22)
    ts = wq("09a", "Second", 0.1)
    if t < tr:
        for j in range(3):
            p0 = v.P(33.3 + 0.7 * j, 47.4); p1 = v.P(33.6 + 0.4 * j, 45.3 - 0.2 * j)
            arrow(n, curve(p0, p1, 0.08 - 0.06 * j, 30), ramp(t, ts + 0.2 * j, ts + 1.6 + 0.2 * j, "cubic"), GREY, 10)
    sx, sy = v.P(*SEV); tb = wq("09a", "besieged", 0.3)
    if tb <= t < tr:
        fr = ramp(t, tb, tb + 0.8, "cubic"); r = 120
        ring = [(sx + math.cos(math.radians(200 + i * 1.6)) * r * 1.2, sy + math.sin(math.radians(200 + i * 1.6)) * r) for i in range(int(110 * fr) + 1)]
        if len(ring) > 1: n.line(ring, GREY, 9)
    if t >= tr:
        for j in range(3):
            p0 = v.P(33.6 + 0.5 * j, 47.4); p1 = v.P(33.8 + 0.3 * j, 45.0 - 0.1 * j)
            arrow(n, curve(p0, p1, -0.08 + 0.05 * j, 30), ramp(t, tr + 0.15 * j, tr + 1.3 + 0.15 * j, "cubic"), RED, 11)
    n.dot((sx, sy), RED, 24 + 6 * math.sin(t * 8))
    can = n.draw(can)
    if t < tr:
        put_icon(can, "el_ww2_tank", 220, (W * 0.18, H * 0.66), t, ts + 0.3, tr - 0.2)
        te = wq("09a", "eight", 0.5); put_text(can, "~8 MONTHS", 64, WHITE, W * 0.78, H * 0.26, t, te, stroke=9, t1=tr)
        label(can, "SIEGE 1941–42", (sx + 30, sy - 120), t, tb + 0.2, WHITE, 44, t1=tr)
    else:
        put_icon(can, "el_soviet_ww2", 300, (W * 0.82, H * 0.60), t, tr)
        put_text(can, "1944", 70, (255, 170, 160), W * 0.82, H * 0.26, t, tr + 0.3, stroke=9)
    return can

def s10a(t):
    a, b = SC["10a"]; v = View(48.0, 45.0, 44)
    can, n, cr = base_map(v, crimea=GREEN, ua=None, ru=None, a_cr=0.3)
    p0 = v.P(34.4, 45.4)
    for j, dst in enumerate(((64.0, 41.3), (68.0, 40.5), (58.0, 52.0))):
        arrow(n, curve(p0, v.P(*dst), -0.12 - 0.05 * j, 50), 1.0, GREY, 7, ) if False else n.line(curve(p0, v.P(*dst), -0.12 - 0.05 * j, 50), GREY, 6, k=0.6)
    tr = wq("10a", "return", 0.8)
    if t >= tr: arrow(n, curve(v.P(64.0, 41.3), p0, 0.15, 50), ramp(t, tr, tr + 1.6, "inout"), (150, 255, 170), 8)
    can = n.draw(can)
    tn = wq("10a", "hundred", 0.15); cnt = int(190000 * ramp(t, tn, tn + 1.6, "cubic") / 1000) * 1000
    if t >= tn: put_text(can, f"{cnt:,}", 96, WHITE, W * 0.30, H * 0.30, t, tn, stroke=11, pop=False)
    if t >= tn: put_text(can, "DEPORTED", 48, (220, 220, 220), W * 0.30, H * 0.40, t, tn + 0.2, stroke=7)
    td = wq("10a", "died", 0.5)
    put_text(can, "TENS OF THOUSANDS DIED", 46, (255, 150, 140), W * 0.30, H * 0.50, t, td, stroke=7)
    put_icon(can, "el_family", 240, (W * 0.80, H * 0.66), t, a + 0.1, tr)
    if t >= tr: put_text(can, "LATE 1980s: RETURN", 50, (150, 255, 170), W * 0.70, H * 0.80 - 120, t, tr + 0.4, stroke=8)
    return can

def s12a(t):
    a, b = SC["12a"]; v = lerpv(View(33.5, 48.3, 17), V_CRIMEA(), ramp(t, a, a + 1.6, "inout"))
    can, n, cr = base_map(v, crimea=BLUE, a_cr=0.35)
    can = n.draw(can)
    label(can, "AUTONOMOUS REPUBLIC", v.P(34.3, 45.25), t, wq("12a", "autonomous", 0.2), WHITE, 50)
    put_text(can, "RUSSIAN-SPEAKING MAJORITY", 46, (255, 200, 190), W * 0.5, H * 0.25, t, wq("12a", "Russian-speaking", 0.45), stroke=7)
    tf = wq("12a", "Fleet", 0.8); sx, sy = v.P(*SEV)
    put_icon(can, "el_warship", 210, (sx - 120, sy + 150 + 5 * math.sin(t * 2)), t, tf - 0.4)
    put_text(can, "?", 120, YEL, sx - 120, sy + 30, t, tf, stroke=10)
    return can

def s12b(t):
    a, b = SC["12b"]; v = View(33.7, 44.75, 2.6); can, n, cr = base_map(v)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.35)
    sx, sy = v.P(*SEV); n.dot((sx, sy), CYAN, 24); can = n.draw(can)
    td = wq("12b", "divided", 0.25); sp = ramp(t, td, td + 1.2, "inout")
    put_icon(can, "el_warship", 240, (W * 0.50 - 260 * sp, H * 0.70 + 5 * math.sin(t * 2)), t, a + 0.1)
    put_icon(can, "el_warship", 240, (W * 0.50 + 260 * sp, H * 0.70 + 5 * math.sin(t * 2 + 1)), t, a + 0.1, flip=True)
    if t >= td: put_text(can, "1997", 60, WHITE, W * 0.5, H * 0.52, t, td + 0.3, stroke=8)
    te = wq("12b", "extended", 0.55)
    put_icon(can, "el_contract", 220, (W * 0.30, H * 0.36), t, te, rot=8)
    put_text(can, "LEASE → 2042", 58, YEL, W * 0.30, H * 0.36 + 120, t, wq("12b", "forty-two", 0.75), stroke=8)
    put_icon(can, "el_gas_pipe", 220, (W * 0.74, H * 0.36), t, wq("12b", "gas", 0.9))
    put_text(can, "CHEAPER GAS", 50, CYAN, W * 0.74, H * 0.36 + 120, t, wq("12b", "gas", 0.9) + 0.15, stroke=8)
    return can

def s13a(t):
    a, b = SC["13a"]; v = lerpv(View(33.7, 46.5, 10), View(31.3, 49.7, 12), ramp(t, a, a + 1.6, "inout"))
    can, n, cr = base_map(v, a_cr=0.25)
    kx, ky = v.P(*KYIV); tp = wq("13a", "protests", 0.5)
    if t >= tp: ring_wave(n, (kx, ky), t, tp, GOLD, 20, 200, 1.2)
    n.dot((kx, ky), GOLD, 26)
    can = n.draw(can)
    label(can, "KYIV", (kx, ky - 70), t, wq("13a", "Kyiv", 0.2), WHITE, 50)
    put_icon(can, "el_protesters", 420, (W * 0.70, H * 0.62), t, tp)
    tt = wq("13a", "fled", 0.6)
    put_text(can, "PRO-RUSSIAN PRESIDENT", 48, (255, 190, 180), W * 0.30, H * 0.30, t, tt, stroke=7)
    put_text(can, "OUSTED", 76, (255, 70, 60), W * 0.30, H * 0.39, t, tt + 0.2, stroke=9)
    put_text(can, "FEB 2014", 50, WHITE, W * 0.30, H * 0.22, t, wq("13a", "early", 0.4), stroke=7)
    return can

def s14a(t):
    a, b = SC["14a"]; v = V_CRIMEA(); can, n, cr = base_map(v, occ=True)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.35); can = n.draw(can)
    tn = wq("14a", "hundred", 0.2); cnt = int(100 * ramp(t, tn - 0.3, tn + 0.9, "cubic"))
    if t >= tn - 0.3:
        put_text(can, str(cnt), 150, (120, 200, 255), W * 0.30, H * 0.40, t, tn - 0.3, stroke=12, pop=False)
        put_text(can, "COUNTRIES AT THE UN", 46, WHITE, W * 0.30, H * 0.52, t, tn, stroke=7)
        put_text(can, "BACK UKRAINE'S BORDERS", 46, (170, 210, 255), W * 0.30, H * 0.59, t, wq("14a", "borders", 0.45), stroke=7)
    ta = wq("14a", "admitted", 0.75)
    put_icon(can, "el_little_green", 300, (W * 0.74, H * 0.58), t, ta - 0.6)
    if t >= ta: put_text(can, "RUSSIAN TROOPS", 64, (255, 70, 60), W * 0.74, H * 0.36, t, ta + 0.2, stroke=9)
    return can

def s15a(t):
    a, b = SC["15a"]; v = View(34.4, 45.75, 4.6)
    tc = wq("15a", "collapsed", 0.25); dry = ramp(t, tc, tc + 1.5, "inout")
    can, n, pts = canal_scene(t, v, {"flow": 0.0})
    north = Image.new("L", (W, H)); ImageDraw.Draw(north).ellipse((v.P(33.3, 46.05)[0], v.P(33.3, 46.05)[1], v.P(35.6, 45.15)[0], v.P(35.6, 45.15)[1]), fill=255)
    m = ImageChops.multiply(north.filter(ImageFilter.GaussianBlur(40)), geomask(v, "cr", M.G["crimea"]))
    col = tuple(int(lerp(g, br, dry)) for g, br in zip((60, 170, 80), (150, 100, 50)))
    can = Image.composite(Image.new("RGB", (W, H), col), can, m.point(lambda x: int(x * 0.55)))
    can = n.draw(can)
    tr = wq("15a", "Rice", 0.45); put_text(can, "RICE FIELDS", 50, (200, 255, 170), W * 0.76, H * 0.26, t, tr, stroke=7)
    if t >= tr + 0.5: put_text(can, "X", 120, (255, 60, 50), W * 0.76, H * 0.27, t, tr + 0.5, stroke=10)
    trs = wq("15a", "reservoirs", 0.75); lvl = 1 - 0.7 * ramp(t, trs, trs + 1.5)
    if t >= trs:
        x0, y0 = W * 0.72, H * 0.40; d = ImageDraw.Draw(can)
        d.rectangle((x0, y0, x0 + 150, y0 + 200), outline=(220, 220, 220), width=6)
        d.rectangle((x0 + 6, y0 + 200 - 194 * lvl, x0 + 144, y0 + 194), fill=(60, 140, 230))
        put_text(can, "RESERVOIRS", 40, LBLUE, x0 + 75, y0 + 240, t, trs, stroke=6)
    return can

def s16a(t):
    a, b = SC["16a"]; v = lerpv(View(34.6, 46.0, 7.5), View(35.0, 45.85, 6.5), ramp(t, a, b, "sine"))
    tb = wq("16a", "attacks", 0.35); tp = wq("16a", "cuts", 0.55)
    dark = ramp(t, tp, tp + 1.0)
    tcab = wq("16a", "undersea", 0.85)
    if t >= tcab: dark *= 1 - ramp(t, tcab + 0.6, tcab + 1.6)
    can, n, cr = base_map(v, a_cr=0.3, occ=True)
    can = Image.composite(Image.new("RGB", (W, H), (3, 4, 8)), can, cr.point(lambda x: int(x * 0.85 * dark)))
    lines = [v.P(33.4, 46.7), v.P(33.7, 46.2), v.P(34.0, 45.6)], [v.P(34.6, 46.6), v.P(34.4, 46.05), v.P(34.4, 45.6)]
    for ln in lines: n.line(ln, GOLD, 6, k=1 - ramp(t, tb, tb + 0.3))
    if t >= tcab:
        cab = [v.P(37.3, 45.15), v.P(36.9, 45.2), v.P(36.5, 45.28)]
        dashes(n, partial(path_px(v, [(37.3, 45.15), (36.9, 45.2), (36.5, 45.28)], 30), ramp(t, tcab, tcab + 1.0)), CYAN, 7, t, 60)
    can = n.draw(can)
    for j, ln in enumerate(lines):
        rot = 75 * ramp(t, tb + 0.1 * j, tb + 0.7 + 0.1 * j, "cubic")
        put_icon(can, "el_pylon", 170, (ln[0][0], ln[0][1] - 40), t, wq("16a", "electricity", 0.15), bob=False, rot=rot * (1 if j else -1))
        if t >= tb: put_icon(can, "el_explosion", 120, (ln[0][0], ln[0][1] - 20), t, tb + 0.1 * j, tb + 0.8 + 0.1 * j, bob=False)
    if t >= tp: label(can, "LIGHTS OUT", v.P(34.3, 45.3), t, tp + 0.3, (200, 200, 200), 60, t1=tcab + 1.2)
    put_text(can, "NOV 2015", 54, WHITE, W * 0.82, H * 0.24, t, wq("16a", "November", 0.3), stroke=8)
    if t >= tcab: label(can, "UNDERSEA POWER LINK", (v.P(36.9, 45.2)[0], v.P(36.9, 45.2)[1] + 90), t, tcab + 0.3, CYAN, 40)
    return can

def s17a(t):
    a = SC["17"][0]; f = int((t - a) * FPS) + 1; can = frame3d("fly", f)
    put_text(can, "EUROPE'S LONGEST BRIDGE", 60, WHITE, W * 0.5, H * 0.30, t, wq("17a", "longest", 0.2), stroke=9)
    put_text(can, "$3+ BILLION", 70, GOLD, W * 0.5, H * 0.40, t, wq("17a", "billion", 0.5), stroke=9)
    put_text(can, "OPENED · MAY 2018", 46, (220, 220, 220), W * 0.5, H * 0.48, t, wq("17a", "opened", 0.75), stroke=7)
    small_tag(can, "ANIMATED RECONSTRUCTION", t)
    return can

def s18a(t):
    a, b = SC["18a"]; v = lerpv(View(36.56, 45.31, 2.2), View(36.8, 46.25, 6.5), ramp(t, a + 0.3, a + 2.2, "inout"))
    can, n = region_scene(t, v)
    mx, my = v.P(*MARIU); bx_, by_ = v.P(*BERD); tm = wq("18a", "Mariupol", 0.45)
    for p in ((mx, my), (bx_, by_)): n.dot(p, (120, 200, 255), 20, 0.4 + 0.6 * (1 - ramp(t, tm + 1.5, tm + 3.0)))
    can = n.draw(can)
    bx, by = v.P(*ARCH_LL)
    ti = wq("18a", "inspections", 0.85)
    for j in range(3):
        put_icon(can, "el_cargo_ship", 130, (bx + 60 + 110 * j, by - 70 - 45 * j + 4 * math.sin(t * 2 + j)), t, wq("18a", "Ships", 0.35) + 0.15 * j)
    label(can, "MARIUPOL", (mx, my + 50), t, tm, WHITE, 38); label(can, "BERDIANSK", (bx_, by_ + 50), t, tm + 0.3, WHITE, 36)
    label(can, "SEA OF AZOV", v.P(36.4, 46.2), t, a + 0.4, LBLUE, 44)
    if t >= ti: put_text(can, "HELD FOR INSPECTIONS", 52, YEL, W * 0.5, H * 0.30, t, ti, stroke=8)
    return can

def s18b(t):
    a, b = SC["18b"]; v = View(36.56, 45.29, 1.8); can, n = region_scene(t, v)
    bx, by = v.P(*ARCH_LL); tf = wq("18b", "fired", 0.55)
    if t >= tf: ring_wave(n, (bx - 120, by + 160), t, tf, RED, 10, 120, 0.9)
    can = n.draw(can)
    put_icon(can, "el_tanker", 260, (bx, by + 20), t, wq("18b", "tanker", 0.3), bob=False)
    tth = wq("18b", "three", 0.5); ts = wq("18b", "seized", 0.85)
    for j in range(3):
        x = lerp(W * 0.05, bx - 220 + 90 * j, ramp(t, tth - 0.6, tth + 1.0, "inout")); y = by + 200 + 50 * j
        put_icon(can, "el_patrol_boat", 120, (x, y), t, tth - 0.6)
        if t >= tf: put_icon(can, "el_explosion", 80, (x + 20, y - 10), t, tf + 0.15 * j, tf + 0.7 + 0.15 * j, bob=False)
        if t >= ts: put_text(can, "X", 80, (255, 60, 50), x, y, t, ts + 0.1 * j, stroke=8)
    put_text(can, "NOV 2018", 54, WHITE, W * 0.82, H * 0.24, t, a + 0.2, stroke=8)
    if t >= ts: put_text(can, "24 SAILORS CAPTURED", 46, WHITE, W * 0.5, H * 0.80 - 80, t, ts + 0.3, stroke=7)
    return can

def s20a(t):
    a, b = SC["20a"]; v = lerpv(View(34.0, 45.6, 9.0), View(31.4, 45.6, 6.0), ramp(t, a, a + 2.0, "inout"))
    can, n, cr = base_map(v, occ=True)
    mx, my = v.P(*MOSKVA_LL); ox, oy = v.P(*ODESA)
    th = wq("20a", "hit", 0.55); tsk = wq("20a", "sank", 0.9)
    tm = wq("20a", "missiles", 0.45)
    path = curve((ox, oy + 30), (mx, my), 0.25, 30)
    if tm <= t < th + 0.1: n.line(partial(path, ramp(t, tm, th)), ORANGE, 5, k=0.8)
    if t >= th: ring_wave(n, (mx, my), t, th, ORANGE, 15, 160, 1.2)
    can = n.draw(can)
    sink = ramp(t, tsk - 0.2, tsk + 1.4, "inout")
    if sink < 0.98: put_icon(can, "el_warship", 220, (mx, my + 80 * sink), t, a + 0.2, rot=-22 * sink, bob=sink < 0.05)
    if tm <= t < th: put_icon(can, "el_missile", 110, at_path(path, ramp(t, tm, th)), t, tm, bob=False)
    if t >= th: put_icon(can, "el_explosion", 160, (mx, my - 20), t, th, th + 1.0, bob=False)
    label(can, "MOSKVA", (mx, my - 120), t, wq("20a", "Moskva", 0.7), WHITE, 50, t1=tsk + 1.4)
    label(can, "ODESA", (ox, oy - 50), t, a + 0.4, WHITE, 38)
    put_text(can, "APR 2022", 54, WHITE, W * 0.82, H * 0.24, t, wq("20a", "April", 0.3), stroke=8)
    if t >= tsk: put_text(can, "SUNK", 90, (255, 70, 60), mx, my + 10, t, tsk + 0.4, stroke=10)
    return can

def s21a(t):
    a, b = SC["21a"]; v = lerpv(View(33.8, 44.9, 4.0), View(35.6, 44.9, 8.0), ramp(t, wq("21a", "east", 0.6) - 0.5, wq("21a", "Novorossiysk", 0.85), "inout"))
    can, n, cr = base_map(v, occ=True)
    sx, sy = v.P(*SEV); nx, ny = v.P(*NOVOR); ts = wq("21a", "struck", 0.2)
    if t >= ts: ring_wave(n, (sx, sy), t, ts, ORANGE, 15, 150, 1.1)
    te = wq("21a", "east", 0.6)
    route = curve((sx, sy + 20), (nx, ny + 20), 0.12, 40)
    if t >= te: dashes(n, partial(route, ramp(t, te, te + 1.5)), GOLD, 6, t, 50)
    n.dot((nx, ny), RED, 20, 0.8)
    can = n.draw(can)
    for j in range(3):
        put_icon(can, "el_explosion", 110, (sx - 40 + 50 * j, sy - 20 + 25 * (j % 2)), t, ts + 0.25 * j, ts + 0.9 + 0.25 * j, bob=False)
    label(can, "FLEET HQ", (sx, sy - 90), t, wq("21a", "headquarters", 0.45), WHITE, 42)
    put_text(can, "SEP 2023", 54, WHITE, W * 0.82, H * 0.24, t, wq("21a", "September", 0.5), stroke=8)
    if t >= te:
        for j in range(2): put_icon(can, "el_warship", 140, at_path(route, ramp(t, te + 0.2 * j, te + 2.2 + 0.2 * j, "inout")), t, te + 0.2 * j)
    label(can, "NOVOROSSIYSK", (nx, ny - 60), t, wq("21a", "Novorossiysk", 0.85), (255, 170, 160), 40)
    return can

def s28a(t):
    a, b = SC["28a"]; v = View(35.6, 46.8, 9.0)
    can, n = region_scene(t, v, corridor=1.0, br=1.0, front=1.0)
    tr = wq("28a", "railways", 0.3)
    rail = path_px(v, [ROSTOV, MARIU, (36.78, 46.75), MELIT, DZHAN], 80)
    if t >= tr: dashes(n, partial([(x, y + 14) for x, y in rail], ramp(t, tr, tr + 1.4)), CYAN, 6, t, 60)
    tf = wq("28a", "vulnerable", 0.85)
    if t >= tf: n.line(path_px(v, FRONT, 80), RED, 10, k=0.5 + 0.5 * math.sin(t * 7) ** 2)
    can = n.draw(can)
    if t >= tr + 0.4: put_icon(can, "el_fuel_train", 120, at_path([(x, y + 14) for x, y in rail], ((t - tr - 0.4) / 6.0) % 1.0), t, tr + 0.4, bob=False)
    label(can, "RAIL THROUGH OCCUPIED UKRAINE", (W * 0.5, H * 0.22 + 40), t, tr + 0.3, CYAN, 40)
    if t >= tf:
        for j, u in enumerate((0.3, 0.55)): put_icon(can, "el_explosion", 80, at_path(rail, u), t, tf + 0.2 * j, tf + 1.0 + 0.2 * j, bob=False)
    return can

def s29a(t):
    a, b = SC["29a"]; v = View(36.0, 46.2, 13); can, n, cr = base_map(v, a_cr=0.15, a_ua=0.08, a_ru=0.08, edges=False)
    can = Image.blend(can, Image.new("RGB", (W, H), (6, 10, 20)), 0.55).filter(ImageFilter.GaussianBlur(3))
    tu = wq("29a", "Ukraine", 0.1); tr = wq("29a", "Moscow", 0.5)
    ang = 9 * math.sin((t - a) * 1.6) * (1 - 0.5 * ramp(t, tr, b))
    put_icon(can, "el_scale", 520, (W * 0.5, H * 0.56), t, a + 0.1, bob=False, rot=ang)
    lx, ly = W * 0.5 - 170, H * 0.555 + 170 * math.sin(math.radians(ang))
    rx, ry = W * 0.5 + 165, H * 0.555 - 165 * math.sin(math.radians(ang))
    n = Neon(); cv = View(34.4, 45.4, 4.6); ol = crimea_outline(cv); s_ = 0.11
    poly = [(rx + (x - W / 2) * s_, ry - 40 + (y - H / 2) * s_) for x, y in ol]
    n.line(poly, BLUE, 5, True, 1.0); can = n.draw(can)
    for j in range(3): put_icon(can, "el_explosion", 70, (lx - 45 + 45 * j, ly - 30 - 25 * (j % 2)), t, wq("29a", "cost", 0.25) + 0.15 * j, bob=False)
    put_text(can, "UKRAINE: RAISE THE COST", 50, (170, 210, 255), W * 0.27, H * 0.22 + 40, t, tu, stroke=7)
    put_text(can, "MOSCOW: HEAVILY INVESTED", 50, (255, 170, 160), W * 0.73, H * 0.22 + 40, t, tr, stroke=7)
    return can

SCENES = [("01", s01), ("02", s02), ("02a", s02a), ("03", s03), ("04", s04), ("05", s05), ("05a", s05a), ("06", s06), ("06a", s06a), ("06b", s06b),
          ("07", s07_08), ("09", s09), ("09a", s09a), ("10", s10), ("10a", s10a), ("11", s11_12), ("12a", s12a), ("12b", s12b), ("13", s13), ("13a", s13a),
          ("14", s14), ("14a", s14a), ("15", s15), ("15a", s15a), ("16", s16), ("16a", s16a), ("17", s17), ("17a", s17a), ("18", s18), ("18a", s18a),
          ("18b", s18b), ("19", s19), ("20", s20), ("20a", s20a), ("21", s21), ("21a", s21a), ("22", s22), ("23", s23), ("24", s24), ("25", s25),
          ("26", s26), ("27", s27_28), ("28a", s28a), ("29", s29), ("29a", s29a), ("30", s30)]

# ---------------- efectos globales ----------------
CUTS = [SC[k][0] for k in sorted(SC)][1:]
SHAKES = []; FLASHES = []
def post(can, t):
    s = 1.0
    for c in CUTS:
        if 0 <= t - c < 0.18: s = 1 + 0.04 * (1 - ease((t - c) / 0.18))
    dx = dy = 0.0
    for t0, amp in SHAKES:
        if 0 <= t - t0 < 0.6:
            a = amp * math.exp(-(t - t0) * 8); dx += a * math.sin(t * 91); dy += a * math.cos(t * 77)
    if s > 1.001 or abs(dx) + abs(dy) > 0.5:
        s = max(s, 1.03); big = can.resize((int(W * s), int(H * s)), Image.BILINEAR)
        x0 = (big.width - W) / 2 + dx; y0 = (big.height - H) / 2 + dy
        can = big.crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
    for t0, dur, a in FLASHES:
        if 0 <= t - t0 < dur: can = Image.blend(can, Image.new("RGB", (W, H), (255, 255, 255)), a * (1 - (t - t0) / dur))
    return can

def frame(t):
    init()
    fn = SCENES[0][1]
    for sid, f in SCENES:
        if t >= SC[sid][0]: fn = f
    can = fn(t)
    headline(can, t); subtitle(can, t)
    return post(can, t)

SFX = []
def ev(t, kind, vol=None, **kw):
    e = {"t": round(t, 3), "type": kind, **kw}
    if vol is not None: e["vol"] = vol
    SFX.append(e)

def plan_fx():
    td = wt("01", "dropped")
    SHAKES.extend([(wq("20a", "hit", 0.55), 10), (wq("16a", "attacks", 0.35), 8), (wq("18b", "fired", 0.55), 6), (td + 0.3, 18), (wt("23", "bomb"), 16), (wt("26", "down") + 0.2, 14), (wt("03", "collapsed"), 8), (wt("24", "damaged"), 10),
                   (wt("21", "destroyed"), 8), (wt("12", "collapsed"), 8)])
    FLASHES.extend([(td + 0.3, 0.2, 0.5), (wt("23", "bomb"), 0.2, 0.6)])
    ev(0.0, "creak", 0.12); ev(td + 0.25, "boom", 0.4); ev(td + 0.6, "boom", 0.2)
    ev(SC["02"][0] + 0.2, "click", 0.15); ev(wt("02", "another"), "creak", 0.06); ev(wt("02", "matter"), "pop")
    ev(wt("03", "collapsed"), "boom", 0.25); ev(wt("03", "rail"), "pop"); ev(wt("03", "resumed"), "click", 0.15)
    ev(SC["04"][0] + 0.1, "pop"); ev(wt("04", "vulnerable"), "creak", 0.06)
    ev(wt("05", "Black"), "pop"); ev(wt("05", "Azov"), "pop"); ev(wt("05", "Perekop"), "click", 0.2)
    ev(wt("06", "Sevastopol"), "pop"); ev(wt("06", "navy"), "creak", 0.05)
    ev(wt("07", "Tatars"), "pop"); ev(wt("07", "Khanate"), "click", 0.15)
    ev(wt("08", "seventeen"), "boom", 0.18); ev(wt("08", "Catherine"), "pop")
    for w in ("Britain", "France", "Ottoman"): ev(wt("09", w), "pop")
    tb = wt("09", "besieged")
    for j in range(4): ev(tb + 0.8 + j * 0.9, "boom", 0.12)
    ev(wt("09", "lost"), "click", 0.2)
    ev(wt("10", "deportation"), "creak", 0.06); ev(wt("10", "Tatar"), "pop")
    ev(wt("11", "transferred"), "click", 0.22); ev(wt("12", "collapsed"), "boom", 0.25); ev(wt("12", "border"), "click", 0.15)
    ev(wt("13", "lease"), "pop"); ev(wt("13", "naval"), "pop")
    for j in range(4): ev(wt("14", "soldiers") + 0.15 * j, "pop")
    ev(wt("14", "annexed"), "boom", 0.2); ev(wt("14", "rejected"), "click", 0.2)
    ev(wt("15", "blocking"), "creak", 0.08); ev(wt("16", "direct"), "click", 0.2); ev(wt("16", "ferries"), "pop")
    ev(wt("17", "nineteen"), "pop"); ev(wt("17", "opened"), "click", 0.15); ev(wt("17", "railway"), "click", 0.15)
    for w in ("fuel", "equipment", "troops"): ev(wt("18", w), "pop")
    ev(wt("19", "launch"), "mg", 0.05); ev(wt("19", "February"), "boom", 0.18)
    ev(wt("20", "corridor"), "creak", 0.06); ev(wt("21", "destroyed"), "boom", 0.25)
    ev(wt("22", "target"), "click", 0.25)
    ev(wt("23", "bomb"), "boom", 0.45); ev(wt("23", "fire"), "fire", 0.08, d=1.0)
    ev(wt("24", "sea"), "creak", 0.06); ev(wt("24", "damaged"), "boom", 0.3)
    for j in range(3): ev(wt("25", "explosives") + 0.12 * j, "boom", 0.15)
    ev(wt("25", "reopened"), "click", 0.2)
    ev(SC["26"][0], "creak", 0.1); ev(wt("26", "down") + 0.2, "boom", 0.4)
    ev(wt("27", "trucks"), "pop"); ev(wt("27", "trains"), "pop")
    for j in range(3): ev(wt("28", "attacks") + 0.15 * j, "boom", 0.12)
    ev(wt("28", "Sevastopol"), "pop"); ev(wt("29", "depends"), "boom", 0.2)
    ev(wt("30", "supplied"), "pop"); ev(wt("30", "comments"), "click", 0.15)
    for k_, w_ in (("map", "pop"), ("history", "pop"), ("bridge", "pop")): ev(wq("02a", k_), w_)
    ev(wq("05a", "defenders"), "click", 0.2); ev(wq("05a", "cut", 0.85), "click", 0.25)
    ev(wq("06a", "ice", 0.12), "pop"); ev(wq("06a", "Sevastopol", 0.3), "pop"); ev(wq("06a", "Bosphorus", 0.65), "creak", 0.05)
    ev(wq("06b", "watching", 0.2), "click", 0.15); ev(wq("06b", "warships", 0.65), "creak", 0.05)
    ev(wq("09a", "Second", 0.1), "mg", 0.05); ev(wq("09a", "besieged", 0.3), "boom", 0.15); ev(wq("09a", "retook", 0.75), "boom", 0.2)
    ev(wq("10a", "hundred", 0.15), "creak", 0.06); ev(wq("10a", "return", 0.8), "click", 0.15)
    ev(wq("12a", "autonomous", 0.2), "pop"); ev(wq("12b", "divided", 0.25), "creak", 0.06); ev(wq("12b", "extended", 0.55), "pop"); ev(wq("12b", "gas", 0.9), "pop")
    ev(wq("13a", "protests", 0.5), "pop"); ev(wq("13a", "fled", 0.6), "boom", 0.18)
    ev(wq("14a", "hundred", 0.2), "click", 0.2); ev(wq("14a", "admitted", 0.75), "boom", 0.18)
    ev(wq("15a", "collapsed", 0.25), "creak", 0.06); ev(wq("15a", "Rice", 0.45) + 0.5, "click", 0.2)
    ev(wq("16a", "attacks", 0.35), "boom", 0.3); ev(wq("16a", "cuts", 0.55), "click", 0.2); ev(wq("16a", "undersea", 0.85), "pop")
    ev(wq("17a", "longest", 0.2), "pop"); ev(wq("17a", "billion", 0.5), "pop")
    ev(wq("18a", "Ships", 0.35), "creak", 0.06); ev(wq("18a", "inspections", 0.85), "click", 0.2)
    ev(wq("18b", "tanker", 0.3), "pop"); ev(wq("18b", "fired", 0.55), "boom", 0.25); ev(wq("18b", "seized", 0.85), "click", 0.2)
    ev(wq("20a", "missiles", 0.45), "creak", 0.06); ev(wq("20a", "hit", 0.55), "boom", 0.35); ev(wq("20a", "sank", 0.9), "boom", 0.15)
    for j in range(3): ev(wq("21a", "struck", 0.2) + 0.25 * j, "boom", 0.18)
    ev(wq("21a", "east", 0.6), "creak", 0.06)
    ev(wq("28a", "railways", 0.3), "pop"); ev(wq("28a", "vulnerable", 0.85), "boom", 0.12)
    ev(wq("29a", "cost", 0.25), "boom", 0.15); ev(wq("29a", "Moscow", 0.5), "click", 0.15)
plan_fx()

def seg(args):
    i, f0, f1, out = args
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - f0) % 150 == 0: print(f"seg{i}: {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close(); p.wait(); return out

if __name__ == "__main__":
    a = sys.argv
    if "--prep" in a: prep(); sys.exit()
    if "--frame" in a:
        for v in a[a.index("--frame") + 1:]:
            frame(float(v)).save(os.path.join(PREP, f"test_{float(v):06.2f}.jpg"), quality=85)
        sys.exit()
    json.dump({"music": True, "bpm": 92, "music_vol": 0.07, "whoosh_cuts": True, "events": SFX}, open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "short_sfx.py"), HERE], check=True)
    t0 = float(a[a.index("--from") + 1]) if "--from" in a else 0.0; t1 = float(a[a.index("--to") + 1]) if "--to" in a else TOTAL
    F0, F1 = int(t0 * FPS), int(t1 * FPS); nw = 7; step = math.ceil((F1 - F0) / (nw * 4))
    tmp = tempfile.mkdtemp(prefix="v6_")
    jobs = [(i, f, min(F1, f + step), os.path.join(tmp, f"s{i:03d}.mp4")) for i, f in enumerate(range(F0, F1, step))]
    with Pool(nw) as pool: parts = pool.map(seg, jobs, chunksize=1)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "video.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    out = os.path.join(ROOT, "Render", "Video6_Crimea.mp4" if "--from" not in a else f"Video6_parte_{int(t0)}.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", vid, "-ss", str(t0), "-i", os.path.join(HERE, "voz.wav"), "-ss", str(t0), "-i", os.path.join(HERE, "sfx.wav"),
                    "-filter_complex", "[1:a]apad[v];[v][2:a]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-t", str(t1 - t0), out], check=True)
    print("listo", out)

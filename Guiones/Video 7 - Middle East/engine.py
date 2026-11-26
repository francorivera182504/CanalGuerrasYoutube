"""Motor reutilizable WarMap Stick (largos 1920x1080): cada escena es DATOS (storyboard.py), no una función.
Elementos de una escena (todos con disparo `at` = palabra de la escena | segundos desde el inicio | None=inicio):
  view / view2+move   vista del mapa (nombre en VIEWS o View) y movimiento opcional
  fill   (región, color, alfa, at)          región = país NE | nombre en REGIONS
  arrow  (desde, hasta, color, at, curva)   puntos (lon,lat) o nombre en PLACES
  salvo  (desde, hasta, n, color, at, intercept)
  icon   (sticker, pos, tamaño, at, hasta, flip)   pos (lon,lat) | [x,y] pantalla | nombre
  label  (texto, pos, color, at, tamaño)
  count  (desde, hasta, formato, pos, at, dur, tamaño, color)
  card   (texto, pos, color, at, ancho)       tarjeta/burbuja
  dot    (pos, color, at)  pulse (pos, color, at)
  shot   toma 3D (carpeta en render3d/) que se reproduce de fondo
  bg     'map' | 'dim' | 'stage'           ; fx: lista de (palabra, 'shake'|'flash'|'boom'...)
"""
import json, math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mapa as M
from mapa import View, Neon, W, H
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\ariblk.ttf"; FONT2 = r"C:\Windows\Fonts\arialbd.ttf"
FPS = 30
COL = dict(RED=(255, 60, 50), BLUE=(70, 160, 255), GREEN=(60, 220, 140), GOLD=(255, 190, 60), GREY=(150, 160, 175), WHITE=(255, 255, 255),
           YEL=(255, 214, 40), ORANGE=(255, 140, 40), CYAN=(60, 200, 255), PURPLE=(190, 120, 255), LBLUE=(190, 225, 255))
def C(c): return COL[c] if isinstance(c, str) else c

# ---------------- tiempos ----------------
TL = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
SC = {s["id"]: (s["start"], s["start"] + s["dur"]) for s in TL["timeline"]}
ORDER = [s["id"] for s in TL["timeline"]]
G = {s["id"]: s for s in json.load(open(os.path.join(HERE, "guion.json"), encoding="utf-8"))["scenes"]}
WORDS = TL["words"]; TOTAL = TL["total"] + 1.5
def clean(w): return w.lower().strip(".,?'’:;!\"()")
def wt(scene, word):
    if word is None: return SC[scene][0]
    if isinstance(word, (int, float)): return SC[scene][0] + word
    n = 0
    if ":" in word: word, n = word.split(":"); n = int(n)
    word = word.lower()
    def hit(w):
        c = clean(w["w"]); toks = [clean(x) for x in c.split()]
        return c == word or c.startswith(word) or word in c.split("-") or any(x == word or x.startswith(word) for x in toks)
    ws = [w for w in WORDS if w["scene"] == scene and hit(w)]
    if not ws: raise KeyError(f"{scene}: '{word}' no está en la escena")
    return ws[min(n, len(ws) - 1)]["s"]

def ease(x, kind="cubic"):
    x = min(1.0, max(0.0, x))
    if kind == "back": c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == "inout": return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind="inout"): return ease((t - t0) / max(1e-6, t1 - t0), kind)
def lerpv(v0, v1, k): return View(lerp(v0.lon, v1.lon, k), lerp(v0.lat, v1.lat, k), math.exp(lerp(math.log(v0.wdeg), math.log(v1.wdeg), k)))

# ---------------- geografía ----------------
PLACES = dict(TEHRAN=(51.39, 35.69), TELAVIV=(34.78, 32.08), JERUSALEM=(35.22, 31.77), GAZA=(34.45, 31.47), RAFAH=(34.25, 31.29), KHANYUNIS=(34.30, 31.35),
              BEIRUT=(35.50, 33.89), DAMASCUS=(36.29, 33.51), BAGHDAD=(44.36, 33.31), SANAA=(44.20, 15.35), HORMUZ=(56.45, 26.55), NATANZ=(51.92, 33.72),
              FORDOW=(50.99, 34.88), ISFAHAN=(51.67, 32.65), BAB=(43.40, 12.60), TIRAN=(34.45, 27.95), CAIRO=(31.24, 30.04), AMMAN=(35.93, 31.95),
              DOHA=(51.53, 25.29), SDEROT=(34.60, 31.52), HAIFA=(34.99, 32.79), RAMALLAH=(35.20, 31.90), CAPE=(18.5, -34.4), SUEZ=(32.55, 29.95),
              BANDAR=(56.27, 27.18), KHANKHAN=(35.55, 33.2), SINAI=(33.8, 29.6), GOLAN=(35.77, 33.0), LONDON=(-0.1, 51.5))
def place(p): return PLACES[p] if isinstance(p, str) else p
POLY = dict(
    PART_A1=[(35.10, 33.09), (35.40, 33.09), (35.43, 32.85), (35.30, 32.65), (35.07, 32.80)],
    PART_A2=[(35.0, 32.55), (35.57, 32.40), (35.57, 31.35), (35.05, 31.35), (34.90, 31.5), (34.95, 32.2)],
    PART_A3=[(34.65, 31.85), (34.75, 31.75), (34.40, 31.25), (34.27, 31.22), (34.22, 31.32), (34.55, 31.80)],
    SINAI_BOX=[(32.3, 31.4), (34.95, 31.4), (34.95, 29.5), (34.3, 27.6), (33.0, 27.9), (32.4, 29.9)],
    GOLAN=[(35.62, 33.27), (35.85, 33.33), (35.95, 32.85), (35.65, 32.70), (35.62, 32.95)],
    SHAH_BOX=[(44, 40), (64, 40), (64, 24), (44, 24)])
REGIONS = {}
def region(name):
    """anillos (lista de polígonos lon,lat) de una región."""
    if name in REGIONS: return REGIONS[name]
    if name in POLY: r = [POLY[name]]
    elif name == "GAZA": r = [min(M.country("Palestine"), key=lambda x: len(x))]
    elif name == "WB": r = [max(M.country("Palestine"), key=lambda x: len(x))]
    elif name == "MANDATE": r = M.country("Israel") + M.country("Palestine")
    elif name.startswith("COUNTRIES:"): r = [x for n in name[10:].split(",") for x in M.country(n)]
    else: r = M.country(name)
    REGIONS[name] = r; return r
def rmask(v, name):
    k = (name, round(v.lon, 3), round(v.lat, 3), round(v.wdeg, 3))
    if k not in D["masks"]:
        if len(D["masks"]) > 60: D["masks"].clear()
        if name == "SINAI": m = ImageChops.multiply(M.mask(v, region("Egypt")), M.mask(v, region("SINAI_BOX")))
        elif name == "PART_J":
            m = M.mask(v, region("MANDATE"))
            for a in ("PART_A1", "PART_A2", "PART_A3"): m = ImageChops.subtract(m, M.mask(v, region(a)))
        elif name == "PART_A": m = ImageChops.multiply(M.mask(v, region("MANDATE")).filter(ImageFilter.MaxFilter(5)), ImageChops.add(ImageChops.add(M.mask(v, region("PART_A1")), M.mask(v, region("PART_A2"))), M.mask(v, region("PART_A3"))))
        elif name == "ISRAEL49": m = ImageChops.subtract(M.mask(v, region("Israel")), M.mask(v, region("GOLAN")))
        else: m = M.mask(v, region(name))
        D["masks"][k] = m
    return D["masks"][k]

VIEWS = dict(levant=View(35.2, 31.8, 5.2), levant_w=View(35.8, 31.6, 9), mandate=View(35.0, 31.6, 3.6), gaza=View(34.40, 31.42, 0.75),
             wb=View(35.25, 31.9, 1.9), north=View(35.6, 33.1, 2.4), region=View(45.5, 29.5, 34), wide=View(42.0, 26.0, 46),
             iran=View(52.5, 32.0, 20), hormuz=View(56.4, 26.4, 5.5), gulf=View(53, 27.5, 14), redsea=View(40, 20, 26),
             africa=View(28, 4, 95), lebanon=View(35.7, 33.6, 3.0), sinai=View(34.0, 30.2, 8.5), ivl=View(44.0, 32.5, 24))
def V(x): return VIEWS[x] if isinstance(x, str) else x

# ---------------- utilidades de dibujo ----------------
D = {}
PREP = os.path.join(HERE, "_prep"); R3 = os.path.join(HERE, "render3d"); CAPDIRS = [os.path.join(ROOT, "Imagenes", "Video7", "capas"), os.path.join(ROOT, "Imagenes", "Video6", "capas")]
def init():
    if D: return
    M.load(); D.update(icons={}, texts={}, masks={}, bgs={}); D["subs"] = build_subs()

def cutout(path, thr=242):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).copy()
    white = (a[..., :3] >= thr).all(-1); lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    a[..., 3] = np.asarray(Image.fromarray(np.where(np.isin(lab, list(border)), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)))
    out = Image.fromarray(a); out = out.crop(out.getbbox())
    pad = 14; big = Image.new("RGBA", (out.width + 2 * pad, out.height + 2 * pad)); big.paste(out, (pad, pad))
    ring = big.getchannel("A").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(1.2))
    st = Image.new("RGBA", big.size, (255, 255, 255, 0)); st.putalpha(ring)
    return Image.alpha_composite(st, big)

def prep():
    os.makedirs(PREP, exist_ok=True)
    for d in CAPDIRS:
        for f in sorted(os.listdir(d)):
            out = os.path.join(PREP, "cut_" + f)
            if f.startswith("el_") and f.endswith(".png") and not os.path.exists(out):
                cutout(os.path.join(d, f)).save(out); print("cut", f)

def icon(name, size, flip=False):
    key = (name, int(size), flip)
    if key not in D["icons"]:
        p = os.path.join(PREP, "cut_" + name + ".png")
        im = Image.open(p) if os.path.exists(p) else placeholder(name)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = size / max(im.size); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        sh = im.getchannel("A").point(lambda v: int(v * 0.6)).filter(ImageFilter.GaussianBlur(max(2, size / 25)))
        if len(D["icons"]) > 260: D["icons"].clear()
        D["icons"][key] = (im, sh)
    return D["icons"][key]

def placeholder(name):
    im = Image.new("RGBA", (300, 300)); d = ImageDraw.Draw(im); d.ellipse((10, 10, 290, 290), fill=(255, 255, 255, 230))
    d.text((30, 130), name[3:16], fill=(0, 0, 0), font=ImageFont.truetype(FONT, 26)); return im

def put_icon(can, name, size, xy, t, t0, t1=None, flip=False, bob=True):
    if t < t0 or (t1 is not None and t >= t1 + 0.2): return
    k = ease((t - t0) / 0.3, "back")
    if t1 is not None and t > t1: k *= 1 - ease((t - t1) / 0.2)
    if k <= 0.03: return
    sz = size * k if abs(k - 1) > 1e-3 else size
    im, sh = icon(name, round(sz / 4) * 4 if abs(k - 1) > 1e-3 else size, flip)
    x, y = xy
    if bob: y += 4 * math.sin(2 * math.pi * 0.7 * (t - t0))
    x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    can.paste((0, 0, 0), (x0 + int(size / 22), y0 + int(size / 14)), sh); can.paste(im, (x0, y0), im)

def text_img(s, size, fill, stroke=8, font=FONT):
    key = (s, size, fill, stroke, font)
    if key not in D["texts"]:
        f = ImageFont.truetype(font, size); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lines = s.split("\n"); bbs = [d.textbbox((0, 0), l, font=f, stroke_width=stroke) for l in lines]
        lw = max(b[2] - b[0] for b in bbs); lh = int(size * 1.15)
        im = Image.new("RGBA", (lw + 8, lh * len(lines) + 8)); dd = ImageDraw.Draw(im)
        for i, (l, b) in enumerate(zip(lines, bbs)):
            dd.text((4 + (lw - (b[2] - b[0])) / 2 - b[0], 4 + i * lh - b[1]), l, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        if len(D["texts"]) > 400: D["texts"].clear()
        D["texts"][key] = im
    return D["texts"][key]

def put_text(can, s, size, fill, cx, cy, t, t0, stroke=8, pop=True, t1=None, font=FONT):
    if t < t0 or (t1 is not None and t > t1): return
    im = text_img(s, size, C(fill), stroke, font)
    if pop and t - t0 < 0.22:
        k = max(0.05, ease((t - t0) / 0.22, "back")); im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
    can.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def wrap(s, font, width):
    words = s.split(); lines = []; cur = ""
    for w in words:
        if cur and font.getlength(cur + " " + w) > width: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return lines + [cur]

def card_img(s, col, width=520, size=40):
    key = ("card", s, col, width, size)
    if key not in D["texts"]:
        f = ImageFont.truetype(FONT, size); lines = wrap(s, f, width - 60); lh = int(size * 1.2)
        h = lh * len(lines) + 50; im = Image.new("RGBA", (width + 16, h + 16)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((8, 12, width + 8, h + 12), 22, fill=(0, 0, 0, 120))
        d.rounded_rectangle((4, 4, width + 4, h + 4), 22, fill=(14, 20, 34, 238), outline=C(col), width=5)
        for i, l in enumerate(lines):
            tw = f.getlength(l); d.text((4 + (width - tw) / 2, 28 + i * lh), l, font=f, fill=(255, 255, 255))
        D["texts"][key] = im
    return D["texts"][key]

def put_card(can, s, xy, col, t, t0, width=520, size=40, t1=None):
    if t < t0 or (t1 is not None and t > t1 + 0.2): return
    im = card_img(s, col, width, size); k = ease((t - t0) / 0.28, "back")
    if t1 is not None and t > t1: k *= 1 - ease((t - t1) / 0.2)
    if k < 0.03: return
    if abs(k - 1) > 1e-3: im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
    can.paste(im, (int(xy[0] - im.width / 2), int(xy[1] - im.height / 2)), im)

# ---------------- titulares y subtítulos ----------------
def headline(can, t, sid):
    s = G[sid]["headline"]; t0 = SC[sid][0]; size = 84
    while ImageFont.truetype(FONT, size).getlength(s) > 1400: size -= 6
    put_text(can, s, size, "YEL", W / 2, 84, t, t0, stroke=10, pop=t0 > 0)

def build_subs():
    groups = []; cur = []
    for w in WORDS:
        txt = w["w"].replace("’", "'").upper()
        if cur and (cur[-1]["scene"] != w["scene"] or len(cur) >= 4 or len(" ".join(c["txt"] for c in cur)) + len(txt) > 24 or cur[-1]["w"].endswith((".", "?", ":", ","))):
            groups.append(cur); cur = []
        cur.append(dict(w, txt=txt))
    groups.append(cur); out = []
    for i, g in enumerate(groups):
        end = groups[i + 1][0]["s"] if i + 1 < len(groups) else TOTAL
        out.append((g[0]["s"], max(min(end, SC[g[0]["scene"]][1]), g[-1]["e"] + 0.2), g))
    return out

def subtitle(can, t):
    for s0, s1, g in D["subs"]:
        if s0 <= t < s1: break
    else: return
    hi = max([i for i, w in enumerate(g) if w["s"] <= t + 0.02] or [0])
    key = ("sub", tuple(w["txt"] for w in g), hi)
    if key not in D["texts"]:
        f = ImageFont.truetype(FONT, 58); sp = f.getlength(" ")
        ws = [f.getlength(w["txt"]) for w in g]; tw = int(sum(ws) + sp * (len(g) - 1)) + 30
        im = Image.new("RGBA", (tw, 104)); d = ImageDraw.Draw(im); x = 15
        for i, w in enumerate(g):
            d.text((x, 12), w["txt"], font=f, fill=COL["YEL"] if i == hi else COL["WHITE"], stroke_width=9, stroke_fill=(0, 0, 0)); x += ws[i] + sp
        D["texts"][key] = im
    im = D["texts"][key]; can.paste(im, (int(W / 2 - im.width / 2), int(H - 112 - im.height / 2)), im)

# ---------------- neón ----------------
def path_px(v, ll, n=40):
    pts = [v.P(*place(p)) for p in ll]; out = []
    for a, b in zip(pts, pts[1:]):
        for i in range(n // len(pts) + 2): u = i / (n // len(pts) + 2); out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
    return out + [pts[-1]]
def partial(pts, frac):
    if frac >= 0.999: return pts
    return pts[:max(2, int(frac * len(pts)))]
def arrowline(n, pts, frac, col, w=10, head=True):
    if frac <= 0: return
    p = partial(pts, frac)
    if len(p) < 2: return
    n.line(p, col, w)
    if head:
        (ax, ay), (bx, by) = p[-2], p[-1]; ang = math.atan2(by - ay, bx - ax); L = w * 3.0
        n.line([(bx + math.cos(ang + 2.5) * L, by + math.sin(ang + 2.5) * L), (bx, by), (bx + math.cos(ang - 2.5) * L, by + math.sin(ang - 2.5) * L)], col, w)
def curve(p0, p1, bend=0.2, n=40):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; dx, dy = p1[0] - p0[0], p1[1] - p0[1]; c = (mx - dy * bend, my + dx * bend)
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]) for u in [i / n for i in range(n + 1)]]
def ring(n, xy, t, t0, col, r0=14, r1=120, period=1.3):
    if t < t0: return
    for j in range(3):
        u = ((t - t0) / period + j / 3) % 1.0; r = lerp(r0, r1, u)
        n.line([(xy[0] + math.cos(a / 30 * 2 * math.pi) * r, xy[1] + math.sin(a / 30 * 2 * math.pi) * r * 0.8) for a in range(31)], col, 4, k=1 - u)

def hatch_mask():
    if "hatch" not in D:
        hm = Image.new("L", (W, H)); hd = ImageDraw.Draw(hm)
        for x in range(-H, W, 30): hd.line([(x, H), (x + H, 0)], fill=255, width=10)
        D["hatch"] = hm
    return D["hatch"]

# ---------------- 3D ----------------
def frame3d(shot, i):
    d = os.path.join(R3, shot); p = os.path.join(d, f"f_{max(1, i):04d}.png")
    if not os.path.exists(p):
        fs = sorted(f for f in os.listdir(d) if f.startswith("f_")) if os.path.isdir(d) else []
        if not fs: return Image.new("RGB", (W, H), (20, 25, 35))
        p = os.path.join(d, fs[min(len(fs) - 1, max(0, i - 1))])
    im = Image.open(p).convert("RGB")
    if im.size != (W, H): im = im.resize((W, H), Image.BILINEAR)
    small = im.resize((W // 2, H // 2), Image.BILINEAR); hi = small.point(lambda v: max(0, v - 170) * 3)
    g = ImageChops.add(hi.filter(ImageFilter.GaussianBlur(10)), hi.filter(ImageFilter.GaussianBlur(3))).resize((W, H), Image.BILINEAR)
    return ImageChops.multiply(ImageChops.add(im, g), M.G["vig"].point(lambda v: min(255, v + 50)))

# ---------------- render de una escena ----------------
def T(sid, at): return wt(sid, at)
def pos(v, p):
    if isinstance(p, list): return tuple(p)
    return v.P(*place(p))

def scene_view(S, sid, t):
    v = V(S.get("view", "levant"))
    if "view2" in S:
        a0 = T(sid, S.get("move", None)); k = ramp(t, a0, a0 + S.get("movedur", 1.6))
        v = lerpv(v, V(S["view2"]), k)
    return v

def background(S, sid, t, v):
    """mapa con rellenos estáticos (cacheado si la vista no se mueve)."""
    fills = [f for f in S.get("fill", []) if t >= T(sid, f[3] if len(f) > 3 else None)]
    moving = "view2" in S and SC[sid][0] <= t <= T(sid, S.get("move")) + S.get("movedur", 1.6)
    key = (sid, tuple(f[0] for f in fills), round(v.wdeg, 3) if moving else 0, round(v.lon, 3) if moving else 0)
    if key in D["bgs"]: return D["bgs"][key].copy(), D["bgs"][key + ("n",)]
    ms = [(rmask(v, f[0]), C(f[1]), f[2]) for f in fills]
    can, n = M.render(v, ms)
    for f in fills:
        if len(f) > 4 and f[4] == "hatch":
            can = Image.composite(Image.new("RGB", (W, H), C(f[1])), can, ImageChops.multiply(rmask(v, f[0]), hatch_mask()).point(lambda x: int(x * 0.5)))
    edges = [(rmask(v, f[0]), C(f[1]), 0.9) for f in fills if f[2] > 0.12]
    if S.get("bg") == "dim":
        can = Image.blend(can.filter(ImageFilter.GaussianBlur(6)), Image.new("RGB", (W, H), (8, 12, 22)), 0.55); edges = []
    if not moving:
        if len(D["bgs"]) > 30: D["bgs"].clear()
        D["bgs"][key] = can.copy(); D["bgs"][key + ("n",)] = edges
    return can, edges

def render_scene(sid, t):
    S = STORY.get(sid, {}); a, b = SC[sid]
    if "shot" in S:
        can = frame3d(S["shot"], int((t - a + S.get("shot_off", 0)) * FPS) + 1); v = V(S.get("view", "levant")); edges = []
    elif S.get("bg") == "card":
        v = V(S.get("view", "region")); can, edges = background(dict(S, bg="dim"), sid, t, v)
    else:
        v = scene_view(S, sid, t); can, edges = background(S, sid, t, v)
    n = Neon()
    for m, c, k in edges: n.edge(m, c, k)
    for ar in S.get("arrow", []):
        p0, p1, col, at = ar[:4]; bend = ar[4] if len(ar) > 4 else 0.15; t0 = T(sid, at)
        if t >= t0:
            pts = curve(pos(v, p0), pos(v, p1), bend) if not (isinstance(p0, list) and len(p0) > 2) else path_px(v, p0)
            arrowline(n, pts, ramp(t, t0, t0 + 0.9, "cubic"), C(col), ar[5] if len(ar) > 5 else 10)
    for sv in S.get("salvo", []):
        p0, p1, cnt, col, at = sv[:5]; icpt = sv[5] if len(sv) > 5 else 0.0; t0 = T(sid, at); rnd = random.Random(hash((sid, str(p0))) & 0xffff)
        for j in range(cnt):
            tj = t0 + j * 0.06 + rnd.random() * 0.4
            if t < tj: continue
            q0 = pos(v, p0); q1 = pos(v, p1); q0 = (q0[0] + rnd.uniform(-25, 25), q0[1] + rnd.uniform(-25, 25)); q1 = (q1[0] + rnd.uniform(-45, 45), q1[1] + rnd.uniform(-45, 45))
            pts = curve(q0, q1, rnd.uniform(0.12, 0.3), 30); u = ramp(t, tj, tj + 1.3, "cubic")
            stop = 0.55 + rnd.random() * 0.3 if rnd.random() < icpt else 1.0
            if u >= stop:
                if u < stop + 0.25: n.dot(pts[int(stop * 30)], COL["WHITE"], 6, k=1 - (u - stop) * 4)
                continue
            tail = max(0, u - 0.25); seg = pts[int(tail * 30):max(int(tail * 30) + 2, int(u * 30))]
            n.line(seg, C(col), 4)
    for d_ in S.get("dot", []):
        if t >= T(sid, d_[2]): n.dot(pos(v, d_[0]), C(d_[1]), d_[3] if len(d_) > 3 else 16)
    for p_ in S.get("pulse", []):
        ring(n, pos(v, p_[0]), t, T(sid, p_[2]), C(p_[1]))
    for ln in S.get("line", []):
        pts, col, at = ln[:3]; t0 = T(sid, at)
        if t >= t0: arrowline(n, path_px(v, pts, 60), ramp(t, t0, t0 + 1.2), C(col), ln[3] if len(ln) > 3 else 7, head=False)
    for fn in S.get("custom", []): fn(can, n, v, t, sid)
    can = n.draw(can)
    for fn in S.get("custom2", []): fn(can, v, t, sid)
    for ic in S.get("icon", []):
        name, p, size, at = ic[:4]; t1 = T(sid, ic[4]) if len(ic) > 4 and ic[4] is not None else None
        put_icon(can, name, size, pos(v, p), t, T(sid, at), t1, flip=len(ic) > 5 and ic[5])
    for lb in S.get("label", []):
        s, p, col, at = lb[:4]; xy = pos(v, p); put_text(can, s, lb[4] if len(lb) > 4 else 38, C(col), xy[0], xy[1], t, T(sid, at), stroke=7)
    for ct in S.get("count", []):
        a0, a1, fmt, p, at, dur = ct[:6]; t0 = T(sid, at)
        if t >= t0:
            k = ramp(t, t0, t0 + dur, "cubic"); val = lerp(a0, a1, k); xy = pos(v, p)
            put_text(can, fmt.format(val), ct[6] if len(ct) > 6 else 72, C(ct[7]) if len(ct) > 7 else COL["WHITE"], xy[0], xy[1], t, t0, stroke=9, pop=False)
    for cd in S.get("card", []):
        s, p, col, at = cd[:4]; t1 = T(sid, cd[5]) if len(cd) > 5 and cd[5] is not None else None
        put_card(can, s, pos(v, p), col, t, T(sid, at), cd[4] if len(cd) > 4 and cd[4] else 520, t1=t1)
    if S.get("bg") == "card": chapter_card(can, sid, t)
    if "shot" in S: put_text(can, "ANIMATED RECONSTRUCTION", 24, (215, 215, 215), 230, H - 36, t, a, stroke=5, pop=False)
    return can

def chapter_card(can, sid, t):
    ch = G[sid]["chapter"]; a = SC[sid][0]; num, _, title = ch.partition(". ")
    put_text(can, "CHAPTER " + num, 54, "LBLUE", W / 2, 400, t, a, stroke=8)
    put_text(can, title, 110, "WHITE", W / 2, 520, t, a + 0.25, stroke=11)
    chs = []
    for s in ORDER:
        c = G[s]["chapter"]
        if c != "HOOK" and c not in chs: chs.append(c)
    i = chs.index(ch); d = ImageDraw.Draw(can)
    for j in range(len(chs)):
        x = W / 2 + (j - (len(chs) - 1) / 2) * 70; r = 14 if j == i else 9
        d.ellipse((x - r, 660 - r, x + r, 660 + r), fill=COL["YEL"] if j <= i else (90, 100, 120))

# ---------------- post: temblores y destellos ----------------
SHAKES, FLASHES = [], []
def post(can, t):
    dx = dy = 0
    for t0, amp in SHAKES:
        if t0 <= t < t0 + 0.5:
            k = 1 - (t - t0) / 0.5; dx += int(amp * k * math.sin(t * 90)); dy += int(amp * k * math.cos(t * 77))
    if dx or dy: can = ImageChops.offset(can, dx, dy)
    for t0, dur, a in FLASHES:
        if t0 <= t < t0 + dur: can = Image.blend(can, Image.new("RGB", (W, H), (255, 245, 230)), a * (1 - (t - t0) / dur))
    return can

def frame(t):
    init(); sid = ORDER[0]
    for s in ORDER:
        if t >= SC[s][0]: sid = s
    can = render_scene(sid, t)
    if STORY.get(sid, {}).get("bg") != "card": headline(can, t, sid)
    subtitle(can, t)
    return post(can, t)

# ---------------- SFX automáticos ----------------
SFX = []
def plan_fx():
    for sid in ORDER:
        S = STORY.get(sid, {})
        for ic in S.get("icon", []): SFX.append({"t": round(T(sid, ic[3]), 3), "type": "pop", "vol": 0.5})
        for ar in S.get("arrow", []): SFX.append({"t": round(T(sid, ar[3]), 3), "type": "creak", "vol": 0.05})
        for sv in S.get("salvo", []):
            t0 = T(sid, sv[4]); SFX.append({"t": round(t0, 3), "type": "mg", "vol": 0.04})
        for cd in S.get("card", []): SFX.append({"t": round(T(sid, cd[3]), 3), "type": "click", "vol": 0.15})
        for ct in S.get("count", []): SFX.append({"t": round(T(sid, ct[4]), 3), "type": "click", "vol": 0.2})
        for f in S.get("fx", []):
            at, kind = f[0], f[1]; t0 = T(sid, at)
            if kind == "shake": SHAKES.append((t0, f[2] if len(f) > 2 else 10))
            elif kind == "flash": FLASHES.append((t0, 0.2, f[2] if len(f) > 2 else 0.5))
            else: SFX.append({"t": round(t0, 3), "type": kind, "vol": f[2] if len(f) > 2 else 0.25})

# ---------------- render ----------------
STORY = {}
def seg(args):
    i, f0, f1, out = args
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait(); return out

def sheet(ids, out, per=1):
    """hoja de miniaturas: un cuadro (o `per`) a mitad de cada escena para revisar barato."""
    init(); ims = []
    for sid in ids:
        a, b = SC[sid]
        for j in range(per):
            t = a + (b - a) * (0.75 if per == 1 else (j + 1) / (per + 1)); im = frame(t).resize((480, 270), Image.BILINEAR)
            ImageDraw.Draw(im).text((6, 4), sid, fill=(255, 255, 0), font=ImageFont.truetype(FONT, 22), stroke_width=3, stroke_fill=(0, 0, 0)); ims.append(im)
    cols = 4; rows = math.ceil(len(ims) / cols); s = Image.new("RGB", (cols * 480, rows * 270))
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * 480, (i // cols) * 270))
    s.save(out, quality=78)

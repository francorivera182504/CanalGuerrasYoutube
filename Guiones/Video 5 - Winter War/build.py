"""Video 5 — The Winter War: How Finland Survived Stalin (1920x1080, estilo casi todo animado).
Requiere OpenReel abierto con Scripts/abrir_openreel_local.bat y `python -m http.server 8777 --bind 127.0.0.1` en la raíz.
Uso: python build.py [--prep]   (--prep solo compone capas + sfx, sin OpenReel)"""
import json, os, sys, math, subprocess, urllib.parse
ROOT = r"E:\Historias TIK\WarMap Stick"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
import short_anim
short_anim.W, short_anim.H = 1920, 1080
from short_anim import cutout, place, Anim
W, H = 1920, 1080
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mapa_fi as M

CAP = os.path.join(ROOT, "Imagenes", "Video5", "capas")
COMP = os.path.join(ROOT, "Imagenes", "Video5", "comp")
os.makedirs(COMP, exist_ok=True)
tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
T = {s["id"]: s["start"] for s in tl["timeline"]}
TOTAL = tl["total"]; WORDS = tl["words"]
IDS = sorted(T)
END = {sid: (T[IDS[i + 1]] if i + 1 < len(IDS) else TOTAL + 1.0) for i, sid in enumerate(IDS)}

def clean(w): return w.strip(".,'’?:;!\"").lower()
def wt(word, sid, n=1):
    """Inicio de la n-ésima aparición de `word` dentro de la escena sid."""
    k = 0
    for w in WORDS:
        if w["scene"] == sid and word.lower() in clean(w["w"]).split("-") + [clean(w["w"])]:
            k += 1
            if k == n: return w["s"]
    raise KeyError(f"{word} en {sid}")

SFX = []
def sfx(t, typ, **kw): SFX.append({"t": round(t, 3), "type": typ, **kw})

# ---------------- colores e iconos propios ----------------
RED = (214, 56, 50, 255); BLUE = (40, 90, 200, 255); YEL = (255, 210, 63, 255); BLK = (0, 0, 0, 255); WHT = (255, 255, 255, 255)
GREY = (120, 120, 120, 255)

def chaikin(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(0.75*x0+0.25*x1, 0.75*y0+0.25*y1), (0.25*x0+0.75*x1, 0.25*y0+0.75*y1)]
        pts = out + [pts[-1]]
    return pts

def route_frames(name, pts, fracs=(0.25, 0.5, 0.75, 1.0), col=RED, w=18, head=True):
    pts = chaikin(pts); outs = []
    for k, frac in enumerate(fracs, 1):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        seg = pts[: max(2, int(len(pts) * frac))]
        d.line(seg, fill=BLK, width=w + 9, joint="curve"); d.line(seg, fill=col, width=w, joint="curve")
        if head and frac == 1.0:
            q, p = seg[-1], seg[-4]; ang = math.atan2(q[1]-p[1], q[0]-p[0]); L = 54
            tip = (q[0] + math.cos(ang)*14, q[1] + math.sin(ang)*14)
            d.polygon([tip, (tip[0]-L*math.cos(ang-.5), tip[1]-L*math.sin(ang-.5)), (tip[0]-L*math.cos(ang+.5), tip[1]-L*math.sin(ang+.5))], fill=col, outline=BLK, width=5)
        f = os.path.join(COMP, f"{name}_{k}.png"); im.save(f); outs.append(f)
    return outs

def dash_line(name, pts, col=RED, w=12, dash=26):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); pts = chaikin(pts); acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); s = 0.0
        while s < L:
            e = min(L, s + 4)
            if int((acc + s) // dash) % 2 == 0:
                d.line([(a[0]+(b[0]-a[0])*s/L, a[1]+(b[1]-a[1])*s/L), (a[0]+(b[0]-a[0])*e/L, a[1]+(b[1]-a[1])*e/L)], fill=col, width=w)
            s = e
        acc += L
    f = os.path.join(COMP, f"{name}.png"); im.save(f); return f

def icon(kind, size=240, col=None):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); s = size
    if kind == "ring":
        d.ellipse([12, 12, s-12, s-12], outline=BLK, width=22); d.ellipse([12, 12, s-12, s-12], outline=col or YEL, width=13)
    elif kind == "x":
        for p0, p1 in [((s*.18, s*.18), (s*.82, s*.82)), ((s*.82, s*.18), (s*.18, s*.82))]:
            d.line([p0, p1], fill=BLK, width=int(s*.2)); d.line([p0, p1], fill=RED, width=int(s*.13))
    elif kind == "check":
        pts = [(s*.15, s*.55), (s*.4, s*.8), (s*.85, s*.22)]
        d.line(pts, fill=BLK, width=int(s*.2), joint="curve"); d.line(pts, fill=(60, 170, 70, 255), width=int(s*.12), joint="curve")
    elif kind == "dot":
        d.ellipse([s*.2, s*.2, s*.8, s*.8], fill=col or BLK, outline=WHT, width=int(s*.08))
    elif kind == "stamp":
        d.rounded_rectangle([8, s*.3, s-8, s*.7], radius=18, outline=RED, width=16)
    elif kind == "bar":  # barra de munición (rect)
        d.rectangle([4, 4, s-4, s-4], fill=col or YEL, outline=BLK, width=8)
    return im

def molotov():
    """Botella con mecha encendida (dibujada; el generador la rechazó)."""
    im = Image.new("RGBA", (300, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([70, 220, 230, 500], radius=40, fill=(120, 170, 110, 255), outline=BLK, width=8)
    d.rectangle([120, 120, 180, 230], fill=(120, 170, 110, 255), outline=BLK, width=8)
    d.rectangle([90, 330, 210, 420], fill=(200, 190, 150, 255), outline=BLK, width=6)
    d.polygon([(135, 125), (165, 125), (175, 70), (125, 80)], fill=(235, 225, 200, 255), outline=BLK)
    try:
        f = cutout(os.path.join(CAP, "el_fire.png")).resize((150, 170)); im.alpha_composite(f, (75, 0))
    except Exception: pass
    return im

# ---------------- capas ----------------
EL = {}
def el(name):
    if name not in EL:
        EL[name] = molotov() if name == "molotov" else cutout(os.path.join(CAP, f"el_{name}.png"))
    return EL[name]
LAYERS = []; LABELS = []
def layer(tag, img, cx, cy, width, start, end, z=5, flip=False, rotate=0):
    f = os.path.join(COMP, f"{tag}.png"); place(img, cx, cy, width, f, flip=flip, rotate=rotate)
    an = Anim(cx, cy); LAYERS.append([start, end, f, an, z]); return an
def full(path, start, end, z=5, c=(W/2, H/2)):
    an = Anim(*c); LAYERS.append([start, end, path, an, z]); return an
def label(txt, s, e, x, y, size=44, col="#1A1A1A", stroke=7, scol="#FFFFFF"):
    LABELS.append((s, e, txt, x, y, size, col, stroke, scol))

def pop(tag, name, cx, cy, w, t, end, z=6, flip=False, s=1.0, snd=True, rotate=0):
    an = layer(tag, el(name) if isinstance(name, str) else name, cx, cy, w, t, end, z, flip=flip, rotate=rotate)
    an.pop_in(0, s=s)
    if snd: sfx(t, "pop")
    return an

def smoke_puffs(tag, cx, cy, t0, t1, every=0.8, w=150, rise=220, z=3):
    t = t0; i = 0
    while t < t1 - 0.4:
        d = min(2.2, t1 - t); an = layer(f"{tag}_{i}", el("smoke"), cx + (i % 3 - 1) * 14, cy, w, t, t + d, z)
        an.scale(0, 0.45); an.scale(d, 1.35); an.op(0, 0.0); an.op(0.25, 0.85); an.op(d, 0.0)
        an.pos(0, 0, 0); an.pos(d, (16 if i % 2 else -16), -rise); t += every; i += 1

def boom_at(tag, cx, cy, t, w=260, z=9, vol=0.28, kind="explosion"):
    an = layer(tag, el(kind), cx, cy, w, t, t + 0.6, z)
    an.scale(0, 0.1, ez="easeOutBack"); an.scale(0.18, 1.2, ez="easeOutBack"); an.scale(0.6, 0.0, ez="easeInBack"); an.rot(0, -10); an.rot(0.6, 15)
    sfx(t, "boom", vol=vol)

def flash(tag, cx, cy, t, w=70, z=9):
    an = layer(tag, el("flash"), cx, cy, w, t, t + 0.18, z); an.scale(0, 0.3); an.scale(0.06, 1.1); an.scale(0.18, 0.2)

def drive(tag, name, width, cx, cy, start, end, dx, z=6, flip=False, bob=0):
    an = layer(tag, el(name), cx + dx / 2, cy, width, start, end, z, flip=flip)  # se coloca en el punto medio (dentro del cuadro)
    an.move(0, end - start, (-dx / 2, 0), (dx / 2, 0), ez="linear")
    return an

def arrow_draw(frames, t0, t1, z=7, step=0.12):
    for k, f in enumerate(frames, 1):
        s = t0 + (k - 1) * step; e = t0 + k * step if k < len(frames) else t1
        full(f, s, e, z)
    sfx(t0, "whoosh_one")

BG = {}; BGK = {}
def bg_cover(name, out=None):
    """Fondo de Codex (3:2) recortado a 16:9 cubriendo el cuadro."""
    out = out or os.path.join(COMP, f"{name}.png")
    im = Image.open(os.path.join(CAP, f"{name}.png")).convert("RGB"); r = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * r + 0.5), int(im.height * r + 0.5)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im.crop((x0, y0, x0 + W, y0 + H)).save(out); return out
def shake_bg(sid, times, amp=16):
    a = BGK.setdefault(sid, Anim(W / 2, H / 2)); a.pos(0, 0, 0)
    for t in times: a.shake(t - T[sid], d=0.45, amp=amp)

# ---------------- mapas ----------------
VN, VI = M.View("north"), M.View("isthmus")
MAPN = os.path.join(COMP, "map_north.png"); VN.base(MAPN)
MAPN_SU = os.path.join(COMP, "map_north_su.png"); VN.base(MAPN_SU, fin_color=M.SU)
MAPI = os.path.join(COMP, "map_isthmus.png"); VI.base(MAPI)
CEDED_N = os.path.join(COMP, "ceded_north.png"); VN.overlay(M.CEDED_S, (214, 56, 50, 190), CEDED_N, outline=BLK, lw=4)
CEDED_N2 = os.path.join(COMP, "ceded_north2.png"); VN.overlay(M.CEDED_SALLA, (214, 56, 50, 190), CEDED_N2, outline=BLK, lw=4)
CEDED_I = os.path.join(COMP, "ceded_isthmus.png"); VI.overlay(M.CEDED_S, (214, 56, 50, 170), CEDED_I, outline=BLK, lw=5)
WHITE = os.path.join(COMP, "white.png"); Image.new("RGB", (W, H), "white").save(WHITE)
PN, PI = VN.P, VI.P
def city(tag, V, name, t, end, txt=None, dy=-46, col=BLK, size=44):
    x, y = V(*M.CITY[name]); an = layer(tag, icon("dot", 60, col), x, y, 34, t, end, 8); an.pop_in(0)
    label(txt or name, t, end, x / W, (y + dy) / H, size)
    return x, y

for name in ("road", "forest", "bunkers", "border", "league", "europe", "evac"):
    BG[name] = bg_cover(f"bg_{name}")

# =====================================================================
# ESCENAS
# =====================================================================
ROAD_Y = 520   # centro de la carretera en bg_road (ajustar tras ver la imagen)

def column(sid, t0, t1, groups, speed=55, split_t=None, z=6, w_tank=170, w_truck=150):
    """Columna soviética vista desde arriba. groups = lista de listas de x iniciales; al split_t los grupos se separan."""
    n = 0
    for gi, xs in enumerate(groups):
        for x in xs:
            kind = "tank_top" if n % 3 == 0 else "truck_top"; n += 1
            an = layer(f"col{sid}_{n}", el(kind), x, ROAD_Y + (6 if n % 2 else -6), w_tank if kind == "tank_top" else w_truck, t0, t1, z)
            if split_t is None:
                an.move(0, t1 - t0, (0, 0), (speed * (t1 - t0), 0), ez="linear")
            else:
                ds = split_t - t0; mv = speed * ds
                an.pos(0, 0, 0); an.pos(ds, mv, 0)
                off = [-90, 0, 120][gi % 3]
                an.pos(ds + 0.5, mv + off, 0, "easeOutCubic"); an.pos(t1 - t0, mv + off + (40 if gi == 2 else 0), 0)
                if gi == 1: an.rot(ds, 0); an.rot(ds + 0.4, 8, "easeOutBack")
    return n

# ---- 01 HOOK: la columna partida en Raate Road ----
s = "01"; BG[s] = BG["road"]; t0, t1 = T[s], END[s]; tS = wt("shattered", s)
groups = [[180, 380, 560], [820, 1000, 1180], [1460, 1640, 1820]]
column(s, t0, t1, groups, speed=60, split_t=tS)
for i, (x, y, fl, dy) in enumerate([(700, 140, False, 260), (1300, 150, False, 250), (420, 960, False, -260), (1060, 950, False, -250)]):
    an = layer(f"ski01_{i}", el("skier_top"), x, y, 110, t0, t1, 8, rotate=0 if dy < 0 else 180)
    an.move(0, tS - t0 + 0.1, (0, 0), (0, dy * 0.75), ez="easeOutCubic"); an.pos(t1 - t0, 30, dy * 0.75)
    flash(f"fl01_{i}", x, y + dy * 0.6, t0 + 0.35 + i * 0.1)
sfx(t0 + 0.3, "mg", vol=0.12)
for i, x in enumerate([700, 1300, 980]):
    boom_at(f"b01_{i}", x, ROAD_Y, tS + i * 0.07, w=300, vol=0.3 if i == 0 else 0.2)
    boom_at(f"sn01_{i}", x + 40, ROAD_Y - 30, tS + 0.05 + i * 0.07, w=260, kind="snowburst", vol=0.05)
shake_bg(s, [tS], amp=20)
for i, x in enumerate([1000, 1180]): smoke_puffs(f"sm01_{i}", x, ROAD_Y - 20, tS + 0.4, t1, every=0.7)
label("RAATE ROAD · JAN 1940", tS + 1.2, t1, 0.5, 0.80, 52, "#FFFFFF", 9, "#000000")

# ---- 02 ¿por qué cedió territorio? ----
s = "02"; BG[s] = MAPN; t0, t1 = T[s], END[s]; tL = wt("land", s)
fa = full(CEDED_N, tL - 0.4, t1, 6); fa.op(0, 0); fa.op(0.4, 1)
fb = full(CEDED_N2, tL - 0.4, t1, 6); fb.op(0, 0); fb.op(0.4, 1); sfx(tL - 0.4, "boom", vol=0.15)
fx, fy = PN(26.0, 63.0); f = pop("flag02", "flag_fi", fx, fy - 40, 170, t0 + 0.1, t1, 7); f.bob(0.4, t1 - t0, amp=6, period=1.2)
pop("q02", "question", 1100, 560, 220, tL, t1, 8)

# ---- 03 población ----
s = "03"; BG[s] = MAPN; t0, t1 = T[s], END[s]
x, y = PN(26.0, 63.0); pop("fi03", "flag_fi", x, y, 150, t0 + 0.2, t1, 7)
x2, y2 = PN(45.0, 62.5); pop("su03", "flag_su", x2, y2, 380, wt("soviet", s), t1, 7)
label("3.7 MILLION", wt("three", s), t1, x / W, (y + 120) / H, 56, "#1A3C8C")
label("170 MILLION", wt("forty", s), t1, x2 / W, (y2 + 250) / H, 76, "#B3261E")
sc = pop("sc03", "scale", 960, 860, 300, t0 + 0.2, t1, 8); sc.rot(wt("forty", s) - t0, 0); sc.rot(wt("forty", s) - t0 + 0.5, 16, "easeOutBack")
sfx(wt("forty", s), "boom", vol=0.12)

# ---- 04 independencia 1917 ----
s = "04"; t0, t1 = T[s], END[s]; tI = wt("independence", s); BG[s] = MAPN_SU
nb = full(MAPN, tI - 0.1, t1, 2); nb.op(0, 0); nb.op(0.35, 1); sfx(tI, "boom", vol=0.14)
x, y = PN(26.0, 63.0); f = pop("fi04", "flag_fi", x, y, 190, tI + 0.2, t1, 7); f.bob(0.6, t1 - t0 - (tI - t0) - 0.2, amp=7, period=1.2)
label("RUSSIAN EMPIRE", t0 + 0.3, tI, 0.62, 0.45, 60, "#B3261E")
label("1917", tI, t1, x / W, (y + 120) / H, 70, "#1A3C8C")

# ---- 05 Leningrado 32 km ----
s = "05"; BG[s] = MAPI; t0, t1 = T[s], END[s]
lx, ly = city("c05a", PI, "LENINGRAD", t0 + 0.2, t1, dy=50)
bx, by = PI(29.95, 60.19)
arrow_draw(route_frames("ruler05", [(lx, ly), ((lx + bx) / 2 - 10, (ly + by) / 2), (bx, by)], col=YEL, head=False), wt("thirty-two", s) - 0.2, t1)
label("32 KM", wt("thirty-two", s), t1, (lx + bx) / 2 / W - 0.06, (ly + by) / 2 / H, 60, "#1A1A1A")
ld = pop("ld05", "leader", 1550, 640, 300, wt("moscow", s), t1, 8); ld.bob(0.4, t1 - wt("moscow", s), amp=6)
pop("ring05", icon("ring", 300), lx, ly, 180, wt("protect", s), t1, 7)

# ---- 06 pacto ----
s = "06"; BG[s] = BG["europe"]; t0, t1 = T[s], END[s]
hs = pop("hs06", "handshake", 960, 520, 420, wt("signed", s) - 0.1, t1, 8); hs.bob(0.4, t1 - t0, amp=10, period=0.6)
pp = layer("pp06", el("paper"), 960, 560, 360, wt("secret", s), t1, 9); pp.move(0, 0.5, (0, 700), (220, 0), "easeOutCubic"); pp.rot(0, 20); pp.rot(0.5, -6, "easeOutCubic")
sfx(wt("secret", s), "whoosh_one"); sfx(wt("sphere", s), "click")
label("SECRET PROTOCOL", wt("secret", s) + 0.3, t1, 0.62, 0.86, 56, "#B3261E")

# ---- 07 demandas ----
s = "07"; BG[s] = MAPN; t0, t1 = T[s], END[s]
for i, (word, lon, lat, txt) in enumerate([("land", 29.3, 60.5, "LAND"), ("gulf", 27.0, 60.05, "ISLANDS"), ("hanko", 22.95, 59.82, "HANKO BASE")]):
    tt = wt(word, s); x, y = PN(lon, lat); pop(f"r07_{i}", icon("ring", 300, RED), x, y, 130, tt, t1, 8)
    label(txt, tt, t1, x / W, (y - 90) / H, 46, "#B3261E")
pop("ld07", "leader", 1450, 600, 280, t0 + 0.2, t1, 7)

# ---- 08 rechazo ----
s = "08"; BG[s] = MAPN; t0, t1 = T[s], END[s]
x, y = PN(34.0, 63.5); pop("ex08", icon("ring", 300, (60, 170, 70, 255)), x, y, 260, t0 + 0.3, t1, 6)
label("OFFER", t0 + 0.3, t1, x / W, (y - 160) / H, 50, "#2E7D32")
fl = pop("fl08", "finleader", 560, 640, 300, wt("finland", s), t1, 8)
tr = wt("rejected", s); fl.rot(tr - t0 - 0.4, 0); fl.rot(tr - t0 - 0.2, -6); fl.rot(tr - t0, 6); fl.rot(tr - t0 + 0.2, 0)
st = layer("st08", icon("stamp", 400), 960, 540, 520, tr, t1, 9, rotate=-12); st.scale(0, 2.2); st.scale(0.18, 1.0, ez="easeOutBack"); st.op(0, 0); st.op(0.1, 1)
label("REJECTED", tr + 0.05, t1, 0.5, 0.5, 90, "#B3261E", 0)
sfx(tr, "boom", vol=0.18)

# ---- 09 Mainila ----
s = "09"; BG[s] = BG["border"]; t0, t1 = T[s], END[s]; tsh = wt("shelled", s)
for i, x in enumerate([1350, 1560, 1750]):
    boom_at(f"b09_{i}", x, 560 + 30 * (i % 2), tsh + i * 0.18, w=230, vol=0.18)
    smoke_puffs(f"sm09_{i}", x, 520, tsh + 0.3 + i * 0.18, t1, every=0.9, w=130)
shake_bg(s, [tsh], amp=10)
label("MOSCOW: \"FINLAND FIRED!\"", wt("claimed", s), wt("denied", s), 0.5, 0.2, 64, "#B3261E")
pop("q09", "question", 960, 380, 220, wt("staged", s), t1, 9)
label("STAGED?", wt("staged", s), t1, 0.5, 0.2, 80, "#1A1A1A")

# ---- 10 invasión 30-nov ----
s = "10"; BG[s] = MAPN; t0, t1 = T[s], END[s]; tc = wt("crossed", s)
for i, pts in enumerate([[(33.5, 61.0), (30.6, 60.5)], [(34.5, 62.6), (31.2, 62.8)], [(32.5, 64.8), (29.4, 64.9)], [(31.5, 66.7), (28.8, 66.8)], [(33.5, 69.0), (30.8, 69.4)]]):
    arrow_draw(route_frames(f"a10_{i}", [PN(*p) for p in pts], w=16), tc - 0.3 + i * 0.12, t1)
shake_bg(s, [tc], amp=10); sfx(tc, "boom", vol=0.2)
hx, hy = PN(*M.CITY["HELSINKI"]); tb = wt("bombers", s)
for i in range(3):
    an = layer(f"bm10_{i}", el("bomber"), 1400, 300 + i * 90, 200, tb - 0.3, t1, 9, flip=True)
    an.move(0, wt("helsinki", s) - tb + 0.6, (500, 0), (hx - 1400 + 120 + i * 60, hy - 300 - i * 90 - 120), "linear")
    an.pos(t1 - tb + 0.3, hx - 1400 - 400, hy - 300 - i * 90 - 220)
sfx(tb - 0.3, "planes", d=t1 - tb)
for i in range(3): boom_at(f"b10_{i}", hx + (i - 1) * 40, hy + (i % 2) * 20, wt("helsinki", s) + 0.15 + i * 0.15, w=150, vol=0.2)
label("NOV 30, 1939", t0 + 0.2, t1, 0.18, 0.2, 64, "#B3261E")
for i, (lo, la) in enumerate([(33.6, 61.2), (34.6, 62.8), (32.8, 64.9), (31.8, 66.8), (33.8, 69.0)]):
    x_, y_ = PN(lo, la); a_ = pop(f"tm10_{i}", "tank", x_ + 40, y_, 90, t0 + 0.3 + i * 0.25, t1, 8, snd=i % 2 == 0, flip=True)
    a_.bob(0.4, t1 - t0 - 0.5 - i * 0.25, amp=4, period=0.5)

# ---- 11 expulsión ----
s = "11"; BG[s] = BG["league"]; t0, t1 = T[s], END[s]; te = wt("expelled", s)
ch = layer("ch11", el("chair"), 960, 680, 260, t0, t1, 7); ch.pos(0, 0, 0); ch.pos(te - t0, 0, 0)
ch.pos(te - t0 + 0.6, 1300, -300, "easeInCubic"); ch.rot(te - t0, 0); ch.rot(te - t0 + 0.6, 260, "easeInCubic")
gv = pop("gv11", "gavel", 1450, 420, 260, t0 + 0.2, t1, 8)
gv.rot(te - t0 - 0.3, 0); gv.rot(te - t0 - 0.1, -35); gv.rot(te - t0, 10, "easeOutBack"); sfx(te, "click", vol=0.3); sfx(te + 0.1, "whoosh_one")
label("DEC 14, 1939", t0 + 0.2, t1, 0.18, 0.2, 60, "#1A1A1A")

# ---- 12 guerra rápida ----
s = "12"; BG[s] = WHITE; t0, t1 = T[s], END[s]
for i in range(10):
    tt = wt("tanks", s) + i * 0.06; x = 1050 + (i % 5) * 170; y = 430 + (i // 5) * 170
    pop(f"tk12_{i}", "tank", x, y, 160, tt, t1, 6, snd=i % 3 == 0)
for i in range(6):
    tt = wt("aircraft", s) + i * 0.06; x = 1050 + i * 145; pop(f"pl12_{i}", "bomber", x, 210, 150, tt, t1, 6, snd=i % 3 == 0)
for i in range(2): pop(f"sk12_{i}", "skier", 300 + i * 220, 600, 200, t0 + 0.3 + i * 0.1, t1, 6)
label("2 WEEKS?", t0 + 0.4, t1, 0.25, 0.25, 90, "#B3261E")

# ---- 13 gobierno títere ----
s = "13"; BG[s] = MAPN; t0, t1 = T[s], END[s]
x, y = city("c13", PN, "TERIJOKI", wt("terijoki", s), t1, dy=40)
pu = pop("pu13", "puppet", x + 200, y - 300, 300, wt("rival", s), t1, 8); pu.bob(0.4, t1 - t0, amp=14, period=1.0)
label("KUUSINEN", wt("kuusinen", s), t1, (x + 200) / W, (y - 90) / H, 50, "#B3261E")
hx, hy = PN(*M.CITY["HELSINKI"]); arrow_draw(route_frames("a13", [(x, y), (x - 150, y - 60), (hx + 20, hy - 20)], col=RED, w=10), wt("replace", s), t1)

# ---- 14 purgas ----
s = "14"; BG[s] = WHITE; t0, t1 = T[s], END[s]; tr = wt("removed", s)
for i in range(10):
    x = 500 + (i % 5) * 210; y = 360 + (i // 5) * 330
    an = layer(f"of14_{i}", el("sovsoldier"), x, y, 160, t0 + 0.1 + i * 0.05, t1 if i in (2, 7) else tr + 0.1 + i * 0.12, 6)
    an.pop_in(0)
    if i not in (2, 7):
        dd = tr + 0.1 + i * 0.12 - (t0 + 0.1 + i * 0.05); an.op(dd - 0.15, 1); an.op(dd, 0); sfx(tr + i * 0.12, "pop", vol=0.05)
pop("ld14", "leader", 1650, 560, 280, wt("purges", s), t1, 7)
label("1937–38", t0 + 0.2, t1, 0.15, 0.15, 64, "#1A1A1A")

# ---- 15 Línea Mannerheim ----
s = "15"; BG[s] = BG["bunkers"]; t0, t1 = T[s], END[s]
for i in range(3):
    drive(f"tk15_{i}", "tank", 260, -150 - i * 280, 900 + (i % 2) * 40, t0, t1, 650, z=6)
for i in range(4): flash(f"fl15_{i}", 1060, 390, wt("mannerheim", s) + i * 0.35, w=90)
sfx(wt("mannerheim", s), "mg", vol=0.1)
label("MANNERHEIM LINE", wt("mannerheim", s), t1, 0.5, 0.2, 70, "#1A3C8C")

# ---- 16 Kollaa + Häyhä ----
s = "16"; BG[s] = MAPN; t0, t1 = T[s], END[s]
kx, ky = city("c16", PN, "KOLLAA", t0 + 0.1, t1, dy=48)
for i in range(3):
    t = t0 + 0.3 + i * 1.0
    arrow_draw(route_frames(f"a16_{i}", [PN(34.5, 62.4 + i * 0.25), (kx + 30, ky - 10 + i * 10)], w=14), t, t + 0.9)
    pop(f"x16_{i}", icon("x", 200), kx + 30, ky, 70, t + 0.6, t + 0.95, 9)
label("\"KOLLAA HOLDS!\"", wt("holds", s), t1, 0.55, 0.42, 70, "#1A3C8C")
sn = pop("sn16", "sniper", 1500, 880, 420, wt("sniper", s), t1, 9)
for i in range(3): flash(f"fl16_{i}", 1720, 860, wt("sniper", s) + 0.6 + i * 0.7, w=90)
label("SIMO HÄYHÄ", wt("simo", s), t1, 0.78, 0.7, 56, "#1A1A1A")

# ---- 17 cortar Finlandia ----
s = "17"; BG[s] = MAPN; t0, t1 = T[s], END[s]
ox, oy = city("c17", PN, "OULU", t0 + 0.2, t1)
arrow_draw(route_frames("a17", [PN(32.5, 64.9), PN(29.5, 64.95), PN(27.4, 65.0), (ox + 40, oy)], w=22), wt("aimed", s), t1, step=0.2)
full(dash_line("cut17", [PN(30.2, 64.7), PN(27.5, 64.8), PN(24.8, 64.95)], col=RED, w=10), wt("cut", s), t1, 6)
pop("q17", "question", 1250, 450, 200, wt("half", s), t1, 9)

# ---- 18 frío ----
s = "18"; BG[s] = BG["forest"]; t0, t1 = T[s], END[s]
th = pop("th18", "thermo", 1500, 520, 280, t0 + 0.1, t1, 7)
sc = layer("sc18", el("sovcold"), 700, 720, 300, t0, t1, 6)
for i in range(int((t1 - t0) / 0.12)): sc.rot(i * 0.12, 3 if i % 2 else -3)
label("−40 °C", wt("forty", s), t1, 0.78, 0.15, 90, "#1A3C8C")

# ---- 19 solo carreteras ----
s = "19"; BG[s] = BG["road"]; t0, t1 = T[s], END[s]
column(s, t0, t1, [[-200 + i * 190 for i in range(11)]], speed=40)
label("NARROW ROADS", t0 + 0.2, t1, 0.5, 0.15, 64, "#FFFFFF", 9, "#000000")

# ---- 20 esquiadores ----
s = "20"; BG[s] = BG["forest"]; t0, t1 = T[s], END[s]
for i in range(4):
    st_ = t0 + 0.2 + i * 0.5; an = drive(f"sk20_{i}", "skier", 220, 150 + i * 60, 640 + (i % 2) * 90, st_, t1, 1500, z=7)
    an.op(0, 0); an.op(0.25, 1); an.op(t1 - st_ - 0.3, 1); an.op(t1 - st_, 0)
fs = pop("fs20", "finshoot", 300, 760, 260, wt("attacking", s), t1, 8)
for i in range(3): flash(f"fl20_{i}", 440, 730, wt("attacking", s) + 0.3 + i * 0.25, w=80)
sfx(wt("attacking", s) + 0.3, "mg", vol=0.1)

# ---- 21 motti ----
s = "21"; BG[s] = BG["road"]; t0, t1 = T[s], END[s]; tcut = wt("cut", s)
column(s, t0, t1, [[200, 390, 580], [860, 1050, 1240], [1520, 1710]], speed=30, split_t=tcut + 0.2)
for i, x in enumerate([720, 1380]): boom_at(f"b21_{i}", x, ROAD_Y, tcut + 0.15 + i * 0.1, w=240, vol=0.18)
for i, x in enumerate([420, 1080, 1700]): pop(f"r21_{i}", icon("ring", 300), x, ROAD_Y, 420, wt("pockets", s) + i * 0.1, t1, 9)
lg = pop("lg21", "logs", 960, 880, 300, wt("firewood", s) - 0.3, t1, 10)
label("MOTTI", wt("motti", s), t1, 0.5, 0.15, 90, "#FFD23F", 9, "#000000")

# ---- 22 Suomussalmi ----
s = "22"; BG[s] = MAPN; t0, t1 = T[s], END[s]
sx_, sy_ = city("c22", PN, "SUOMUSSALMI", t0 + 0.1, t1, dy=48)
arrow_draw(route_frames("a22a", [PN(31.8, 65.4), PN(30.2, 65.2), (sx_ + 20, sy_ - 10)], w=14), t0 + 0.2, t1)
pop("x22", icon("x", 200), sx_ + 60, sy_ - 50, 110, wt("defeated", s), t1, 9)
arrow_draw(route_frames("a22b", [PN(32.5, 64.7), PN(30.5, 64.8), PN(29.9, 64.85)], w=14, col=(240, 110, 60, 255)), wt("another", s), t1)
label("163RD DIVISION", wt("defeated", s), t1, (sx_ + 60) / W, (sy_ - 140) / H, 44, "#B3261E")

# ---- 23 Raate (repetición ampliada) ----
s = "23"; BG[s] = BG["road"]; t0, t1 = T[s], END[s]; tsh = wt("shattered", s); tt_ = wt("trapped", s)
column(s, t0, t1, [[120, 310, 500], [800, 990, 1180], [1480, 1670, 1860]], speed=35, split_t=tt_ + 0.2)
for i, (x, y) in enumerate([(650, 120), (1250, 130), (400, 960), (1000, 960)]):
    an = layer(f"sk23_{i}", el("skier_top"), x, y, 110, t0, t1, 8, rotate=180 if y < 500 else 0)
    an.move(0, tt_ - t0, (0, 0), (0, 200 if y < 500 else -200), "easeOutCubic")
for i, x in enumerate([680, 1320]): boom_at(f"b23_{i}", x, ROAD_Y, tt_ + 0.2 + i * 0.1, w=280)
for i, x in enumerate([300, 1000, 1650]): boom_at(f"c23_{i}", x, ROAD_Y + 20, tsh + i * 0.1, w=320, vol=0.25)
shake_bg(s, [tt_ + 0.2, tsh], amp=18)
for i, x in enumerate([1000, 1600]): smoke_puffs(f"sm23_{i}", x, ROAD_Y - 20, tsh + 0.4, t1, every=0.8)
label("44TH DIVISION", t0 + 0.3, t1, 0.5, 0.86, 56, "#FFFFFF", 9, "#000000")

# ---- 24 botín ----
s = "24"; BG[s] = WHITE; t0, t1 = T[s], END[s]
for i, (w_, name) in enumerate([("tanks", "tank"), ("guns", "cannon"), ("trucks", "truck")]):
    tt = wt(w_, s); x = 420 + i * 540; pop(f"lo24_{i}", name, x, 420, 360, tt, t1, 7)
    pop(f"ck24_{i}", icon("check", 200), x + 150, 300, 110, tt + 0.25, t1, 8, snd=False)
sc = layer("sc24", el("sovcold"), 960, 800, 240, wt("soviet", s), t1, 7); sc.pop_in(0)
for i in range(int((t1 - wt("soviet", s)) / 0.12)): sc.rot(0.35 + i * 0.12, 3 if i % 2 else -3)
label("CAPTURED", t0 + 0.3, t1, 0.5, 0.12, 70, "#2E7D32")

# ---- 25 el frente principal ----
s = "25"; BG[s] = MAPN; t0, t1 = T[s], END[s]
ix, iy = PN(30.4, 60.5)
for i in range(8):
    pop(f"tk25_{i}", "tank", ix + 120 + (i % 4) * 75, iy + 40 + (i // 4) * 55 - 60, 90, wt("main", s) + i * 0.06, t1, 8, snd=i % 3 == 0)
arrow_draw(route_frames("a25", [PN(33.0, 59.8), PN(31.0, 60.2), PN(29.4, 60.55)], w=26), wt("army", s), t1, step=0.15)
label("THE MAIN FRONT", t0 + 0.2, t1, 0.62, 0.62, 60, "#B3261E")

# ---- 26 Molotov ----
s = "26"; BG[s] = BG["forest"]; t0, t1 = T[s], END[s]; tb = wt("bombs", s)
bm = layer("bm26", el("bomber"), 960, 200, 360, t0, wt("incendiary", s), 8)
bm.move(0, wt("incendiary", s) - t0, (-1300, 0), (1300, 0), "linear"); sfx(t0, "planes", d=wt("incendiary", s) - t0)
for i in range(3):
    tt = tb + i * 0.35; an = layer(f"bo26_{i}", el("bomb"), 700 + i * 220, 260, 60, tt, tt + 1.0, 7)
    an.move(0, 0.9, (0, 0), (0, 520), "easeInQuad"); boom_at(f"b26_{i}", 700 + i * 220, 790, tt + 0.9, w=220, vol=0.18)
label("\"MOLOTOV'S BREAD BASKETS\"", wt("bread", s), wt("incendiary", s), 0.5, 0.12, 60, "#B3261E")
tm = wt("incendiary", s); tk = drive("tk26", "tank", 380, 1400, 790, tm, t1, -120, z=6, flip=True)
mo = layer("mo26", el("molotov"), 260, 760, 90, tm, tm + 1.0, 9); mo.pos(0, 0, 0); mo.pos(0.5, 520, -330, "easeOutQuad"); mo.pos(1.0, 1100, 20, "easeInQuad"); mo.spin(0, 1.0, 0, 540)
fi = layer("fi26", el("fire"), 1340, 700, 200, tm + 1.0, t1, 9); fi.flicker(0, t1 - tm - 1.0)
sfx(tm + 1.0, "boom", vol=0.15); sfx(tm + 1.0, "fire", d=t1 - tm - 1.0)
label("MOLOTOV COCKTAIL", tm + 1.0, t1, 0.5, 0.12, 70, "#FFD23F", 9, "#000000")

# ---- 27 Stalin se adapta ----
s = "27"; BG[s] = MAPI; t0, t1 = T[s], END[s]
pop("ld27", "leader", 1650, 640, 300, t0 + 0.1, t1, 9)
label("TIMOSHENKO", wt("timoshenko", s), t1, 0.86, 0.3, 54, "#B3261E")
for i in range(12):
    x = 1150 + (i % 4) * 90; y = 780 + (i // 4) * 70
    pop(f"cn27_{i}", "cannon" if i < 4 else "tank", x - 200, y - 120, 100, wt("concentrated", s) + i * 0.05, t1, 8, snd=i % 4 == 0)
arrow_draw(route_frames("a27", [PI(30.9, 59.95), PI(30.2, 60.25), PI(29.4, 60.5)], w=34), wt("isthmus", s), t1)

# ---- 28 febrero 1940 ----
s = "28"; BG[s] = BG["bunkers"]; t0, t1 = T[s], END[s]; ta = wt("artillery", s)
bt = []
for i in range(9):
    t = ta + 0.1 + i * 0.45; x = 700 + (i * 137) % 700; boom_at(f"b28_{i}", x, 380 + (i % 3) * 70, t, w=220, vol=0.2); bt.append(t)
shake_bg(s, bt[::2], amp=12)
for i in range(3): drive(f"tk28_{i}", "tank", 230, -200 - i * 300, 930, wt("tanks", s), t1, 900, z=7)
for i in range(4): drive(f"so28_{i}", "sovsoldier", 120, -100 - i * 200, 900, wt("infantry", s), t1, 800, z=7)
smoke_puffs("sm28", 980, 360, ta + 0.6, t1, every=0.6)

# ---- 29 la línea se rompe ----
s = "29"; BG[s] = MAPI; t0, t1 = T[s], END[s]
LINE = [PI(28.75, 60.33), PI(29.3, 60.47), PI(29.8, 60.62), PI(30.35, 60.82)]
ml = full(dash_line("ml29", LINE, col=BLUE, w=16, dash=30), t0, t1, 6)
sx2, sy2 = city("c29", PI, "SUMMA", t0 + 0.2, t1, dy=-50)
tbk = wt("broke", s)
arrow_draw(route_frames("a29", [PI(29.5, 60.05), (sx2, sy2 + 60), (sx2 - 40, sy2 - 160)], w=30), tbk - 0.2, t1)
boom_at("b29", sx2, sy2, tbk, w=200); shake_bg(s, [tbk], amp=10)
vx, vy = city("c29b", PI, "VIIPURI", wt("viipuri", s) - 0.5, t1)
arrow_draw(route_frames("a29b", [(sx2 + 80, sy2 - 40), (vx + 60, vy + 40)], col=BLUE, w=18), wt("back", s), t1)
label("MANNERHEIM LINE", t0 + 0.1, tbk, 0.3, 0.75, 50, "#1A3C8C")

# ---- 30 sin recursos ----
s = "30"; BG[s] = WHITE; t0, t1 = T[s], END[s]
cr = pop("cr30", "crate", 500, 560, 380, t0 + 0.1, t1, 7)
bar = layer("bar30", icon("bar", 200, YEL), 500, 860, 400, t0 + 0.2, t1, 7); bar.scale(0, 1.0, 0.15); bar.scale(wt("ammunition", s) - t0 + 0.6, 0.05, 0.15, "easeInCubic")
sh = layer("sh30", el("ship"), 1250, 640, 380, wt("britain", s), t1, 6); sh.move(0, t1 - wt("britain", s), (0, 0), (220, 0), "linear"); sh.bob(0, t1 - wt("britain", s), amp=6, dx=0)
pop("x30", icon("x", 200), 1350, 600, 260, wt("never", s), t1, 9)
label("NEVER ARRIVED", wt("never", s), t1, 0.7, 0.25, 64, "#B3261E")

# ---- 31 tratado ----
s = "31"; BG[s] = WHITE; t0, t1 = T[s], END[s]
pn = pop("pn31", "pen", 960, 520, 520, t0 + 0.1, t1, 7)
for i in range(6): pn.pos(0.4 + i * 0.3, (-30 if i % 2 else 30), (8 if i % 2 else -8))
sfx(t0 + 0.4, "creak", vol=0.05)
label("MOSCOW PEACE TREATY", t0 + 0.2, t1, 0.5, 0.12, 64, "#1A1A1A")
label("105 DAYS", wt("hundred", s), t1, 0.5, 0.86, 110, "#B3261E")
sfx(wt("hundred", s), "boom", vol=0.15)

# ---- 32 una décima ----
s = "32"; BG[s] = MAPN; t0, t1 = T[s], END[s]; tl_ = wt("lost", s)
for i, f in enumerate([CEDED_N, CEDED_N2]):
    a = full(f, tl_, t1, 6); a.op(0, 0); a.op(0.3, 1)
sfx(tl_, "boom", vol=0.18)
city("c32", PN, "VIIPURI", wt("viipuri", s), t1)
label("≈ 1/10 OF FINLAND", tl_ + 0.3, t1, 0.62, 0.62, 66, "#B3261E")

# ---- 33 evacuados ----
s = "33"; BG[s] = BG["evac"]; t0, t1 = T[s], END[s]
for i in range(4):
    st_ = t0 + i * 0.6; drive(f"rf33_{i}", "refugees", 330, 2100 + i * 380, 790 + (i % 2) * 40, st_, t1, -(t1 - st_) * 210, z=7, flip=True)
label("400,000+", wt("four", s), t1, 0.5, 0.15, 100, "#1A3C8C")

# ---- 34 bajas ----
s = "34"; BG[s] = WHITE; t0, t1 = T[s], END[s]
tf = wt("finnish", s); tsv = wt("soviet", s)
for i in range(4): pop(f"hf34_{i}", "helmet_fi", 380 + (i % 2) * 120, 700 - (i // 2) * 110, 110, tf + i * 0.08, t1, 7, snd=i == 0)
for i in range(16): pop(f"hs34_{i}", "helmet_su", 1150 + (i % 4) * 120, 800 - (i // 4) * 110, 110, tsv + i * 0.06, t1, 7, snd=i % 4 == 0)
label("~26,000", tf, t1, 0.23, 0.85, 80, "#1A3C8C")
label("100,000+", tsv, t1, 0.72, 0.9, 80, "#B3261E")

# ---- 35 independiente ----
s = "35"; BG[s] = MAPN; t0, t1 = T[s], END[s]
a = full(CEDED_N, t0, t1, 6); b = full(CEDED_N2, t0, t1, 6)
x, y = PN(26.0, 63.0); tk = wt("independence", s)
fg = pop("fg35", "flag_fi", x, y, 230, wt("kept", s), t1, 8); fg.bob(0.4, t1 - wt("kept", s), amp=8, period=1.2)
st = layer("st35", icon("stamp", 400), 1250, 540, 620, tk, t1, 9, rotate=-10); st.scale(0, 2.0); st.scale(0.18, 1.0, ez="easeOutBack"); st.op(0, 0); st.op(0.1, 1)
label("INDEPENDENT", tk + 0.05, t1, 1250 / W, 0.5, 80, "#B3261E", 0); sfx(tk, "boom", vol=0.18)

# ---- 36 Hitler toma nota ----
s = "36"; BG[s] = BG["europe"]; t0, t1 = T[s], END[s]
of = pop("of36", "officer", 520, 600, 380, wt("hitler's", s) - 0.6, t1, 8)
label("RED ARMY = WEAK?", wt("weak", s), t1, 0.62, 0.2, 76, "#B3261E")
pop("q36", "question", 1350, 520, 200, wt("weak", s), t1, 9)

# ---- 37 1941 ----
s = "37"; BG[s] = MAPN; t0, t1 = T[s], END[s]
for i, pts in enumerate([[(24.5, 58.2), (31.0, 58.9), (38.0, 59.2)], [(23.0, 57.7), (30.0, 58.0), (40.0, 58.2)]]):
    arrow_draw(route_frames(f"a37_{i}", [PN(*p) for p in pts], col=GREY, w=30), wt("germany's", s) + i * 0.2, t1)
arrow_draw(route_frames("a37f", [PN(28.5, 61.5), PN(31.5, 62.2), PN(34.6, 62.3)], col=BLUE, w=24), wt("offensive", s), t1)
label("JUNE 1941", t0 + 0.2, t1, 0.18, 0.2, 70, "#1A1A1A")
label("CONTINUATION WAR", wt("offensive", s), t1, 0.6, 0.45, 56, "#1A3C8C")

# ---- 38 veredicto ----
s = "38"; BG[s] = MAPN; t0, t1 = T[s], END[s]
for f in (CEDED_N, CEDED_N2): full(f, t0, t1, 6)
x2, y2 = PN(44.0, 63.0); pop("su38", "flag_su", x2, y2, 300, wt("soviet", s), t1, 7)
x, y = PN(26.0, 63.0); f = pop("fi38", "flag_fi", x, y, 230, wt("finland", s), t1, 7); f.bob(0.4, t1 - wt("finland", s), amp=7, period=1.2)
label("WON THE WAR", wt("won", s), t1, x2 / W, (y2 + 200) / H, 60, "#B3261E")
label("KEPT INDEPENDENCE", wt("independence", s), t1, x / W, (y + 170) / H, 54, "#1A3C8C")
stk = pop("stk38", "stick", 1700, 800, 260, wt("another", s), t1, 9)

# ---------------- sfx ----------------
ev = []
for x in SFX:
    if x["type"] == "whoosh_one": ev.append({"t": x["t"] - 0.15, "type": "pop", "vol": 0.05})
    else: ev.append(x)
json.dump({"music": True, "bpm": 96, "music_vol": 0.08, "whoosh_cuts": True, "events": ev}, open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "short_sfx.py"), HERE], check=True)
print("capas:", len(LAYERS), "etiquetas:", len(LABELS))

# vista previa: un fotograma compuesto por escena (sin animación) para revisar posiciones
if "--prep" in sys.argv:
    os.makedirs(os.path.join(COMP, "_preview"), exist_ok=True)
    for sid in IDS:
        tm = (T[sid] + END[sid]) / 2
        im = Image.open(BG[sid]).convert("RGBA")
        for st_, en, path, an, z in sorted(LAYERS, key=lambda L: L[4]):
            if st_ <= tm < en and os.path.getsize(path) > 0:
                im.alpha_composite(Image.open(path).convert("RGBA"))
        d = ImageDraw.Draw(im)
        for st_, en, txt, x, y, size, col, *_ in LABELS:
            if st_ <= tm < en: d.text((x * W - 4 * len(txt), y * H), txt, fill=col)
        im.convert("RGB").resize((960, 540)).save(os.path.join(COMP, "_preview", f"{sid}.jpg"), quality=80)
    sys.exit(0)

# ======================= render propio (sin OpenReel) =======================
if "--render" in sys.argv:
    TEXTS = []
    def text(txt, s, e, x, y, size, col, stroke, scol="#000000", anim="pop"):
        TEXTS.append({"t": txt, "s": round(s, 3), "e": round(e, 3), "x": x, "y": y, "size": size, "col": col, "stroke": stroke, "scol": scol})
    src = open(os.path.abspath(__file__), encoding="utf-8").read().split("# ---TEXTOS---")[2].split('call("save_project")')[0]
    exec(src)
    spec = {"W": W, "H": H, "total": TOTAL,
            "bg": [{"s": T[sid], "e": END[sid], "path": BG[sid], "k": BGK[sid].k if sid in BGK else []} for sid in IDS],
            "layers": [{"s": a, "e": b, "path": p_, "cx": an.cx, "cy": an.cy, "z": z, "k": an.k} for a, b, p_, an, z in LAYERS if b - a >= 0.05],
            "texts": TEXTS}
    json.dump(spec, open(os.path.join(HERE, "render_spec.json"), "w", encoding="utf-8"))
    print("spec:", len(spec["layers"]), "capas,", len(TEXTS), "textos"); sys.exit(0)

# ======================= OpenReel =======================
from openreel_api import call
def url(path):
    return "http://127.0.0.1:8777/" + urllib.parse.quote(os.path.relpath(path, ROOT).replace("\\", "/"))
MED = {}
def media(path):
    if path not in MED: MED[path] = call("import_media_from_url", {"url": url(path), "name": os.path.basename(path)})["mediaId"]
    return MED[path]

call("create_project", {"name": "Video 5 Winter War", "width": W, "height": H, "frameRate": 30})
call("set_canvas_background", {"backgroundFillMode": "color", "layoutBackgroundColor": "#FFFFFF"})
tracks = call("list_tracks")
while len([t for t in tracks if t["type"] == "audio"]) < 2:
    call("add_track", {"trackType": "audio"}); tracks = call("list_tracks")
aud = [t["id"] for t in tracks if t["type"] == "audio"]
imgs = [t["id"] for t in tracks if t["type"] == "image"]
while len(imgs) < 30:
    call("add_track", {"trackType": "image", "position": 0}); imgs = [t["id"] for t in call("list_tracks") if t["type"] == "image"]
base_track, over_tracks = imgs[-1], imgs[:-1]
call("add_clip", {"trackId": aud[0], "mediaId": media(os.path.join(HERE, "voz.wav")), "startTime": 0})
call("add_clip", {"trackId": aud[1], "mediaId": media(os.path.join(HERE, "sfx.wav")), "startTime": 0})

def add(track, path, start, end):
    before = {c["id"] for c in call("list_clips")}
    call("add_clip", {"trackId": track, "mediaId": media(path), "startTime": round(start, 3)})
    cid = [c["id"] for c in call("list_clips") if c["id"] not in before][0]
    call("trim_clip", {"clipId": cid, "inPoint": 0, "outPoint": round(end - start, 3)})
    return cid

for sid in IDS:
    cid = add(base_track, BG[sid], T[sid], END[sid])
    if sid in BGK:
        call("set_clip_transform", {"clipId": cid, "transform": BGK[sid].transform()})
        call("set_clip_keyframes", {"clipId": cid, "keyframes": BGK[sid].k})
print("fondos listos")
busy = {t: [] for t in over_tracks}
LAYERS.sort(key=lambda L: (-L[4], L[0]))
NT = len(over_tracks)
for n, (start, end, path, an, z) in enumerate(LAYERS):
    if end - start < 0.05: continue
    order = over_tracks[max(0, min(NT - 1, 10 - z)):] + over_tracks
    for tr in order:
        if all(end <= a0 or start >= b0 for a0, b0 in busy[tr]): busy[tr].append((start, end)); break
    else: raise RuntimeError("faltan pistas")
    cid = add(tr, path, start, end)
    call("set_clip_transform", {"clipId": cid, "transform": an.transform()})
    if an.k: call("set_clip_keyframes", {"clipId": cid, "keyframes": an.k})
    if n % 25 == 0: print("capa", n, "/", len(LAYERS), flush=True)
print("capas subidas")

def text(txt, s, e, x, y, size, col, stroke, scol="#000000", anim="pop"):
    r_ = call("create_text_clip", {"clip": {"text": txt, "startTime": round(s, 3), "duration": round(max(0.2, e - s), 3), "animation": anim,
        "style": {"fontFamily": "Inter", "fontSize": size, "fontWeight": 900, "color": col, "lineHeight": 1.0,
                  "strokeColor": scol, "strokeWidth": stroke, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r_["id"], "updates": {"transform": {"position": {"x": x, "y": y}}}})

# ---TEXTOS---
for s_, e_, txt, x, y, size, col, stroke, scol in LABELS: text(txt, s_, e_, x, y, size, col, stroke, scol)

# titulares estables por escena (arriba a la izquierda no tapa mapas: centrados arriba)
text("ONE FROZEN ROAD", 0.0, END["01"], 0.5, 0.08, 84, "#FFD23F", 10)

# subtítulos de 2-3 palabras, mínimo ~0.65 s en pantalla
KEY = {"shattered", "frozen", "stalin", "invaded", "forty", "1917", "leningrad", "secret", "hanko", "rejected", "staged",
       "helsinki", "expelled", "puppet", "purges", "mannerheim", "kollaa", "häyhä", "half", "minus", "skis", "motti",
       "suomussalmi", "raate", "captured", "molotov", "cocktails", "timoshenko", "february", "broke", "summa", "viipuri",
       "never", "treaty", "hundred", "tenth", "evacuated", "twenty-six", "independence", "weak", "hitler's", "1941", "won"}
def hot(w): return any(p in KEY for p in clean(w).split())
chunks, cur = [], []
for w in WORDS:
    txt = " ".join(x["w"] for x in cur + [w])
    if cur and (len(cur) >= 3 or len(txt) > 20 or w["s"] - cur[-1]["e"] > 0.35 or w["scene"] != cur[-1]["scene"]
                or (len(cur) >= 2 and cur[-1]["w"].endswith((",", ".", "?", ";", ":")))):
        chunks.append(cur); cur = []
    cur.append(w)
chunks.append(cur)
merged = []
for ch in chunks:
    if merged and ch[0]["s"] - merged[-1][0]["s"] < 0.65 and len(" ".join(x["w"] for x in merged[-1] + ch)) <= 22 \
       and merged[-1][-1]["scene"] == ch[0]["scene"]:
        merged[-1] = merged[-1] + ch
    else: merged.append(ch)
for i, ch in enumerate(merged):
    s_ = ch[0]["s"]; nxt = merged[i + 1][0]["s"] if i + 1 < len(merged) else TOTAL + 0.5
    e_ = nxt if nxt - ch[-1]["e"] < 0.6 else ch[-1]["e"] + 0.45
    txt = " ".join(x["w"] for x in ch).upper().replace("...", "")
    text(txt, s_, e_, 0.5, 0.93, 62, "#FFD23F" if any(hot(x["w"]) for x in ch) else "#FFFFFF", 9)
print("subtítulos:", len(merged))
call("save_project"); print("listo")

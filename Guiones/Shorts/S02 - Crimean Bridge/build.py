"""Short S02 — Why Ukraine Keeps Hitting the Crimean Bridge (estilo casi todo animado, textos más lentos).
Requiere OpenReel abierto con Scripts/abrir_openreel_local.bat y `python -m http.server 8777 --bind 127.0.0.1` en la raíz.
Uso: python build.py [--prep]   (--prep solo compone capas + sfx.json, sin tocar OpenReel)"""
import json, os, sys, math, subprocess, urllib.parse
import numpy as np
ROOT = r"E:\Historias TIK\WarMap Stick"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from short_anim import cutout, place, bg_full, Anim, W, H
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mapa
from mapa import P

CAP = os.path.join(ROOT, "Imagenes", "Shorts", "S02", "capas")
COMP = os.path.join(ROOT, "Imagenes", "Shorts", "S02", "comp")
os.makedirs(COMP, exist_ok=True)
tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
T = {s["id"]: s["start"] for s in tl["timeline"]}
TOTAL = tl["total"]; WORDS = tl["words"]
END = {sid: (T[f"{int(sid)+1:02d}"] if int(sid) < 10 else TOTAL + 0.5) for sid in T}

def wt(word, after=0.0):
    for w in WORDS:
        if w["s"] >= after - 0.01 and word.lower() in w["w"].strip(".,'’?").lower().split():
            return w["s"]
    raise KeyError(word)

SFX = []
def sfx(t, typ, **kw): SFX.append({"t": round(t, 3), "type": typ, **kw})

# ---------------- fondos ----------------
BR = os.path.join(COMP, "bg_bridge_broken.png"); bg_full(os.path.join(CAP, "bg_bridge_broken.png"), BR)
MAP = os.path.join(COMP, "bg_map.png"); mapa.draw(MAP)
# el arco = píxeles que cambian entre puente entero y roto
a = Image.open(os.path.join(CAP, "bg_bridge.png")).convert("RGBA"); b = Image.open(os.path.join(CAP, "bg_bridge_broken.png")).convert("RGBA")
diff = (np.abs(np.asarray(a, int)[..., :3] - np.asarray(b, int)[..., :3]).sum(2) > 40)
arr = np.asarray(a).copy(); arr[..., 3] = np.where(diff, 255, 0)
r = W / a.width; arch = Image.fromarray(arr).resize((W, int(a.height * r)), Image.LANCZOS)
ARCH = os.path.join(COMP, "arch.png"); can = Image.new("RGBA", (W, H), (0, 0, 0, 0)); can.alpha_composite(arch, (0, (H - arch.height) // 2)); can.save(ARCH)
ARCH_C = (540, 755)
fy = lambda y: y * r + (H - int(a.height * r)) // 2
RAIL_TOP, ROAD_TOP, WATER = fy(600), fy(672), fy(776)

# ---------------- dibujos propios ----------------
RED = (214, 56, 50, 255); YEL = (255, 210, 63, 255); BLK = (0, 0, 0, 255)
def chaikin(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(0.75*x0+0.25*x1, 0.75*y0+0.25*y1), (0.25*x0+0.75*x1, 0.25*y0+0.75*y1)]
        pts = out + [pts[-1]]
    return pts

def route_frames(name, pts, fracs=(0.25, 0.5, 0.75, 1.0), col=RED, w=20, head=True):
    pts = chaikin(pts); outs = []
    for k, frac in enumerate(fracs, 1):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        seg = pts[: max(2, int(len(pts) * frac))]
        d.line(seg, fill=BLK, width=w + 10, joint="curve"); d.line(seg, fill=col, width=w, joint="curve")
        x, y = seg[0]; d.ellipse([x-15, y-15, x+15, y+15], fill=col, outline=BLK, width=5)
        if head and frac == 1.0:
            q, p = seg[-1], seg[-4]; ang = math.atan2(q[1]-p[1], q[0]-p[0]); L = 62
            tip = (q[0] + math.cos(ang)*16, q[1] + math.sin(ang)*16)
            d.polygon([tip, (tip[0]-L*math.cos(ang-.5), tip[1]-L*math.sin(ang-.5)), (tip[0]-L*math.cos(ang+.5), tip[1]-L*math.sin(ang+.5))], fill=col, outline=BLK, width=5)
        f = os.path.join(COMP, f"{name}_{k}.png"); im.save(f); outs.append(f)
    return outs

def icon(kind, size=240):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); s = size
    if kind == "ring":
        d.ellipse([12, 12, s-12, s-12], outline=BLK, width=22); d.ellipse([12, 12, s-12, s-12], outline=YEL, width=13)
    elif kind == "x":
        for p0, p1 in [((s*.18, s*.18), (s*.82, s*.82)), ((s*.82, s*.18), (s*.18, s*.82))]:
            d.line([p0, p1], fill=BLK, width=int(s*.2)); d.line([p0, p1], fill=RED, width=int(s*.13))
    return im

def bridge_icon():
    """El puente sobre el estrecho en el mapa: barra amarilla gruesa con contorno."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    p0, p1 = P(36.47, 45.31), P(36.70, 45.24)
    d.line([p0, p1], fill=BLK, width=26); d.line([p0, p1], fill=YEL, width=14)
    f = os.path.join(COMP, "map_bridge.png"); im.save(f); return f, ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)

# ---------------- capas ----------------
EL = {}
def el(name):
    if name not in EL: EL[name] = cutout(os.path.join(CAP, f"el_{name}.png"))
    return EL[name]
LAYERS = []
def layer(tag, img, cx, cy, width, start, end, z=5, flip=False, rotate=0):
    f = os.path.join(COMP, f"{tag}.png"); place(img, cx, cy, width, f, flip=flip, rotate=rotate)
    an = Anim(cx, cy); LAYERS.append([start, end, f, an, z]); return an
def full(path, start, end, z=5, c=(W/2, H/2)):
    an = Anim(*c); LAYERS.append([start, end, path, an, z]); return an

def smoke_puffs(tag, cx, cy, t0, t1, every=0.8, w=170, rise=280, z=3):
    t = t0; i = 0
    while t < t1 - 0.4:
        d = min(2.2, t1 - t); an = layer(f"{tag}_{i}", el("smoke"), cx + (i % 3 - 1) * 16, cy, w, t, t + d, z)
        an.scale(0, 0.45); an.scale(d, 1.35); an.op(0, 0.0); an.op(0.25, 0.85); an.op(d, 0.0)
        an.pos(0, 0, 0); an.pos(d, (18 if i % 2 else -18), -rise); t += every; i += 1

def boom_at(tag, cx, cy, t, w=300, z=9, vol=0.28):
    an = layer(tag, el("explosion"), cx, cy, w, t, t + 0.6, z)
    an.scale(0, 0.1, ez="easeOutBack"); an.scale(0.18, 1.2, ez="easeOutBack"); an.scale(0.6, 0.0, ez="easeInBack"); an.rot(0, -10); an.rot(0.6, 15)
    sfx(t, "boom", vol=vol)

def drive(tag, name, width, cy, start, end, x0, x1, z=6, bounce=True):
    """Vehículo que cruza de x0 a x1 entre start y end (moviéndose todo el clip)."""
    an = layer(tag, el(name), x0, cy, width, start, end, z)
    an.move(0, end - start, (0, 0), (x1 - x0, 0), ez="linear")
    return an

def arrow_draw(frames, t0, t1, z=7, step=0.12):
    for k, f in enumerate(frames, 1):
        s = t0 + (k - 1) * step; e = t0 + k * step if k < len(frames) else t1
        full(f, s, e, z)

BG = {}
BGK = {}
TRUCK_W, FUEL_W, TRAIN_W = 190, 200, 360
TRUCK_Y = ROAD_TOP - TRUCK_W * 0.48 / 2 + 4
FUEL_Y = ROAD_TOP - FUEL_W * 0.475 / 2 + 4
TRAIN_Y = RAIL_TOP - TRAIN_W * 0.238 / 2 + 6
MAPB, MAPB_C = bridge_icon()
LABELS = []  # (start, end, text, x, y, color)

# ===== 01 HOOK VISUAL: desde el cuadro 0 los drones ya caen y el arco se desploma al decir "dropped" =====
s, e = T["01"], END["01"]; BG["01"] = BR
t_dr = wt("dropped", s); t_kh = wt("keeps", s)
BGK["01"] = Anim(W / 2, H / 2); BGK["01"].pos(0, 0, 0); BGK["01"].shake(0.05, 0.5, 16, 0.05); BGK["01"].shake(t_dr - s, 0.8, 22, 0.05)
BGK["01"].shake(t_kh - s + 0.3, 0.6, 14, 0.05)
ar = full(ARCH, s, e, 6, ARCH_C)
ar.pos(0, 0, 0); ar.shake(0.05, 0.5, 16, 0.05); ar.shake(0.55, t_dr - s - 0.55, 8, 0.05)
ar.pos(t_dr - s, 0, 0); ar.rot(t_dr - s, 0)
ar.pos(t_dr - s + 0.75, 0, 360, "easeInCubic"); ar.rot(t_dr - s + 0.75, 14, "easeInCubic"); ar.op(t_dr - s + 0.45, 1); ar.op(t_dr - s + 0.75, 0)
# primera oleada: 3 drones ya visibles en el cuadro 0
for i, (dx, dy, hit, sx, sy) in enumerate([(0, -40, 0.15, 230, -200), (-120, 20, 0.45, 420, -380), (130, 0, t_dr - s - 0.05, 620, -560)]):
    d = layer(f"s1_dr{i}", el("drone"), 540 + dx, 720 + dy, 160, s, s + hit, 10)
    d.move(0, hit, (sx, sy), (0, 0), ez="easeInQuad")
    boom_at(f"s1_b{i}", 540 + dx, 730 + dy, s + hit, 380 if i == 0 else 320, vol=0.34 - i * 0.03)
sp = layer("s1_splash", el("splash"), 540, WATER - 40, 460, t_dr + 0.6, e, 9); sp.pop_in(0, 0.3); sp.op(1.0, 1); sp.op(1.5, 0)
sfx(t_dr + 0.6, "boom", vol=0.24)
sfx(0, "planes", d=1.4, vol=0.09)
smoke_puffs("s1_smk", 540, 800, s + 0.3, e, every=0.4, w=220, rise=340)
drive("s1_train", "train", TRAIN_W, TRAIN_Y, s, e, -250, 1350, z=4)
# segunda oleada al decir "keeps hitting it"
for i, (x, y, hit) in enumerate([(210, ROAD_TOP - 10, wt("hitting", s)), (860, RAIL_TOP - 10, wt("it", t_kh + 0.3) + 0.05)]):
    d = layer(f"s1_dw{i}", el("drone"), x, y, 140, hit - 0.7, hit, 10); d.move(0, 0.7, (560, -520), (0, 0), ez="easeInQuad")
    boom_at(f"s1_bw{i}", x, y, hit, 280, vol=0.26)
    smoke_puffs(f"s1_sw{i}", x, y - 40, hit + 0.2, e, every=0.5, w=150, rise=260)
sfx(t_kh - 0.7, "planes", d=1.3, vol=0.07)

# ===== 02 mapa: el puente une Rusia y Crimea =====
s, e = T["02"], END["02"]; BG["02"] = MAP
t_st = wt("strait", s)
mb = full(MAPB, t_st - 0.2, e, 7, MAPB_C); mb.pop_in(0, 0.35, 1.0); sfx(t_st - 0.2, "pop")
rg = layer("s2_ring", icon("ring"), *MAPB_C, 170, t_st, e, 8); rg.pop_in(0, 0.35); rg.pulse(0.35, e - t_st, 0.6, 0.93, 1.08)
LABELS += [(wt("russia", s), END["03"], "RUSSIA", *P(38.25, 45.55)), (wt("crimea", s), END["03"], "CRIMEA", *P(34.2, 45.2)),
           (s, END["03"], "KERCH STRAIT", MAPB_C[0], MAPB_C[1] + 120)]
sfx(wt("russia", s), "pop"); sfx(wt("crimea", s), "pop")

# ===== 03 2014: Rusia toma Crimea (mancha roja + bandera), construye el cruce =====
s, e = T["03"], END["03"]; BG["03"] = MAP
t_se = wt("seized", s)
TINT = os.path.join(COMP, "crimea_tint.png"); mapa.crimea_mask(TINT, (214, 56, 50, 95))
tn = full(TINT, t_se, e, 4); tn.op(0, 0); tn.op(0.5, 1); sfx(t_se, "whoosh_one")
fl = layer("s3_flag", el("flag"), P(34.0, 45.6)[0], P(34.0, 45.6)[1] - 70, 170, t_se + 0.3, e, 7)
fl.move(0, 0.55, (0, -700), (0, 0), ez="easeOutBounce"); fl.rot(0.55, 0); fl.rot(0.9, -6, "easeInOutSine"); fl.rot(1.3, 4, "easeInOutSine"); fl.rot(1.7, 0, "easeInOutSine")
sfx(t_se + 0.85, "click")
t_b = wt("built", s)
mb = full(MAPB, s, e, 7, MAPB_C); mb.pulse(t_b - s, e - s, 0.5, 0.9, 1.25); sfx(t_b, "pop")

# ===== 04 tráfico: tren, camiones, cisterna =====
s, e = T["04"], END["04"]; BG["04"] = BR
ar = full(ARCH, s, e, 6, ARCH_C)
drive("s4_train", "train", TRAIN_W, TRAIN_Y, wt("trains", s) - 0.4, e, -250, 1300, z=4); sfx(wt("trains", s), "planes", d=2.5, vol=0.05)
drive("s4_truck", "truck", TRUCK_W, TRUCK_Y, wt("trucks", s) - 0.5, e, -150, 1250, z=8)
drive("s4_fuel", "fueltruck", FUEL_W, FUEL_Y, wt("fuel", s) - 0.6, e, -150, 1100, z=8)
drive("s4_truck2", "truck", TRUCK_W, TRUCK_Y, wt("military", s) - 0.6, e, -150, 700, z=8)
for wd in ["trains", "trucks", "fuel", "military"]: sfx(wt(wd, s), "pop")

# ===== 05 noviembre 2026: drones, explosiones, el arco cae =====
s, e = T["05"], END["05"]; BG["05"] = BR
t_br = wt("brought", s); t_st = wt("strikes", s)
ar = full(ARCH, s, e, 6, ARCH_C)
fall = t_br - s
ar.pos(0, 0, 0); ar.shake(t_st - s + 0.2, 0.4, 10, 0.05); ar.pos(fall, 0, 0)
ar.pos(fall + 0.8, 0, 340, "easeInCubic"); ar.rot(fall, 0); ar.rot(fall + 0.8, -14, "easeInCubic"); ar.op(fall + 0.45, 1); ar.op(fall + 0.8, 0)
for i, (dx, dy, dt) in enumerate([(0, 0, 0.0), (-130, 60, 0.35), (140, 40, 0.7)]):
    st = t_st - 1.0 + dt
    d = layer(f"s5_dr{i}", el("drone"), 540 + dx, 720 + dy, 150, st, st + 1.0, 10)
    d.move(0, 1.0, (650, -620), (0, 0), ez="easeInQuad")
    boom_at(f"s5_b{i}", 540 + dx, 730 + dy, st + 1.0, 300, vol=0.26 - i * 0.04)
sfx(t_st - 1.0, "planes", d=2.0, vol=0.08)
sp = layer("s5_splash", el("splash"), 540, WATER - 40, 440, t_br + 0.7, e, 9); sp.pop_in(0, 0.3); sfx(t_br + 0.7, "boom", vol=0.2)
smoke_puffs("s5_smk", 540, 800, t_st + 0.2, e, every=0.45, w=210, rise=340)

# ===== 06 el tren se detiene =====
s, e = T["06"], END["06"]; BG["06"] = BR
t_d = wt("damaged", s); t_h = wt("halted", s)
boom_at("s6_boom", 760, RAIL_TOP - 10, t_d, 220, vol=0.2)
smoke_puffs("s6_smk", 760, RAIL_TOP - 60, t_d + 0.2, e, every=0.6, w=150, rise=250)
tr = layer("s6_train", el("train"), 200, TRAIN_Y, TRAIN_W, s, e, 4)
tr.pos(0, -560, 0); tr.pos(t_h - s - 0.3, 0, 0, "easeOutCubic"); tr.shake(t_h - s - 0.3, 0.3, 8, 0.05)
sfx(t_h - 0.3, "creak")
sg = layer("s6_stop", el("stop"), 220, 600, 170, t_h, e, 9); sg.pop_in(0, 0.35); sg.pulse(0.35, e - t_h, 0.5, 0.94, 1.08); sfx(t_h, "click")

# ===== 07 ruta terrestre por el sur ocupado =====
s, e = T["07"], END["07"]; BG["07"] = MAP
ROUTE = [P(39.0, 47.65), P(37.6, 47.5), P(36.3, 47.25), P(35.4, 47.0), P(34.8, 46.4), P(34.35, 45.85)]
fr = route_frames("route", ROUTE)
t_l = wt("land", s); arrow_draw(fr, t_l - 0.1, e); sfx(t_l, "whoosh_one")
xm = layer("s7_x", icon("x"), *MAPB_C, 110, s, e, 8); xm.pop_in(0, 0.35); sfx(s, "click")
mb = full(MAPB, s, e, 7, MAPB_C)
LABELS += [(wt("southern", s), END["08"], "SOUTHERN UKRAINE", *P(34.3, 47.6))]

# ===== 08 desvío: camiones lentos por la ruta, reloj =====
s, e = T["08"], END["08"]; BG["08"] = MAP
full(fr[-1], s, e, 5); full(MAPB, s, e, 7, MAPB_C); layer("s8_x", icon("x"), *MAPB_C, 110, s, e, 8)
pts = chaikin(ROUTE)
for i, dt in enumerate([0.0, 1.3, 2.6]):
    st = s + dt; dur = e - st
    t0 = layer(f"s8_tr{i}", el("truck"), pts[0][0], pts[0][1] - 30, 110, st, e, 9)
    n = 6
    for k in range(n + 1):
        frac = min(1, k / n * dur / 3.4); q = pts[min(len(pts) - 1, int(frac * (len(pts) - 1)))]
        t0.pos(k / n * dur, q[0] - pts[0][0], q[1] - pts[0][1], "linear")
t_sl = wt("slower", s)
ck = layer("s8_clock", el("clock"), 860, 1060, 190, t_sl - 0.3, e, 9); ck.pop_in(0, 0.35); ck.rot(0.35, 0); ck.rot(e - t_sl + 0.3, 200)
sfx(t_sl - 0.3, "pop"); sfx(t_sl, "click")
boom_at("s8_boom", *P(35.1, 46.65), wt("riskier", s), 200, vol=0.2)

# ===== 09 símbolo: bandera en el puente, Stick señala =====
s, e = T["09"], END["09"]; BG["09"] = BR
t_hit = wt("hit", s)
boom_at("s9_boom", 860, 800, t_hit, 300, vol=0.26)
smoke_puffs("s9_smk", 300, 820, s, e, every=0.6, w=170, rise=280)
fl = layer("s9_flag", el("flag"), 860, ROAD_TOP - 95, 190, wt("symbol", s), e, 7)
fl.pop_in(0, 0.35); fl.shake(0.4, 0.4, 10); fl.rot(0.9, -6, "easeInOutSine"); fl.rot(1.4, 4, "easeInOutSine"); fl.rot(1.9, 0, "easeInOutSine")
sfx(wt("symbol", s), "pop")
st = layer("s9_stick", el("stick"), 330, 1160, 240, wt("putin", s) - 0.2, e, 10, flip=True)
st.move(0, 0.5, (-500, 0), (0, 0), ez="easeOutCubic"); st.bob(0.5, e - s, amp=5, period=1.2); sfx(wt("putin", s) - 0.2, "whoosh_one")

# ===== 10 cierre: pregunta =====
s, e = T["10"], END["10"]; BG["10"] = MAP
full(TINT, s, e, 4); mb = full(MAPB, s, e, 7, MAPB_C); mb.pulse(0, e - s, 0.5, 0.9, 1.25)
q = layer("s10_q", el("question"), MAPB_C[0], MAPB_C[1] - 250, 170, wt("supplied", s) - 0.3, e, 9); q.pop_in(0, 0.4); q.pulse(0.4, e - s, 0.6, 0.92, 1.1)
sfx(wt("supplied", s) - 0.3, "pop")
sk = layer("s10_stick", el("stick_think"), 880, 1180, 170, s, e, 10)
sk.move(0, 0.5, (400, 0), (0, 0), ez="easeOutCubic"); sk.bob(0.5, e - s, amp=5, period=1.3)
LABELS += [(s, e, "CRIMEA", *P(34.2, 45.2)), (s, e, "RUSSIA", *P(38.25, 45.55))]

# ---------------- sfx ----------------
ev = []
for x in SFX:
    if x["type"] == "whoosh_one": ev.append({"t": x["t"] - 0.15, "type": "pop", "vol": 0.05})
    else: ev.append(x)
json.dump({"music": True, "bpm": 104, "music_vol": 0.1, "whoosh_cuts": True, "events": ev}, open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "short_sfx.py"), HERE], check=True)
print("capas:", len(LAYERS))
if "--prep" in sys.argv: sys.exit(0)

# ======================= OpenReel =======================
from openreel_api import call
def url(path):
    return "http://127.0.0.1:8777/" + urllib.parse.quote(os.path.relpath(path, ROOT).replace("\\", "/"))
MED = {}
def media(path):
    if path not in MED: MED[path] = call("import_media_from_url", {"url": url(path), "name": os.path.basename(path)})["mediaId"]
    return MED[path]

call("create_project", {"name": "Short S02 Crimean Bridge v2", "width": W, "height": H, "frameRate": 30})
call("set_canvas_background", {"backgroundFillMode": "color", "layoutBackgroundColor": "#FFFFFF"})
tracks = call("list_tracks")
while len([t for t in tracks if t["type"] == "audio"]) < 2:
    call("add_track", {"trackType": "audio"}); tracks = call("list_tracks")
aud = [t["id"] for t in tracks if t["type"] == "audio"]
imgs = [t["id"] for t in tracks if t["type"] == "image"]
while len(imgs) < 15:
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

for sid in sorted(T):
    cid = add(base_track, BG[sid], T[sid], END[sid])
    if sid in BGK:
        call("set_clip_transform", {"clipId": cid, "transform": BGK[sid].transform()})
        call("set_clip_keyframes", {"clipId": cid, "keyframes": BGK[sid].k})
busy = {t: [] for t in over_tracks}
LAYERS.sort(key=lambda L: (-L[4], L[0]))
NT = len(over_tracks)
for start, end, path, an, z in LAYERS:
    order = over_tracks[max(0, min(NT - 1, 10 - z)):] + over_tracks
    for tr in order:
        if all(end <= a0 or start >= b0 for a0, b0 in busy[tr]): busy[tr].append((start, end)); break
    else: raise RuntimeError("faltan pistas")
    cid = add(tr, path, start, end)
    call("set_clip_transform", {"clipId": cid, "transform": an.transform()})
    if an.k: call("set_clip_keyframes", {"clipId": cid, "keyframes": an.k})
print("capas subidas")

def text(txt, s, e, x, y, size, col, stroke, scol="#000000", anim="pop"):
    r_ = call("create_text_clip", {"clip": {"text": txt, "startTime": round(s, 3), "duration": round(max(0.2, e - s), 3), "animation": anim,
        "style": {"fontFamily": "Inter", "fontSize": size, "fontWeight": 900, "color": col, "lineHeight": 1.0,
                  "strokeColor": scol, "strokeWidth": stroke, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r_["id"], "updates": {"transform": {"position": {"x": x, "y": y}}}})

# etiquetas del mapa
for s, e, txt, x, y in LABELS: text(txt, s, e, x / W, y / H, 50, "#1A1A1A", 7, "#FFFFFF")

# titulares estables por frase
HEAD = [
    (0.0, wt("nineteen-kilometre"), "BRIDGE DOWN!", "#FFD23F"), (wt("nineteen-kilometre"), wt("and"), "RUSSIA'S 19 KM\nBRIDGE", "#FFFFFF"),
    (wt("and"), T["02"], "AGAIN AND AGAIN", "#FFD23F"),
    (T["02"], T["03"], "RUSSIA ↔ CRIMEA", "#FFFFFF"), (T["03"], T["04"], "2014: SEIZED", "#FFD23F"),
    (T["04"], T["05"], "SUPPLY LINE", "#FFFFFF"), (T["05"], T["06"], "NOVEMBER 2026", "#FFD23F"),
    (T["06"], T["07"], "RAIL HALTED", "#FFFFFF"), (T["07"], T["08"], "THE LAND ROUTE", "#FFFFFF"),
    (T["08"], T["09"], "SLOWER + RISKIER", "#FFD23F"), (T["09"], T["10"], "PUTIN'S SYMBOL", "#FFD23F"),
    (T["10"], TOTAL + 0.5, "WITHOUT\nTHE BRIDGE?", "#FFFFFF"),
]
for s, e, txt, col in HEAD: text(txt, s, e, 0.5, 0.14, 96, col, 9)

# subtítulos de 2-3 palabras, mínimo ~0.65 s en pantalla
KEY = {"nineteen-kilometre", "dropped", "keeps", "hitting", "kerch", "occupied", "seized", "2014", "rail", "fuel", "military",
       "november", "2026", "strikes", "arch", "halted", "damaged", "land", "slower", "riskier", "symbol", "putin", "2018", "without"}
def clean(w): return w.strip(".,'’?").lower()
def hot(w): return any(p in KEY for p in clean(w).split())
chunks, cur = [], []
for w in WORDS:
    txt = " ".join(x["w"] for x in cur + [w])
    if cur and (len(cur) >= 3 or len(txt) > 18 or w["s"] - cur[-1]["e"] > 0.35 or w["scene"] != cur[-1]["scene"]
                or (len(cur) >= 2 and cur[-1]["w"].endswith((",", ".", "?")))):
        chunks.append(cur); cur = []
    cur.append(w)
chunks.append(cur)
merged = []
for ch in chunks:  # junta trozos que durarían < 0.65 s
    if merged and ch[0]["s"] - merged[-1][0]["s"] < 0.65 and len(" ".join(x["w"] for x in merged[-1] + ch)) <= 20 \
       and merged[-1][-1]["scene"] == ch[0]["scene"]:
        merged[-1] = merged[-1] + ch
    else: merged.append(ch)
for i, ch in enumerate(merged):
    s = ch[0]["s"]; nxt = merged[i + 1][0]["s"] if i + 1 < len(merged) else TOTAL + 0.5
    e = nxt if nxt - ch[-1]["e"] < 0.6 else ch[-1]["e"] + 0.45
    e = max(e, s + 0.65) if i + 1 == len(merged) or s + 0.65 <= nxt else e
    txt = " ".join(x["w"] for x in ch).upper().replace("...", "").replace("NINETEEN-KILOMETRE", "19-KM")
    text(txt, s, e, 0.5, 0.73, 100, "#FFD23F" if any(hot(x["w"]) for x in ch) else "#FFFFFF", 11)
print("subtítulos:", len(merged))
call("save_project"); print("listo")

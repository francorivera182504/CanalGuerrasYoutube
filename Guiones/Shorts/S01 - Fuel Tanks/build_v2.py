"""Short S01 v2: escenas con elementos animados (capas de Codex) en OpenReel.
Requiere OpenReel abierto con Scripts/abrir_openreel_local.bat, el proyecto "Short S01 Fuel Tanks" activo
y `python -m http.server 8777 --bind 127.0.0.1` en la raíz del proyecto."""
import json, os, sys, math, urllib.parse
ROOT = r"E:\Historias TIK\WarMap Stick"
sys.path.insert(0, os.path.join(ROOT, "Scripts"))
from openreel_api import call
from short_anim import cutout, place, Anim, W, H
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(ROOT, "Imagenes", "Shorts", "S01", "capas")
COMP = os.path.join(ROOT, "Imagenes", "Shorts", "S01", "comp")
os.makedirs(COMP, exist_ok=True)
tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
T = {s["id"]: s["start"] for s in tl["timeline"]}
TOTAL = tl["total"]
WORDS = tl["words"]
END = {sid: (T[f"{int(sid)+1:02d}"] if int(sid) < 10 else TOTAL + 0.4) for sid in T}

def wt(word, after=0.0):
    """Momento (s) en que Ryan dice `word` después de `after`."""
    for w in WORDS:
        if w["s"] >= after - 0.01 and w["w"].strip(".,'’").lower() == word.lower():
            return w["s"]
    raise KeyError(word)

def url(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    return "http://127.0.0.1:8777/" + urllib.parse.quote(rel)

# ---------------- dibujos propios: flechas, aro, check, X ----------------
RED = (214, 56, 50, 255)
def arrow_frames(name, p0, p1, ctrl, n=4):
    pts = []
    for i in range(101):
        t = i / 100
        pts.append(((1-t)**2*p0[0] + 2*(1-t)*t*ctrl[0] + t*t*p1[0], (1-t)**2*p0[1] + 2*(1-t)*t*ctrl[1] + t*t*p1[1]))
    outs = []
    for k, frac in enumerate([0.3, 0.55, 0.8, 1.0][:n], 1):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        seg = pts[: int(100 * frac) + 1]
        d.line(seg, fill=(0, 0, 0, 255), width=30, joint="curve"); d.line(seg, fill=RED, width=20, joint="curve")
        x, y = seg[0]; d.ellipse([x-16, y-16, x+16, y+16], fill=RED, outline=(0, 0, 0), width=5)
        if frac == 1.0:
            q, p = seg[-1], seg[-5]; a = math.atan2(q[1]-p[1], q[0]-p[0]); L = 70
            tip = (q[0] + math.cos(a)*18, q[1] + math.sin(a)*18)
            d.polygon([tip, (tip[0]-L*math.cos(a-.5), tip[1]-L*math.sin(a-.5)), (tip[0]-L*math.cos(a+.5), tip[1]-L*math.sin(a+.5))],
                      fill=RED, outline=(0, 0, 0), width=5)
        f = os.path.join(COMP, f"{name}_{k}.png"); im.save(f); outs.append(f)
    return outs

def icon(name, kind, size=220):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); s = size
    if kind == "ring":
        d.ellipse([10, 10, s-10, s-10], outline=(0, 0, 0, 255), width=22); d.ellipse([10, 10, s-10, s-10], outline=(255, 210, 63, 255), width=14)
    elif kind == "check":
        pts = [(s*.15, s*.55), (s*.4, s*.8), (s*.88, s*.22)]
        d.line(pts, fill=(0, 0, 0, 255), width=int(s*.2), joint="curve"); d.line(pts, fill=(60, 170, 70, 255), width=int(s*.13), joint="curve")
    elif kind == "x":
        for a, b in [((s*.18, s*.18), (s*.82, s*.82)), ((s*.82, s*.18), (s*.18, s*.82))]:
            d.line([a, b], fill=(0, 0, 0, 255), width=int(s*.2)); d.line([a, b], fill=RED, width=int(s*.13))
    elif kind == "tracer":  # ráfaga: rayas amarillas en diagonal
        for i in range(5):
            x0 = i * s * .2
            d.line([(x0, x0*.6), (x0 + s*.12, (x0 + s*.12)*.6)], fill=(0, 0, 0, 255), width=12)
            d.line([(x0, x0*.6), (x0 + s*.12, (x0 + s*.12)*.6)], fill=(255, 210, 63, 255), width=7)
    return im

# ---------------- capas ----------------
EL = {}
def el(name):
    if name not in EL:
        EL[name] = cutout(os.path.join(CAP, f"el_{name}.png"))
    return EL[name]

LAYERS = []  # (start, end, png_path, Anim, z)  z alto = más arriba
def layer(tag, img, cx, cy, width, start, end, z=5, flip=False, rotate=0):
    f = os.path.join(COMP, f"{tag}.png")
    place(img, cx, cy, width, f, flip=flip, rotate=rotate)
    a = Anim(cx, cy); LAYERS.append([start, end, f, a, z]); return a

def full_layer(path, start, end, z=5):
    a = Anim(W / 2, H / 2); LAYERS.append([start, end, path, a, z]); return a

def smoke_puffs(tag, cx, cy, t0, t1, every=0.8, w=170, rise=280, z=3):
    t = t0; i = 0
    while t < t1 - 0.4:
        d = min(2.2, t1 - t); a = layer(f"{tag}_{i}", el("smoke"), cx + (i % 3 - 1) * 14, cy, w, t, t + d, z)
        a.scale(0, 0.45); a.scale(d, 1.35); a.op(0, 0.0); a.op(0.25, 0.85); a.op(d, 0.0)
        a.pos(0, 0, 0); a.pos(d, (18 if i % 2 else -18), -rise)
        t += every; i += 1

def boom_at(tag, cx, cy, t, w=300, z=8):
    a = layer(tag, el("explosion"), cx, cy, w, t, t + 0.6, z)
    a.scale(0, 0.1, ez="easeOutBack"); a.scale(0.18, 1.2, ez="easeOutBack"); a.scale(0.6, 0.0, ez="easeInBack")
    a.rot(0, -10); a.rot(0.6, 15)

def flame_at(tag, cx, cy, t0, t1, w=110, z=6):
    a = layer(tag, el("flame"), cx, cy, w, t0, t1, z)
    a.scale(0, 0.0, ez="easeOutBack"); a.scale(0.3, 1.0, ez="easeOutBack")
    a.flicker(0.3, t1 - t0, period=0.17, amp=0.18, wobble=6)
    return a

def arrow_draw(tag, p0, p1, ctrl, t0, t1, z=7, step=0.11):
    for k, f in enumerate(arrow_frames(tag, p0, p1, ctrl), 1):
        s = t0 + (k - 1) * step; e = t0 + k * step if k < 4 else t1
        full_layer(f, s, e, z)

BG = {}
def bg(sid, key):
    BG[sid] = os.path.join(COMP, f"bg_{key}.png") if key else None

# ===== S01: hook (fuego, explosión, humo, aro en los tanques) =====
s, e = T["01"], END["01"]; bg("01", "A")
boom_at("s1_boom", 300, 845, s, 360)
flame_at("s1_f1", 255, 815, s + 0.12, e, 130)
flame_at("s1_f2", 470, 812, s + 0.3, e, 100)
smoke_puffs("s1_smk", 255, 740, s + 0.4, e)
tank_t = wt("barrels", s)
r = layer("s1_ring", icon("r", "ring", 400), 750, 1090, 600, tank_t, e, 7)
r.pop_in(0, 0.35); r.pulse(0.35, e - tank_t, 0.6, 0.95, 1.05)

# ===== S02: embargo (válvula gira, candado cae) =====
s, e = T["02"], END["02"]; bg("02", "B")
t_emb = wt("embargo", s)
wh = layer("s2_wheel", el("wheel"), 465, 738, 250, s, e, 6)
wh.rot(0, 0); wh.spin(t_emb - s - 0.9, t_emb - s + 0.6, 0, 540)
pl = layer("s2_lock", el("padlock"), 330, 965, 165, t_emb + 0.4, e, 7)
pl.move(0, 0.55, (0, -900), (0, 0), ez="easeOutBounce"); pl.rot(0.55, 0); pl.rot(0.8, -8, "easeInOutSine"); pl.rot(1.1, 0, "easeInOutSine")

# ===== S03: objetivo petrolero (flecha a Indonesia, torres aparecen) =====
s, e = T["03"], END["03"]; bg("03", "C")
arrow_draw("s3_arr", (735, 700), (500, 965), (720, 900), wt("seize", s) - 0.1, e)
t_oil = wt("oil", s)
for i, (x, y) in enumerate([(300, 1010), (545, 990), (420, 1060)]):
    d = layer(f"s3_der{i}", el("derrick"), x, y, 85, t_oil + i * 0.18, e, 8)
    d.pop_in(0, 0.35); d.bob(0.4, e - t_oil - i * 0.18, amp=6, period=1.0, phase=i)

# ===== S04: la flota llega a Hawái =====
s, e = T["04"], END["04"]; bg("04", "D")
fl = layer("s4_fleet", el("fleet"), 800, 965, 230, s, e, 6)
fl.move(0, 1.0, (520, 0), (0, 0), ez="easeOutCubic"); fl.bob(1.0, e - s, amp=6, period=1.4)

# ===== S05: Japón ataca Hawái (flecha + explosión) =====
s, e = T["05"], END["05"]; bg("05", "D")
fl = layer("s5_fleet", el("fleet"), 800, 965, 230, s, e, 6); fl.bob(0, e - s, amp=6, period=1.4)
t_st = wt("struck", s)
arrow_draw("s5_arr", (380, 745), (760, 935), (560, 560), t_st - 0.25, e)
boom_at("s5_boom", 800, 950, t_st + 0.25, 240)

# ===== S06: ataque (aviones disparando, explosiones, fuego, humo) =====
s, e = T["06"], END["06"]; bg("06", "E")
t_air = wt("aircraft", s)
for i, (y, w, dt) in enumerate([(560, 270, 0.0), (470, 220, 0.5), (650, 200, 0.95)]):
    st = t_air - 0.9 + dt
    p = layer(f"s6_plane{i}", el("plane"), 540, y, w, st, st + 2.3, 9, rotate=-14)
    p.move(0, 2.3, (-820, -120), (820, 260), ez="linear")
    for j in range(3):  # ráfagas que acompañan al avión
        ts = st + 0.6 + j * 0.35
        frac = (0.6 + j * 0.35) / 2.3
        x = 540 - 820 + 1640 * frac + w * 0.45; yy = y - 120 + 380 * frac + 90
        tr = layer(f"s6_tr{i}{j}", icon("t", "tracer", 260), x, yy, 200, ts, ts + 0.16, 8)
        tr.op(0, 1); tr.op(0.08, 0.2, "hold"); tr.op(0.12, 1, "hold")
ships = [(345, 1185, 330), (660, 1090, 250), (915, 1055, 180)]
t_dev = wt("devastated", s)
for i, (x, y, w) in enumerate(ships):
    tb = t_dev - 0.6 + i * 0.35
    boom_at(f"s6_boom{i}", x, y - 30, tb, w * 1.1)
    flame_at(f"s6_fl{i}", x - w * 0.1, y - 60, tb + 0.25, e, w * 0.38)
    smoke_puffs(f"s6_smk{i}", x - w * 0.1, y - 130, tb + 0.5, e, every=0.9, w=int(w * 0.55))

# ===== S07: lo que sobrevivió (aparecen tanques, dique, muelle vacío, checks y X) =====
s, e = T["07"], END["07"]; bg("07", None)
items = [("tanks", 195, 840, 330, wt("fuel", s)), ("drydock", 545, 840, 330, wt("repair", s)), ("berth", 890, 840, 290, wt("carriers", s))]
for name, x, y, w, t in items:
    a = layer(f"s7_{name}", el(name), x, y, w, t, e, 6); a.pop_in(0, 0.35)
t_sur = wt("survived", s)
for i, x in enumerate([195, 545]):
    c = layer(f"s7_chk{i}", icon("c", "check"), x, 600, 170, t_sur + i * 0.15, e, 8); c.pop_in(0, 0.3)
t_abs = wt("absent", s)
xx = layer("s7_x", icon("x", "x"), 890, 820, 230, t_abs, e, 8); xx.pop_in(0, 0.3); xx.pulse(0.3, e - t_abs, 0.5, 0.95, 1.08)
st = layer("s7_stick", el("stick"), 210, 1150, 270, s, e, 7)
st.move(0, 0.6, (-450, 0), (0, 0), ez="easeOutCubic"); st.bob(0.6, e - s, amp=5, period=1.2)

# ===== S08: la flota sigue luchando (barco zarpa) =====
s, e = T["08"], END["08"]; bg("08", "G")
sh = layer("s8_ship", el("ship"), 790, 1175, 430, s, e, 6)
sh.move(0, e - s, (0, 0), (380, 10), ez="easeInSine")
t = 0; i = 0
while t < e - s:
    sh.rot(t, 2 if i % 2 else -2, "easeInOutSine"); t += 0.6; i += 1
smoke_puffs("s8_smk", 800, 1080, s + 0.3, e, every=0.7, w=110, rise=200)

# ===== S09: el combustible quedó (fuego en el barco, aro en los tanques) =====
s, e = T["09"], END["09"]; bg("09", "A")
flame_at("s9_f1", 255, 815, s, e, 120)
flame_at("s9_f2", 470, 812, s + 0.2, e, 95)
smoke_puffs("s9_smk", 255, 740, s + 0.2, e)
t_f = wt("fuel", s)
r = layer("s9_ring", icon("r", "ring", 400), 750, 1090, 600, t_f, e, 7); r.pop_in(0, 0.35); r.pulse(0.35, e - t_f, 0.6, 0.95, 1.05)

# ===== S10: cierre (Stick señala el mapa) =====
s, e = T["10"], END["10"]
BG["10"] = os.path.join(ROOT, "Imagenes", "Shorts", "S01", "H.png")

# ======================= subir a OpenReel =======================
for c in call("list_clips"):
    if c["trackType"] == "text": call("remove_text_clip", {"clipId": c["id"]})
    else: call("remove_clip", {"clipId": c["id"]})

MED = {}
def media(path):
    if path not in MED:
        MED[path] = call("import_media_from_url", {"url": url(path), "name": os.path.basename(path)})["mediaId"]
    return MED[path]

if "--new" in sys.argv:  # proyecto limpio (los textos viejos no se pueden listar para borrarlos)
    call("create_project", {"name": "Short S01 Fuel Tanks v2", "width": W, "height": H, "frameRate": 30})
    call("set_canvas_background", {"backgroundFillMode": "color", "layoutBackgroundColor": "#FFFFFF"})
tracks = call("list_tracks")
while len([t for t in tracks if t["type"] == "audio"]) < 2:
    call("add_track", {"trackType": "audio"}); tracks = call("list_tracks")
aud = [t["id"] for t in tracks if t["type"] == "audio"]
imgs = [t["id"] for t in tracks if t["type"] == "image"]
need_overlays = 12
while len(imgs) < need_overlays + 1:
    call("add_track", {"trackType": "image", "position": 0})
    imgs = [t["id"] for t in call("list_tracks") if t["type"] == "image"]
base_track = imgs[-1]           # la de más abajo: fondos
over_tracks = imgs[:-1]         # índice 0 = la de más arriba

voz = media(os.path.join(HERE, "voz.wav")); sfx = media(os.path.join(HERE, "sfx.wav"))
call("add_clip", {"trackId": aud[0], "mediaId": voz, "startTime": 0})
call("add_clip", {"trackId": aud[1], "mediaId": sfx, "startTime": 0})

def add(track, path, start, end):
    before = {c["id"] for c in call("list_clips")}
    call("add_clip", {"trackId": track, "mediaId": media(path), "startTime": round(start, 3)})
    cid = [c["id"] for c in call("list_clips") if c["id"] not in before][0]
    call("trim_clip", {"clipId": cid, "inPoint": 0, "outPoint": round(end - start, 3)})
    return cid

# fondos
for sid in sorted(T):
    if BG.get(sid) is None: continue
    cid = add(base_track, BG[sid], T[sid], END[sid])
    if sid == "10":
        call("set_clip_keyframes", {"clipId": cid, "keyframes": [
            {"id": "z1", "time": 0, "property": "scale.x", "value": 1.0, "easing": "linear"},
            {"id": "z2", "time": round(END["10"] - T["10"], 3), "property": "scale.x", "value": 1.06, "easing": "linear"},
            {"id": "z3", "time": 0, "property": "scale.y", "value": 1.0, "easing": "linear"},
            {"id": "z4", "time": round(END["10"] - T["10"], 3), "property": "scale.y", "value": 1.06, "easing": "linear"}]})

# capas animadas: z alto -> pista más arriba; se reparte sin solapes
busy = {t: [] for t in over_tracks}
LAYERS.sort(key=lambda L: (-L[4], L[0]))
for start, end, path, an, z in LAYERS:
    order = over_tracks[max(0, min(len(over_tracks) - 1, 10 - z)):] + over_tracks
    for tr in order:
        if all(end <= a or start >= b for a, b in busy[tr]):
            busy[tr].append((start, end)); break
    else:
        raise RuntimeError("faltan pistas")
    cid = add(tr, path, start, end)
    call("set_clip_transform", {"clipId": cid, "transform": an.transform()})
    if an.k:
        call("set_clip_keyframes", {"clipId": cid, "keyframes": an.k})
print("capas:", len(LAYERS))

# titulares
HEAD = [
    (0.0, wt("then"), "ATTACKED FOR OIL", "#FFFFFF"),
    (wt("then"), wt("fuel"), "4.5 MILLION\nBARRELS", "#FFD23F"),
    (wt("fuel"), T["02"], "UNTOUCHED", "#FFD23F"),
    (T["02"], T["03"], "1941: OIL EMBARGO", "#FFFFFF"), (T["03"], T["04"], "DUTCH EAST INDIES", "#FFFFFF"),
    (T["04"], T["05"], "U.S. PACIFIC\nFLEET", "#FFFFFF"), (T["05"], T["06"], "BUY TIME", "#FFD23F"),
    (T["06"], T["07"], "7 DECEMBER 1941", "#FFFFFF"),
    (T["07"], wt("carriers", T["07"]) - 0.6, "FUEL + REPAIRS", "#FFD23F"),
    (wt("carriers", T["07"]) - 0.6, T["08"], "CARRIERS\nABSENT", "#FFD23F"),
    (T["08"], T["09"], "KEEP FIGHTING", "#FFFFFF"), (T["09"], T["10"], "FUEL FOR\nA LONG WAR", "#FFD23F"),
    (T["10"], TOTAL + 0.4, "WATCH THE\nFULL STORY", "#FFFFFF"),
]
for s, e, txt, col in HEAD:
    r = call("create_text_clip", {"clip": {"text": txt, "startTime": round(s, 3), "duration": round(e - s, 3), "animation": "pop",
        "style": {"fontFamily": "Inter", "fontSize": 96, "fontWeight": 900, "color": col, "lineHeight": 1.0,
                  "strokeColor": "#000000", "strokeWidth": 9, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r["id"], "updates": {"transform": {"position": {"x": 0.5, "y": 0.14}}}})

# subtítulos de 1-2 palabras
KEY = {"oil", "fuel", "barrels", "million", "untouched", "1941", "embargo", "indonesia", "indies", "fleet", "hawaii",
       "december", "seventh", "devastated", "survived", "carriers", "absent", "fighting", "gamble", "war"}
chunks, cur = [], []
for w in WORDS:
    clean = w["w"].strip(".,'’").lower()
    if cur and (len(cur) >= 2 or len(" ".join(x["w"] for x in cur + [w])) > 13 or w["s"] - cur[-1]["e"] > 0.35
                or clean in KEY or cur[-1]["w"].strip(".,").lower() in KEY):
        chunks.append(cur); cur = []
    cur.append(w)
chunks.append(cur)
for i, ch in enumerate(chunks):
    s = ch[0]["s"]; nxt = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else ch[-1]["e"] + 0.4
    e = min(nxt, ch[-1]["e"] + 0.5)
    txt = " ".join(x["w"] for x in ch).upper().replace("...", "")
    hot = any(x["w"].strip(".,'’").lower() in KEY for x in ch)
    r = call("create_text_clip", {"clip": {"text": txt, "startTime": round(s, 3), "duration": round(max(0.2, e - s), 3),
        "animation": "pop", "style": {"fontFamily": "Inter", "fontSize": 104, "fontWeight": 900,
        "color": "#FFD23F" if hot else "#FFFFFF", "strokeColor": "#000000", "strokeWidth": 11, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r["id"], "updates": {"transform": {"position": {"x": 0.5, "y": 0.70}}}})
print("subtítulos:", len(chunks))
call("save_project")
print("listo")

"""Arma el Short S01 en OpenReel (proyecto ya abierto, 1080x1920) a partir de timeline.json.
Requiere: OpenReel abierto con Scripts/abrir_openreel_local.bat y un http.server en 127.0.0.1:8777
sirviendo la raíz del proyecto."""
import json, sys, os, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "Scripts"))
from openreel_api import call

BASE = "http://127.0.0.1:8777/"
HERE = "Guiones/Shorts/S01 - Fuel Tanks/"
url = lambda p: BASE + urllib.parse.quote(p)
tl = json.load(open(os.path.join(os.path.dirname(__file__), "timeline.json"), encoding="utf-8"))
T = {s["id"]: s for s in tl["timeline"]}
TOTAL = tl["total"]

# ---------- limpiar el proyecto ----------
for c in call("list_clips"):
    if c["trackType"] == "text":
        call("remove_text_clip", {"clipId": c["id"]})
    else:
        call("remove_clip", {"clipId": c["id"]})
for tr in call("list_tracks"):
    try: call("remove_track", {"trackId": tr["id"]})
    except Exception as e: print("track", e)

# ---------- medios ----------
med = {}
for k in "ABCDEFGH":
    med[k] = call("import_media_from_url", {"url": url(f"Imagenes/Shorts/S01/{k}.png"), "name": k})["mediaId"]
med["voz"] = call("import_media_from_url", {"url": url(HERE + "voz.wav"), "name": "voz"})["mediaId"]
med["sfx"] = call("import_media_from_url", {"url": url(HERE + "sfx.wav"), "name": "sfx"})["mediaId"]

for t in ["audio", "audio", "image"]:
    call("add_track", {"trackType": t})
tracks = call("list_tracks")
aud = [t["id"] for t in tracks if t["type"] == "audio"]
img_track = [t["id"] for t in tracks if t["type"] == "image"][0]

call("add_clip", {"trackId": aud[0], "mediaId": med["voz"], "startTime": 0})
call("add_clip", {"trackId": aud[1], "mediaId": med["sfx"], "startTime": 0})

# ---------- escenas: imagen + movimiento ----------
# kf: lista de (t_rel, scale, x, y, easing)  — posición en px respecto al centro
E = "easeInOutCubic"
SCENES = {
    "01": ("A", [(0, 1.45, 170, 330, E), (2.6, 1.52, 170, 330, E), (3.2, 1.40, -150, -230, E), (5.3, 1.48, -150, -230, E)]),
    "02": ("B", [(0, 1.05, 0, 0, E), (4.9, 1.30, 120, -120, E)]),
    "03": ("C", [(0, 1.05, 0, 0, E), (2.0, 1.10, 0, -60, E), (4.8, 1.55, 30, -380, E)]),
    "04": ("D", [(0, 1.05, 0, 0, E), (3.3, 1.35, -300, -40, E)]),
    "05": ("D", [(0, 1.35, -300, -40, E), (1.2, 1.10, 0, 0, E), (4.9, 1.16, 0, 0, E)]),
    "06": ("E", [(0, 1.40, 0, 0, "easeOutExpo"), (0.7, 1.12, 0, 0, E), (4.5, 1.20, 0, 60, E)]),
    "07": ("F", [(0, 1.45, 300, 120, E), (2.2, 1.45, 0, 120, E), (4.0, 1.45, -300, 120, E), (6.3, 1.12, 0, 0, E)]),
    "08": ("G", [(0, 1.05, 0, 0, E), (3.6, 1.28, -150, -60, E)]),
    "09": ("A", [(0, 1.12, 0, 0, E), (4.6, 1.02, 0, 0, E)]),
    "10": ("H", [(0, 1.25, -60, 0, E), (3.6, 1.05, 0, 0, E)]),
}
ids = sorted(SCENES)
for i, sid in enumerate(ids):
    k, kfs = SCENES[sid]
    start = T[sid]["start"]
    end = T[ids[i + 1]]["start"] if i + 1 < len(ids) else TOTAL + 0.4
    call("add_clip", {"trackId": img_track, "mediaId": med[k], "startTime": start})
    clip = [c for c in call("list_clips") if c["trackType"] == "image" and abs(c["startSec"] - start) < 0.01][0]
    call("trim_clip", {"clipId": clip["id"], "inPoint": 0, "outPoint": round(end - start, 3)})
    keys = []
    for n, (t, s, x, y, ez) in enumerate(kfs):
        t = min(t, end - start)
        for prop, v in (("scale.x", s), ("scale.y", s), ("position.x", x), ("position.y", y)):
            keys.append({"id": f"{sid}-{n}-{prop}", "time": t, "property": prop, "value": v, "easing": ez})
    call("set_clip_keyframes", {"clipId": clip["id"], "keyframes": keys})
    print("escena", sid, k, round(start, 2), "->", round(end, 2))

# ---------- titulares (arriba) ----------
HEAD = [
    (0.0, 2.7, "ATTACKED FOR OIL", "#FFFFFF"), (2.75, 5.2, "FUEL TANKS SURVIVED", "#FFD23F"),
    (5.3, 10.0, "1941: OIL EMBARGO", "#FFFFFF"), (10.2, 14.9, "DUTCH EAST INDIES", "#FFFFFF"),
    (15.0, 18.1, "U.S. PACIFIC FLEET", "#FFFFFF"), (18.2, 23.0, "BUY TIME", "#FFD23F"),
    (23.1, 27.4, "7 DECEMBER 1941", "#FFFFFF"), (27.6, 31.2, "FUEL + REPAIRS", "#FFD23F"),
    (31.2, 33.7, "CARRIERS ABSENT", "#FFD23F"), (33.8, 37.3, "KEEP FIGHTING", "#FFFFFF"),
    (37.4, 41.8, "THE BASE STILL WORKED", "#FFD23F"), (41.9, TOTAL + 0.4, "WATCH THE FULL STORY", "#FFFFFF"),
]
for s, e, txt, col in HEAD:
    if len(txt) > 17:  # partir en dos líneas para que no se salga del ancho
        w = txt.split(); h = len(w) // 2 + (len(w) % 2)
        txt = " ".join(w[:h]) + "\n" + " ".join(w[h:])
    r = call("create_text_clip", {"clip": {"text": txt, "startTime": s, "duration": round(e - s, 3), "animation": "pop",
        "style": {"fontFamily": "Inter", "fontSize": 96, "fontWeight": 900, "color": col, "lineHeight": 1.0,
                  "strokeColor": "#000000", "strokeWidth": 9, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r["id"], "updates": {"transform": {"position": {"x": 0.5, "y": 0.14}}}})

# ---------- subtítulos palabra a palabra (centro-abajo) ----------
KEY = {"oil", "fuel", "tanks", "1941", "embargo", "indonesia", "indies", "fleet", "hawaii", "december",
       "seventh", "devastated", "survived", "carriers", "absent", "fighting", "gamble", "war", "standing"}
words = tl["words"]
chunks, cur = [], []
for w in words:
    clean = w["w"].strip(".,'’").lower()
    starts_new = cur and (len(cur) >= 2 or len(" ".join(x["w"] for x in cur + [w])) > 13
                          or w["s"] - cur[-1]["e"] > 0.35 or clean in KEY or cur[-1]["w"].strip(".,").lower() in KEY)
    if starts_new:
        chunks.append(cur); cur = []
    cur.append(w)
chunks.append(cur)
for i, ch in enumerate(chunks):
    s = ch[0]["s"]
    nxt = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else ch[-1]["e"] + 0.4
    e = min(nxt, ch[-1]["e"] + 0.5)
    txt = " ".join(x["w"] for x in ch).upper()
    hot = any(x["w"].strip(".,'’").lower() in KEY for x in ch)
    r = call("create_text_clip", {"clip": {"text": txt, "startTime": round(s, 3), "duration": round(max(0.2, e - s), 3),
        "animation": "pop", "style": {"fontFamily": "Inter", "fontSize": 104, "fontWeight": 900,
        "color": "#FFD23F" if hot else "#FFFFFF", "strokeColor": "#000000", "strokeWidth": 11, "textAlign": "center"}}})
    call("update_text_clip", {"clipId": r["id"], "updates": {"transform": {"position": {"x": 0.5, "y": 0.70}}}})
print("subtítulos:", len(chunks))

# ---------- flecha Japón -> Hawái que se dibuja sola (escena 05) ----------
call("add_track", {"trackType": "image", "position": 0})
over = [t["id"] for t in call("list_tracks") if t["type"] == "image" and t["id"] != img_track][0]
t0 = T["05"]["start"] + 1.25
end5 = T["06"]["start"]
steps = [(1, 0.12), (2, 0.12), (3, 0.12), (4, None)]
t = t0
for k, d in steps:
    mid = call("import_media_from_url", {"url": url(f"Imagenes/Shorts/S01/arrow_{k}.png"), "name": f"arrow_{k}"})["mediaId"]
    call("add_clip", {"trackId": over, "mediaId": mid, "startTime": round(t, 3)})
    c = [c for c in call("list_clips") if c["mediaId"] == mid][0]
    dur = d if d else end5 - t
    call("trim_clip", {"clipId": c["id"], "inPoint": 0, "outPoint": round(dur, 3)})
    call("set_clip_transform", {"clipId": c["id"], "transform": {"fitMode": "contain"}})
    if not d:  # acompaña el zoom lento de la imagen (1.11 -> 1.16)
        call("set_clip_keyframes", {"clipId": c["id"], "keyframes": [
            {"id": "a1", "time": 0, "property": "scale.x", "value": 1.0, "easing": E},
            {"id": "a2", "time": round(dur, 3), "property": "scale.x", "value": 1.045, "easing": E},
            {"id": "a3", "time": 0, "property": "scale.y", "value": 1.0, "easing": E},
            {"id": "a4", "time": round(dur, 3), "property": "scale.y", "value": 1.045, "easing": E}]})
    t += d if d else 0
print("flecha lista")
call("save_project")
print("listo")

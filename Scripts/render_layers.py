"""Render propio de las capas animadas (alternativa a OpenReel para videos largos).
Uso: python render_layers.py render_spec.json salida.mp4 voz.wav sfx.wav [--from S --to S] [--workers N]
render_spec.json lo escribe build.py --render: fondos (con temblor), capas PNG de pantalla completa con
keyframes estilo OpenReel (position.x/y = desplazamiento desde el centro, scale.x/y, rotation, opacity) y textos.
Cada worker renderiza un tramo contiguo y lo codifica con ffmpeg; luego se concatenan y se mezcla el audio.
"""
import json, math, os, subprocess, sys, tempfile
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\ariblk.ttf"
FPS = 30

# ---------------- easing ----------------
def ease(name, x):
    x = min(1.0, max(0.0, x))
    if name == "easeOutBack":
        c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if name == "easeInBack":
        c1 = 1.70158; c3 = c1 + 1; return c3 * x ** 3 - c1 * x ** 2
    if name == "easeInOutSine": return -(math.cos(math.pi * x) - 1) / 2
    if name == "easeInOutCubic": return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    if name == "easeOutCubic": return 1 - (1 - x) ** 3
    if name == "easeInCubic": return x ** 3
    if name == "easeOutQuad": return 1 - (1 - x) ** 2
    if name == "easeInQuad": return x ** 2
    return x

def tracks(keys):
    tr = {}
    for k in keys: tr.setdefault(k["property"], []).append((k["time"], k["value"], k.get("easing", "linear")))
    for p in tr: tr[p].sort(key=lambda a: a[0])
    return tr

def val(tr, prop, t, default):
    ks = tr.get(prop)
    if not ks: return default
    if t <= ks[0][0]: return ks[0][1]
    if t >= ks[-1][0]: return ks[-1][1]
    for (t0, v0, _), (t1, v1, e1) in zip(ks, ks[1:]):
        if t0 <= t <= t1:
            if t1 - t0 < 1e-6: return v1
            return v0 + (v1 - v0) * ease(e1, (t - t0) / (t1 - t0))
    return ks[-1][1]

# ---------------- worker ----------------
SPEC = None; CACHE = {}; TXT = {}
def init(spec_path):
    global SPEC
    SPEC = json.load(open(spec_path, encoding="utf-8"))
    for L in SPEC["layers"]: L["tr"] = tracks(L["k"])
    for B in SPEC["bg"]: B["tr"] = tracks(B["k"])
    SPEC["layers"].sort(key=lambda L: (L["z"], L["s"]))

def load_layer(path, cx, cy):
    key = (path, cx, cy)
    if key not in CACHE:
        im = Image.open(path).convert("RGBA"); bb = im.getbbox()
        if not bb: CACHE[key] = None; return None
        crop = im.crop(bb)
        hw = int(math.ceil(max(abs(bb[0] - cx), abs(bb[2] - cx)))) + 2
        hh = int(math.ceil(max(abs(bb[1] - cy), abs(bb[3] - cy)))) + 2
        pad = Image.new("RGBA", (2 * hw, 2 * hh), (0, 0, 0, 0))
        pad.alpha_composite(crop, (int(bb[0] - cx + hw), int(bb[1] - cy + hh)))
        CACHE[key] = (im, crop, bb, pad)
    return CACHE[key]

def text_img(T):
    key = (T["t"], T["size"], T["col"], T["stroke"], T["scol"])
    if key not in TXT:
        f = ImageFont.truetype(FONT, int(T["size"] * 0.92))
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = d.multiline_textbbox((0, 0), T["t"], font=f, stroke_width=T["stroke"], align="center", spacing=4)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).multiline_text((4 - bb[0], 4 - bb[1]), T["t"], font=f, fill=T["col"], stroke_width=T["stroke"],
                                          stroke_fill=T["scol"], align="center", spacing=4)
        TXT[key] = im
    return TXT[key]

def frame(t):
    W, H = SPEC["W"], SPEC["H"]
    can = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    for B in SPEC["bg"]:
        if B["s"] <= t < B["e"]:
            im = load_layer(B["path"], W / 2, H / 2)[0]; lt = t - B["s"]
            dx = val(B["tr"], "position.x", lt, 0); dy = val(B["tr"], "position.y", lt, 0)
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                s = 1.04; big = im.resize((int(W * s), int(H * s)))  # leve zoom para que el temblor no deje bordes
                can.alpha_composite(big, (int((W - big.width) / 2 + dx), int((H - big.height) / 2 + dy)))
            else:
                can.alpha_composite(im)
            break
    for L in SPEC["layers"]:
        if not (L["s"] <= t < L["e"]): continue
        c = load_layer(L["path"], L["cx"], L["cy"])
        if c is None: continue
        im, crop, bb, pad = c; lt = t - L["s"]; tr = L["tr"]; cx, cy = L["cx"], L["cy"]
        dx = val(tr, "position.x", lt, cx - W / 2) - (cx - W / 2)
        dy = val(tr, "position.y", lt, cy - H / 2) - (cy - H / 2)
        sx = val(tr, "scale.x", lt, 1.0); sy = val(tr, "scale.y", lt, 1.0)
        rot = val(tr, "rotation", lt, 0.0); op = val(tr, "opacity", lt, 1.0)
        if sx <= 0.01 or sy <= 0.01 or op <= 0.01: continue
        if abs(sx - 1) < 1e-3 and abs(sy - 1) < 1e-3 and abs(rot) < 0.05:
            el = crop; x0, y0 = bb[0] + dx, bb[1] + dy
        else:
            el = pad
            if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3:
                el = el.resize((max(1, int(el.width * abs(sx))), max(1, int(el.height * abs(sy)))), Image.BILINEAR)
            if abs(rot) >= 0.05: el = el.rotate(-rot, resample=Image.BILINEAR, expand=True)
            x0, y0 = cx + dx - el.width / 2, cy + dy - el.height / 2
        if op < 0.999:
            a = el.getchannel("A").point(lambda v: int(v * op)); el = el.copy(); el.putalpha(a)
        x0, y0 = int(round(x0)), int(round(y0))
        if x0 >= W or y0 >= H or x0 + el.width <= 0 or y0 + el.height <= 0: continue
        sx0, sy0 = max(0, -x0), max(0, -y0)
        el2 = el.crop((sx0, sy0, min(el.width, W - x0), min(el.height, H - y0)))
        can.alpha_composite(el2, (x0 + sx0, y0 + sy0))
    for T in SPEC["texts"]:
        if not (T["s"] <= t < T["e"]): continue
        im = text_img(T); lt = t - T["s"]
        if lt < 0.22:
            k = ease("easeOutBack", lt / 0.22); k = max(0.05, k)
            im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
        x0 = int(T["x"] * W - im.width / 2); y0 = int(T["y"] * H - im.height / 2)
        x0 = max(-im.width + 1, min(W - 1, x0)); y0 = max(-im.height + 1, min(H - 1, y0))
        sx0, sy0 = max(0, -x0), max(0, -y0)
        can.alpha_composite(im.crop((sx0, sy0, min(im.width, W - x0), min(im.height, H - y0))), (x0 + sx0, y0 + sy0))
    return can.convert("RGB")

def seg(args):
    i, f0, f1, out = args
    W, H = SPEC["W"], SPEC["H"]
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - f0) % 300 == 0: print(f"seg{i}: {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close(); p.wait()
    return out

if __name__ == "__main__":
    spec_path, out, voz, sfx = sys.argv[1:5]
    a = sys.argv
    t_from = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    sp = json.load(open(spec_path, encoding="utf-8"))
    t_to = float(a[a.index("--to") + 1]) if "--to" in a else sp["total"] + 0.6
    nw = int(a[a.index("--workers") + 1]) if "--workers" in a else 7
    F0, F1 = int(t_from * FPS), int(t_to * FPS)
    tmp = tempfile.mkdtemp(prefix="wm_render_")
    step = math.ceil((F1 - F0) / nw)
    jobs = [(i, F0 + i * step, min(F1, F0 + (i + 1) * step), os.path.join(tmp, f"s{i:02d}.mp4")) for i in range(nw) if F0 + i * step < F1]
    with Pool(len(jobs), initializer=init, initargs=(spec_path,)) as pool:
        parts = pool.map(seg, jobs)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "video.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", vid, "-ss", str(t_from), "-t", str(t_to - t_from), "-i", voz,
                    "-ss", str(t_from), "-t", str(t_to - t_from), "-i", sfx,
                    "-filter_complex", "[1:a][2:a]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print("listo", out)

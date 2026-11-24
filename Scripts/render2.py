"""Render v2: movimiento suave sin temblor (transformación sub-píxel cuadro a cuadro),
fuego que se mueve, agua que ondula, aviones que se balancean, efectos de sonido y subtítulos palabra por palabra.
Uso: python render2.py guion.json carpeta_imagenes carpeta_audios salida.mp4
Cada escena del guion puede tener "fx": ["fire", "water", "planes", "wind"].
"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image

FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
FFMPEG, FFPROBE = os.path.join(FF, "ffmpeg.exe"), os.path.join(FF, "ffprobe.exe")
W, H, FPS = 1920, 1080, 30
X = 0.6      # fundido entre escenas
LEAD, TAIL = 0.30, 0.45
SR = 48000

g = json.load(open(sys.argv[1], encoding="utf-8"))
IMG, AUD, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
work = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_work_" + os.path.splitext(os.path.basename(OUT))[0])
os.makedirs(work, exist_ok=True)
rng = np.random.default_rng(7)

def dur(f):
    return float(subprocess.check_output([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

scenes = g["scenes"]
ad = [dur(f"{AUD}/{s['id']}.mp3") for s in scenes]
L = [a + LEAD + TAIL + X for a in ad]
L[-1] += 1.5
starts, t = [], 0.0
for l in L:
    starts.append(t); t += l - X
total = t + X

def ease(u):
    return u * u * (3 - 2 * u)  # smoothstep

# ---------- 1) clips de video ----------
def masks_for(arr):
    """Máscaras (0..1) de fuego (naranja/amarillo) y agua (azul) sobre la imagen grande."""
    a = arr.astype(np.float32) / 255
    r, gg, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / (mx + 1e-5)
    fire = ((r > 0.75) & (gg > 0.25) & (gg < 0.85) & (b < 0.45) & (sat > 0.45)).astype(np.float32)
    water = ((b > 0.55) & (b > r + 0.12) & (sat > 0.18)).astype(np.float32)
    return fire, water

def blur(m, k=9):
    im = Image.fromarray((m * 255).astype(np.uint8))
    from PIL import ImageFilter
    return np.asarray(im.filter(ImageFilter.GaussianBlur(k)), dtype=np.float32) / 255

def render_clip(i, s):
    out = f"{work}/{s['id']}.mp4"
    if os.environ.get("REUSE_CLIPS") and os.path.exists(out):
        return
    fx = set(s.get("fx", []))
    src = Image.open(f"{IMG}/{s['id']}.jpg").convert("RGB")
    big = src.resize((W + W // 8, H + H // 8), Image.LANCZOS)  # margen para el movimiento
    BW, BH = big.size
    base = np.asarray(big)
    fire_m, water_m = masks_for(base)
    fire_soft = blur(np.clip(fire_m * 1.0, 0, 1), 6) if "fire" in fx else None
    water_soft = blur(water_m, 4) if "water" in fx else None
    n = int(round(L[i] * FPS))
    mode = ["in", "out", "panl", "in", "panr", "out"][i % 6]
    proc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    for f in range(n):
        tt = f / FPS
        u = ease(f / max(n - 1, 1))
        frame = base
        if fire_soft is not None:
            # llamas: ondulan hacia arriba y parpadean
            dy = (np.sin(xx * 0.045 + tt * 9.0) * 5 + np.sin(xx * 0.11 - tt * 13.0) * 3) * fire_soft
            dx = np.sin(yy * 0.06 + tt * 7.0) * 3 * fire_soft
            sy = np.clip(yy + dy + 4 * fire_soft, 0, BH - 1).astype(np.int32)
            sx = np.clip(xx + dx, 0, BW - 1).astype(np.int32)
            warped = base[sy, sx].astype(np.float32)
            flick = 1.0 + 0.10 * np.sin(tt * 17.0) + 0.06 * np.sin(tt * 29.0 + 1.3)
            warped *= (1 + (flick - 1) * fire_soft[..., None])
            frame = np.clip(warped, 0, 255).astype(np.uint8)
        if water_soft is not None:
            dx = np.sin(yy * 0.08 + tt * 2.2) * 2.5 * water_soft
            sx = np.clip(xx + dx, 0, BW - 1).astype(np.int32)
            frame = frame[yy.astype(np.int32), sx]
        img = Image.fromarray(frame) if frame is not base else big
        # zoom/paneo con transformación afín en coma flotante (sin saltos de píxel)
        if mode == "in":
            z = 1.0 + 0.04 * u; cx, cy = 0.5, 0.5
        elif mode == "out":
            z = 1.04 - 0.04 * u; cx, cy = 0.5, 0.5
        elif mode == "panl":
            z = 1.03; cx, cy = 0.514 - 0.028 * u, 0.5
        else:
            z = 1.03; cx, cy = 0.486 + 0.028 * u, 0.5
        if "planes" in fx:  # leve balanceo vertical, muy suave (no temblor)
            cy += 0.004 * np.sin(tt * 1.6)
        vw, vh = BW / z, BH / z  # ventana visible: con z=1 se ve la imagen completa (sin recortar bordes)
        x0 = cx * BW - vw / 2; y0 = cy * BH - vh / 2
        x0 = min(max(x0, 0), BW - vw); y0 = min(max(y0, 0), BH - vh)
        sxs, sys_ = vw / W, vh / H
        fr = img.transform((W, H), Image.AFFINE, (sxs, 0, x0, 0, sys_, y0), resample=Image.BICUBIC)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close(); proc.wait()
    print("clip", s["id"], f"{L[i]:.2f}s", sorted(fx), flush=True)

for i, s in enumerate(scenes):
    render_clip(i, s)

# ---------- 2) efectos de sonido (generados por código, sin licencias) ----------
def lp(x, a):  # filtro paso bajo simple
    y = np.empty_like(x); acc = 0.0
    for k in range(len(x)):
        acc += a * (x[k] - acc); y[k] = acc
    return y

def lp_fast(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)

def sfx_fire(d):
    n = int(d * SR); base = lp_fast(rng.standard_normal(n), 0.05) * 0.35
    cr = np.zeros(n)
    for _ in range(int(d * 14)):
        p = rng.integers(0, n - 400); ln = rng.integers(40, 300)
        cr[p:p + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / (ln / 4)) * rng.uniform(0.3, 0.9)
    return base + cr * 0.5

def sfx_water(d):
    n = int(d * SR); tt = np.arange(n) / SR
    x = lp_fast(rng.standard_normal(n), 0.02)
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.18 * tt)) * 0.9

def sfx_wind(d):
    n = int(d * SR); tt = np.arange(n) / SR
    x = lp_fast(rng.standard_normal(n), 0.008)
    return x * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt + 1)) * 2.2

def sfx_planes(d):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 92 + 4 * np.sin(2 * np.pi * 0.3 * tt)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sign(np.sin(ph)) * 0.25 + np.sin(2 * ph) * 0.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt))
    return lp_fast(x + 0.15 * rng.standard_normal(n), 0.08) * 0.8

def whoosh(d=0.7):
    n = int(d * SR); x = rng.standard_normal(n)
    env = np.sin(np.pi * np.arange(n) / n) ** 2
    out = np.zeros(n); a0, a1 = 0.01, 0.25
    seg = 8
    for k in range(seg):
        s0, s1 = k * n // seg, (k + 1) * n // seg
        out[s0:s1] = lp_fast(x[s0:s1], a0 + (a1 - a0) * k / seg)
    return out * env * 0.6

GEN = {"fire": sfx_fire, "water": sfx_water, "wind": sfx_wind, "planes": sfx_planes}
VOL = {"fire": 0.22, "water": 0.16, "wind": 0.12, "planes": 0.14}
N = int((total + 1) * SR)
bed = np.zeros(N)
for i, s in enumerate(scenes):
    for fx in s.get("fx", []):
        if fx in GEN:
            d = L[i]; x = GEN[fx](d)
            x = x / (np.abs(x).max() + 1e-9) * VOL[fx]
            fade = np.minimum(1, np.minimum(np.arange(len(x)), np.arange(len(x))[::-1]) / (0.6 * SR))
            p = int(starts[i] * SR); bed[p:p + len(x)] += (x * fade)[:N - p]
    if i > 0:
        w = whoosh(); w = w / (np.abs(w).max() + 1e-9) * 0.10
        p = int((starts[i] - 0.15) * SR); bed[p:p + len(w)] += w[:N - p]
bed = np.clip(bed, -1, 1)
with wave.open(f"{work}/sfx.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((bed * 32767).astype(np.int16).tobytes())

# ---------- 3) subtítulos ----------
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def srt_ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

import re
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Arial Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,2,80,80,70,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
srt, k = [], 1
for i, s in enumerate(scenes):
    words = json.load(open(f"{AUD}/{s['id']}.words.json", encoding="utf-8"))
    # fines de frase: palabras del texto que terminan en . , ? ! :
    ends = set()
    toks = s["text"].split()
    wi = 0
    for tok in toks:
        if wi >= len(words): break
        # avanzar palabras de edge-tts que caben en este token
        if re.search(r"[.,?!:;]$", tok):
            # buscar la palabra de edge-tts cuyo texto termina este token
            core = re.sub(r"[^\w']", "", tok.split()[-1]).lower()
            for j in range(wi, min(wi + 4, len(words))):
                if re.sub(r"[^\w']", "", words[j]["w"].split()[-1]).lower() == core:
                    ends.add(j); wi = j + 1; break
        else:
            core = re.sub(r"[^\w']", "", tok).lower()
            for j in range(wi, min(wi + 4, len(words))):
                if re.sub(r"[^\w']", "", words[j]["w"].split()[-1]).lower() == core:
                    wi = j + 1; break
    base = starts[i] + LEAD
    groups, cur = [], []
    for j, w in enumerate(words):
        cur.append(w)
        if j in ends or len(cur) >= 4 or (len(cur) >= 3 and len(" ".join(x["w"] for x in cur)) > 18):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    for gi, grp in enumerate(groups):
        g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else grp[-1]["e"] + 0.25
        for wi2, w in enumerate(grp):
            w_end = grp[wi2 + 1]["s"] if wi2 + 1 < len(grp) else g_end
            txt = " ".join(("{\\c&H00D7FF&\\fscx108\\fscy108}" + x["w"].upper() + "{\\c&HFFFFFF&\\fscx100\\fscy100}") if j == wi2 else x["w"].upper()
                           for j, x in enumerate(grp))
            ass.append(f"Dialogue: 0,{ts(base + w['s'])},{ts(base + w_end)},Sub,,0,0,0,,{txt}")
        srt.append(f"{k}\n{srt_ts(base + grp[0]['s'])} --> {srt_ts(base + g_end)}\n{' '.join(x['w'] for x in grp)}\n"); k += 1
open(f"{work}/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")
open(OUT.replace(".mp4", ".srt"), "w", encoding="utf-8").write("\n".join(srt))

# ---------- 4) montaje final ----------
lst = f"{work}/xf.txt"
args = [FFMPEG, "-y", "-v", "error"]
for s in scenes:
    args += ["-i", f"{work}/{s['id']}.mp4"]
for s in scenes:
    args += ["-i", f"{AUD}/{s['id']}.mp3"]
args += ["-i", f"{work}/sfx.wav"]
n = len(scenes)
fc, prev, off = [], "0:v", 0.0
for i in range(1, n):
    off += L[i - 1] - X
    fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[v{i}]"); prev = f"v{i}"
mix = []
for i in range(n):
    d = int((starts[i] + LEAD) * 1000)
    fc.append(f"[{n+i}:a]aresample={SR},adelay={d}|{d}[a{i}]"); mix.append(f"[a{i}]")
fc.append("".join(mix) + f"amix=inputs={n}:normalize=0[voice]")
fc.append(f"[{2*n}:a]aresample={SR},pan=stereo|c0=c0|c1=c0[fx]")
fc.append(f"[voice][fx]amix=inputs=2:normalize=0,apad,atrim=0:{total:.3f},alimiter=limit=0.95[aout]")
sub_path = f"{work}/subs.ass".replace("\\", "/").replace(":", "\\:")
fc.append(f"[{prev}]ass='{sub_path}',fade=t=in:st=0:d=0.6,fade=t=out:st={total-1.0:.3f}:d=1.0[vout]")
args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(args, check=True)
print("OK", OUT, f"{total:.1f}s")

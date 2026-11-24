"""Arma el video: imágenes con zoom suave (Ken Burns), fundidos, voz por escena y subtítulos palabra por palabra.
Uso: python render.py guion.json carpeta_imagenes carpeta_audios salida.mp4
"""
import json, os, subprocess, sys

FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
FFMPEG, FFPROBE = os.path.join(FF, "ffmpeg.exe"), os.path.join(FF, "ffprobe.exe")
W, H, FPS = 1920, 1080, 30
X = 0.5      # duración del fundido entre escenas
LEAD = 0.30  # silencio antes de que hable en cada escena
TAIL = 0.45  # silencio después

g = json.load(open(sys.argv[1], encoding="utf-8"))
IMG, AUD, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
work = os.path.join(os.path.dirname(os.path.abspath(OUT)), "_work")
os.makedirs(work, exist_ok=True)

def dur(f):
    return float(subprocess.check_output([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

scenes = g["scenes"]
ad = [dur(f"{AUD}/{s['id']}.mp3") for s in scenes]
L = [a + LEAD + TAIL + X for a in ad]
L[-1] += 1.5  # cierre
starts, t = [], 0.0
for i, l in enumerate(L):
    starts.append(t)
    t += l - X
total = t + X

# 1) Clips por escena con movimiento suave
moves = ["in", "out", "left", "in", "right", "out"]
for i, s in enumerate(scenes):
    out = f"{work}/{s['id']}.mp4"
    n = int(round(L[i] * FPS))
    if os.environ.get("REUSE_CLIPS") and os.path.exists(out):
        continue
    m = moves[i % len(moves)]
    z0, z1 = (1.0, 1.12) if m in ("in", "left", "right") else (1.12, 1.0)
    zexpr = f"{z0}+({z1}-{z0})*(on/{n})"
    if m == "left":
        xexpr = f"(iw-iw/zoom)*(0.65-0.3*on/{n})"
    elif m == "right":
        xexpr = f"(iw-iw/zoom)*(0.35+0.3*on/{n})"
    else:
        xexpr = "(iw-iw/zoom)/2"
    yexpr = "(ih-ih/zoom)/2"
    vf = (f"scale={W*2}:{H*2}:flags=lanczos,setsar=1,"
          f"zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':d={n}:s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    img = f"{IMG}/{s['id']}.jpg"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{L[i]:.3f}", "-i", img,
                    "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "medium", "-crf", "18", out], check=True)
    print("clip", s["id"], f"{L[i]:.2f}s", flush=True)

# 2) Subtítulos ASS con la palabra actual resaltada
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def srt_ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Arial Black,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,3,2,80,80,70,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
srt, k = [], 1
for i, s in enumerate(scenes):
    words = json.load(open(f"{AUD}/{s['id']}.words.json", encoding="utf-8"))
    base = starts[i] + LEAD
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or (len(cur) >= 3 and len(" ".join(x["w"] for x in cur)) > 18):
            groups.append(cur); cur = []
    if cur:
        if groups and len(cur) == 1:
            groups[-1] += cur
        else:
            groups.append(cur)
    for gi, grp in enumerate(groups):
        g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else grp[-1]["e"] + 0.25
        for wi, w in enumerate(grp):
            w_end = grp[wi + 1]["s"] if wi + 1 < len(grp) else g_end
            txt = " ".join(("{\\c&H00D7FF&\\fscx108\\fscy108}" + x["w"].upper() + "{\\c&HFFFFFF&\\fscx100\\fscy100}") if j == wi else x["w"].upper()
                           for j, x in enumerate(grp))
            ass.append(f"Dialogue: 0,{ts(base + w['s'])},{ts(base + w_end)},Sub,,0,0,0,,{txt}")
        srt.append(f"{k}\n{srt_ts(base + grp[0]['s'])} --> {srt_ts(base + g_end)}\n{' '.join(x['w'] for x in grp)}\n"); k += 1
open(f"{work}/subs.ass", "w", encoding="utf-8").write("\n".join(ass) + "\n")
open(OUT.replace(".mp4", ".srt"), "w", encoding="utf-8").write("\n".join(srt))

# 3) Unir clips con fundidos + audio + subtítulos
args = [FFMPEG, "-y", "-v", "error"]
for s in scenes:
    args += ["-i", f"{work}/{s['id']}.mp4"]
for s in scenes:
    args += ["-i", f"{AUD}/{s['id']}.mp3"]
fc, prev, off = [], "0:v", 0.0
for i in range(1, len(scenes)):
    off += L[i - 1] - X
    lab = f"v{i}"
    fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[{lab}]")
    prev = lab
n = len(scenes)
amix = []
for i in range(n):
    d = int((starts[i] + LEAD) * 1000)
    fc.append(f"[{n+i}:a]aresample=48000,adelay={d}|{d}[a{i}]")
    amix.append(f"[a{i}]")
fc.append("".join(amix) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{total:.3f}[aout]")
sub_path = f"{work}/subs.ass".replace("\\", "/").replace(":", "\\:")
fc.append(f"[{prev}]ass='{sub_path}',fade=t=in:st=0:d=0.6,fade=t=out:st={total-1.0:.3f}:d=1.0[vout]")
args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(args, check=True)
print("OK", OUT, f"{total:.1f}s")

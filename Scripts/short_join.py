"""Une las voces por escena de un Short y escribe voz.wav + timeline.json.
Uso: python short_join.py carpeta_del_short   (lee audio/NN.mp3 + NN.words.json)
Cada escena se recorta al final de su última palabra + 0.22 s y se separa con 0.18 s.
"""
import json, os, subprocess, sys

FF = r"C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
TAIL, GAP = 0.22, 0.18

d = sys.argv[1]
g = json.load(open(f"{d}/guion.json", encoding="utf-8"))
timeline, words, t = [], [], 0.0
parts = []
for s in g["scenes"]:
    w = json.load(open(f"{d}/audio/{s['id']}.words.json", encoding="utf-8"))
    dur = round(w[-1]["e"] + TAIL, 3)
    timeline.append({"id": s["id"], "start": round(t, 3), "dur": round(dur + GAP, 3)})
    for x in w:
        words.append({"w": x["w"], "s": round(t + x["s"], 3), "e": round(t + x["e"], 3), "scene": s["id"]})
    parts.append((f"{d}/audio/{s['id']}.mp3", dur))
    t += dur + GAP
total = round(t - GAP, 3)

inputs, filt = [], []
for i, (p, dur) in enumerate(parts):
    inputs += ["-i", p]
    pad = 0 if i == len(parts) - 1 else GAP
    filt.append(f"[{i}:a]atrim=0:{dur},asetpts=PTS-STARTPTS,aresample=48000,apad=pad_dur={pad}[a{i}]")
filt.append("".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
subprocess.run([FF, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ac", "1", f"{d}/voz.wav"], check=True)
json.dump({"timeline": timeline, "words": words, "total": total}, open(f"{d}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", total)
for s in timeline: print(s["id"], s["start"])

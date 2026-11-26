"""Video 7 — Israel, Palestina e Irán (1920x1080). Motor: engine.py · escenas: storyboard.py
python build.py --prep                 recortes de stickers
python build.py --frame 1.2 ...        cuadros de prueba
python build.py --sheet 101 102 ...    hoja de miniaturas (o --sheet all / --sheet CAP)
python build.py [--from S --to S]      sfx.wav + Render/Video7_MiddleEast.mp4
"""
import json, math, os, subprocess, sys
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import engine as E
import storyboard  # noqa: F401  (llena E.STORY)
E.plan_fx()
frame, seg = E.frame, E.seg
ROOT = E.ROOT; FF = E.FF; FPS = E.FPS

if __name__ == "__main__":
    a = sys.argv
    if "--prep" in a: E.prep(); sys.exit()
    if "--frame" in a:
        for v in a[a.index("--frame") + 1:]: frame(float(v)).save(os.path.join(E.PREP, f"test_{float(v):07.2f}.jpg"), quality=85)
        sys.exit()
    if "--sheet" in a:
        ids = a[a.index("--sheet") + 1:]
        if ids == ["all"]: ids = E.ORDER
        elif len(ids) == 1 and len(ids[0]) == 1: ids = [s for s in E.ORDER if s.startswith(ids[0])]
        E.sheet(ids, os.path.join(E.PREP, f"sheet_{ids[0]}_{ids[-1]}.jpg")); sys.exit()
    json.dump({"music": True, "bpm": 88, "music_vol": 0.06, "whoosh_cuts": True, "events": E.SFX}, open(os.path.join(HERE, "sfx.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "short_sfx.py"), HERE], check=True)
    t0 = float(a[a.index("--from") + 1]) if "--from" in a else 0.0; t1 = float(a[a.index("--to") + 1]) if "--to" in a else E.TOTAL
    F0, F1 = int(t0 * FPS), int(t1 * FPS); nw = 7; step = math.ceil((F1 - F0) / (nw * 6))
    tmp = os.path.join(HERE, f"_v7_{os.getpid()}"); os.makedirs(tmp, exist_ok=True)
    jobs = [(i, f, min(F1, f + step), os.path.join(tmp, f"s{i:03d}.mp4")) for i, f in enumerate(range(F0, F1, step))]
    with Pool(nw) as pool: parts = pool.map(seg, jobs, chunksize=1)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(tmp, "video.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    out = os.path.join(ROOT, "Render", "Video7_MiddleEast.mp4" if "--from" not in a else f"Video7_parte_{int(t0)}.mp4")
    mux_inputs = ["-i", vid, "-ss", str(t0), "-i", os.path.join(HERE, "voz.wav"), "-ss", str(t0), "-i", os.path.join(HERE, "sfx.wav")]
    mix = f"[1:a]apad[v];[v][2:a]amix=inputs=2:normalize=0:duration=longest,atrim=duration={t1 - t0}"
    meas = subprocess.run([FF, "-hide_banner", "-nostats", *mux_inputs, "-filter_complex", mix + ",loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[a]",
                           "-map", "[a]", "-vn", "-f", "null", "-"], capture_output=True, text=True, check=True)
    m = json.loads(meas.stderr[meas.stderr.rfind("{"):meas.stderr.rfind("}") + 1]); off = float(m["target_offset"])
    for _ in range(6):
        norm = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                f"measured_thresh={m['input_thresh']}:offset={off}:linear=true:print_format=json")
        mux = subprocess.run([FF, "-y", "-hide_banner", "-nostats", *mux_inputs, "-filter_complex", mix + "," + norm + "[a]", "-map", "0:v", "-map", "[a]",
                              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", str(t1 - t0), out], capture_output=True, text=True, check=True)
        ap = json.loads(mux.stderr[mux.stderr.rfind("{"):mux.stderr.rfind("}") + 1]); err = -14 - float(ap["output_i"])
        print("loudnorm", ap["output_i"], flush=True)
        if abs(err) <= 0.45: break
        off += err
    print("listo", out)

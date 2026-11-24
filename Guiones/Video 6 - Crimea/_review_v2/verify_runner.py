"""Verify the completed MP4, extract timestamped review sheets, and encode upload."""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import traceback

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
REVIEW = HERE / "_review_v2"
REVIEW.mkdir(exist_ok=True)
STATUS = REVIEW / "verification_status.json"
MASTER = ROOT / "Render" / "Video6_Crimea.mp4"
UPLOAD = ROOT / "Render" / "Video6_Crimea_upload.mp4"
tree = ast.parse((HERE / "build.py").read_text(encoding="utf-8"))
FF = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == "FF" for t in n.targets))
PROBE = str(Path(FF).with_name("ffprobe.exe"))
state = {"started": datetime.now().astimezone().isoformat(), "status": "running"}


def save_status(**items):
    state.update(items)
    STATUS.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_logged(args, log):
    with (REVIEW / log).open("w", encoding="utf-8") as stream:
        subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, check=True)


def probe(path):
    result = subprocess.run([PROBE, "-v", "error", "-show_format", "-show_streams",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    (REVIEW / (path.stem + "_ffprobe.json")).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def loudness(path, name):
    log = name + "_ebur128.log"
    run_logged([FF, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128",
                "-f", "null", "-"], log)
    text = (REVIEW / log).read_text(encoding="utf-8")
    return float(re.findall(r"I:\s*(-?[\d.]+) LUFS", text)[-1])


def integrity(path, name):
    log = name + "_decode.log"
    run_logged([FF, "-hide_banner", "-v", "error", "-xerror", "-i", str(path),
                "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], log)
    return {"exit_code": 0, "log_bytes": (REVIEW / log).stat().st_size}


def extract_sheets(duration):
    times = sorted(set([float(t) for t in range(1, math.ceil(duration), 8)]
                       + [0.5, 1.2, 1.8, 2.6, 3.4, 328.7, 330.0, 347.5, 348.5]))
    entries = []
    for index, timestamp in enumerate(times):
        path = REVIEW / f"frame_{timestamp:08.3f}.jpg"
        run_logged([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}",
                    "-i", str(MASTER), "-frames:v", "1", "-vf", "scale=960:540",
                    "-q:v", "2", "-update", "1", str(path)], "frame_extract.log")
        with Image.open(path) as im:
            assert im.size == (960, 540), (path, im.size)
        entries.append({"seconds": timestamp, "file": str(path), "sheet": index // 12 + 1,
                        "tile": index % 12 + 1})
        print(f"Review frame {index + 1}/{len(times)}: {timestamp:.3f}s", flush=True)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28)
    sheets = []
    for start in range(0, len(entries), 12):
        sheet = Image.new("RGB", (3840, 1740), (18, 22, 28))
        draw = ImageDraw.Draw(sheet)
        for tile, entry in enumerate(entries[start:start + 12]):
            x, y = (tile % 4) * 960, (tile // 4) * 580
            with Image.open(entry["file"]) as frame:
                sheet.paste(frame, (x, y + 40))
            timestamp = entry["seconds"]
            stamp = f"{int(timestamp // 60):02d}:{timestamp % 60:06.3f}  |  t={timestamp:.3f}s"
            draw.text((x + 12, y + 4), stamp, font=font, fill="white")
        path = REVIEW / f"sheet_{start // 12 + 1:02d}.jpg"
        sheet.save(path, quality=93, subsampling=0)
        sheets.append(str(path))
    (REVIEW / "frames_manifest.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return {"frame_count": len(entries), "sheets": sheets, "timestamps": times}


def upload():
    run_logged([FF, "-y", "-hide_banner", "-i", str(MASTER), "-map", "0:v:0", "-map", "0:a:0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-movflags", "+faststart",
                "-progress", str(REVIEW / "upload_progress.txt"), str(UPLOAD)], "upload_encode.log")
    return probe(UPLOAD)


def boxes(path):
    result = []
    with path.open("rb") as stream:
        while stream.tell() < path.stat().st_size:
            offset = stream.tell()
            header = stream.read(8)
            size, kind = struct.unpack(">I4s", header)
            if size == 1:
                size = struct.unpack(">Q", stream.read(8))[0]
            if size == 0:
                size = path.stat().st_size - offset
            result.append({"type": kind.decode("ascii"), "offset": offset, "size": size})
            stream.seek(offset + size)
    return result


if __name__ == "__main__":
    save_status()
    try:
        render = json.loads((REVIEW / "render_status.json").read_text(encoding="utf-8"))
        assert render["status"] == "completed" and render["exit_code"] == 0, render
        assert "listo " in (REVIEW / "render.log").read_text(encoding="utf-8")
        master = probe(MASTER)
        duration = float(master["format"]["duration"])
        report = {"master": master, "render": render}
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {
                "master_lufs": pool.submit(loudness, MASTER, "master"),
                "master_integrity": pool.submit(integrity, MASTER, "master"),
                "review": pool.submit(extract_sheets, duration),
                "upload": pool.submit(upload),
            }
            for name, future in jobs.items():
                report[name] = future.result()
                save_status(completed_tasks=list(report))
        report["upload_lufs"] = loudness(UPLOAD, "upload")
        report["upload_integrity"] = integrity(UPLOAD, "upload")
        for name, path in (("master", MASTER), ("upload", UPLOAD)):
            report[name + "_size_bytes"] = path.stat().st_size
            report[name + "_mp4_boxes"] = boxes(path)
            media = report[name]
            video = next(s for s in media["streams"] if s["codec_type"] == "video")
            audio = next(s for s in media["streams"] if s["codec_type"] == "audio")
            assert (video["width"], video["height"]) == (1920, 1080)
            assert video["r_frame_rate"] == "30/1"
            assert video["pix_fmt"] == "yuv420p"
            assert audio["codec_name"] == "aac"
        report["master_loudness_in_target"] = -14.5 <= report["master_lufs"] <= -13.5
        report["upload_loudness_in_target"] = -14.5 <= report["upload_lufs"] <= -13.5
        (REVIEW / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        assert report["master_loudness_in_target"] and report["upload_loudness_in_target"], report
        assert 404 <= duration <= 407, duration
        save_status(status="completed", finished=datetime.now().astimezone().isoformat())
        print("Verification complete", flush=True)
    except BaseException:
        save_status(status="failed", traceback=traceback.format_exc(),
                    finished=datetime.now().astimezone().isoformat())
        raise

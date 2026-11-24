Codex: you are taking over the final render of WarMap Stick Video 6 (Crimea, long version 6:44). Everything is already prepared; your job is to run, verify and report. Claude will review your output.

Working dir: E:\Historias TIK\WarMap Stick\Guiones\Video 6 - Crimea

ALREADY DONE (do NOT modify these unless a step below fails because of them):
- guion.json (49 scenes), audio/, voz.wav, timeline.json (total 404.17 s)
- render3d/hook, nov26, oct22, fly (Blender frames, complete: 130/128/190/676 frames)
- _prep/cut_*.png sticker cutouts (python build.py --prep already run)
- build.py (renderer). Do NOT edit blender_puente.py, mapa.py, guion.json, audio or render3d.

STEPS
1. Full render: `python build.py` (no arguments). It writes sfx.json + sfx.wav, renders with 7 worker processes and writes
   E:\Historias TIK\WarMap Stick\Render\Video6_Crimea.mp4 (audio normalized with loudnorm -14 LUFS). It takes ~25–35 minutes; run it so it is not killed by a command timeout (e.g. start it in the background and poll the log/output file until "listo" is printed).
   If it crashes, read the traceback, make the MINIMAL fix in build.py (e.g. a word lookup that fails), and re-run. List every change you made.
2. Verify the MP4 with ffprobe/ffmpeg (ffmpeg path is in build.py, variable FF): duration ≈ 405 s, 1920x1080, 30 fps, AAC audio. Measure integrated loudness with `-af ebur128` and report it (target −14 LUFS ±1).
3. Extract review frames to E:\Historias TIK\WarMap Stick\Guiones\Video 6 - Crimea\_review\ : one JPG every 8 seconds (t=1,9,17,...) at 960x540, plus these exact times: 0.5, 1.2, 1.8, 2.6, 3.4, 328.7, 330.0, 347.5, 348.5. Then build contact sheets of 12 frames each (4x3 grid, timestamp written on each tile) named sheet_01.jpg, sheet_02.jpg, ...
4. Make an upload copy: E:\Historias TIK\WarMap Stick\Render\Video6_Crimea_upload.mp4 with libx264 -preset slow -crf 20 -pix_fmt yuv420p, AAC 192k, -movflags +faststart (audio copied or re-encoded, no re-normalization). Report both file sizes.
5. Look at your contact sheets yourself and list any frame that looks broken (black frame, missing sticker shown as a white placeholder circle with text, text cut off at the edges, overlapping labels, subtitle covering something important). Do not fix visual issues; just list them with timestamps.

FINAL REPLY (Spanish): changes made to build.py (if any), MP4 checks (duration, resolution, fps, LUFS, sizes), paths of the contact sheets, and the list of suspicious frames.

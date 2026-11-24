Codex: good work on the render. Claude reviewed your contact sheets. Please apply these 3 fixes in build.py (only these), re-render and re-verify exactly like last time (same steps 1–4: full render, ffprobe checks, review sheets into _review_v2\, upload copy). Working dir: E:\Historias TIK\WarMap Stick\Guiones\Video 6 - Crimea

1. Black vertical strip at the left around t=55–58 s (scene 06a, function s06a): the starting View(36.0, 50.5, 40) is wider than the base map crop (lon 18–76). Change it to View(37.0, 50.5, 34) and verify with `python build.py --frame 55 56 57 58` that no black/empty strip appears at any edge. If it still appears, reduce the width further.
2. "ANIMATED RECONSTRUCTION" tag (function small_tag) is cut on the left in the 3D scenes because of the punch-in at cuts. Move its center from x=230 to x=300 (keep y).
3. Loudness came out −15.1 LUFS (target −14). In the final ffmpeg mux of build.py replace single-pass loudnorm by a two-pass approach: first pass measures with loudnorm print_format=json, second pass applies measured_I/measured_TP/measured_LRA/measured_thresh/offset with linear=true. Target I=-14, TP=-1.5, LRA=11. Report the final integrated LUFS (must be −14 ±0.5).

Do not touch anything else. Final reply in Spanish: changes, checks (duration, res, fps, LUFS, sizes), sheet paths, suspicious frames.

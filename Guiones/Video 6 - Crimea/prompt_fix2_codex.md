Codex: new correction from Franco for WarMap Stick Video 6 (long format). Working dir: E:\Historias TIK\WarMap Stick\Guiones\Video 6 - Crimea

Franco does not like the big yellow scene HEADLINES at the top center (e.g. "ROAD ARCH DOWN", "WARM WATER", "1997 · 2010"). In long videos only the bottom SUBTITLES must remain, narrating what happens.

1. In build.py, function frame(t): stop drawing the headline (remove/disable the `headline(can, t)` call). Add a module constant `SHOW_HEADLINES = False` and guard the call with it, so it can be turned back on. Do not change subtitles.
2. Some scenes put small labels/date chips near the top (y around 190–260 px) that were placed BELOW the headline. They can stay; but check with `python build.py --frame <t>` on ~10 scenes (e.g. t = 2, 20, 60, 110, 160, 200, 270, 300, 330, 390) that nothing now looks strangely empty or misplaced. Report, don't redesign.
3. Full re-render (`python build.py`, ~30 min, run it so it is not killed by a command timeout), then the same verification as before: duration/res/fps/LUFS (two-pass loudnorm is already in build.py; target −14 ±0.5), review frames every 8 s + contact sheets into _review_v3\, and the upload copy Render\Video6_Crimea_upload.mp4 (x264 slow CRF 20, AAC copied, +faststart). Overwrite the previous Render\Video6_Crimea.mp4 and upload copy.

Do not touch anything else. Final reply in Spanish: change made, checks, sheet paths, suspicious frames.

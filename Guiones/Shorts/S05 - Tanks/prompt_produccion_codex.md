Codex: you are producing WarMap Stick Short S05 "Why Tanks Are Called 'Tanks'" (1080x1920, 30 fps, ~48.5 s). Franco (channel owner) approved the script, hook and formula; Claude will review your output frame by frame. Work dir:
E:\Historias TIK\WarMap Stick\Guiones\Shorts\S05 - Tanks

Research and formula (read them first, they explain the intent and what NOT to claim):
- E:\Historias TIK\WarMap Stick\Guiones\Ideas\2026-11-23 Formula Short Tanks (Claude+Codex).md
- E:\Historias TIK\WarMap Stick\Guiones\Ideas\2026-11-23 Investigacion Tanks (Codex).md

ALREADY DONE (do not change):
- guion.json: 12 scenes, each with a style (3D/MAP/CHAR) and a headline.
- audio/, voz.wav.
- timeline.json: total 48.53 s; per-scene start/dur in "timeline"; word timings in "words".
- "crushes" starts at 1.15 s. Use timeline.json for every other word sync.

TEMPLATES TO COPY (S04 is the closest, so start from it):
- ..\S04 - Saint-Nazaire\build.py, review.py, sound.py, master_audio.py, finish_render.py, render_all_3d.py, render3d.sh, mapa.py.
  - The own PIL renderer: big headline on top, subtitles in blocks of 2–3 words that last at least 0.65 s, SFX → sfx.wav, screen shake, `--prep` / `--frame t` / full render, loudnorm −14 LUFS.
  - Shorts KEEP the big headline on top.
- ..\S04 - Saint-Nazaire\blender_hook_claude.py: Blender 5.3 Eevee with the FX helpers (vol_shape, mist/smoke volumes, particles stepped frame by frame), plus Claude's camera fixes for vertical hooks.
  - Blender: "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe".
- ..\S04 - Saint-Nazaire\assets\: sticker style and prompts.json; reuse the cut-out pipeline.
- Natural Earth data: E:\Historias TIK\WarMap Stick\Recursos\naturalearth\
- ffmpeg: C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe

LESSONS FROM S04 (important):
- ALWAYS pass an ABSOLUTE --out path to Blender. A relative path writes to C:\.
- Vertical hook shots must be CLOSE: use a 22–28 mm lens near the subject so it FILLS the 9:16 frame. In S04 your first hook was too distant and small, and Claude had to redo it.
- AgX blows strong emission to white. Keep emissive values low and use warm colours.
- Eevee volumes need Object texture coordinates, and emission must be multiplied by the density mask.

STYLE RULES (Franco):
- **Hook in frame 0.**
  - Action from the very first frame. No static or empty frame, no title card, no still crate.
  - The climax lands on "crushes" (1.15 s): the track flattens the wire with a metallic crunch, a dirt burst and one short shake.
- **Almost everything animated.** Elements really move (tracks, mud, smoke, arrows drawing themselves, icons popping, Stick characters entering and gesturing). Few zooms on still images.
- **No 2D drawn effects on 3D shots.** Dirt, mud, exhaust smoke and sparks in 3D must be Blender particles or volumes.
- **SFX for every movement:** engine rumble, track clank, wire snap, stamp thud, paint brush, pop, whoosh, plus a low tension pulse.
- **No gore:** no people under tracks, no bodies, no blood.
- **No real insignia.** Use generic British khaki and generic grey Germans if any appear (they don't need to).
- **Tag on 3D shots:** a small "ANIMATED RECONSTRUCTION" tag inside the safe area.
- **Safe area:** keep text out of the bottom 280 px and the right 140 px.
- **Mark I accuracy:** rhomboid hull with the tracks running all the way round it, side sponsons with short guns ("male"), NO turret, rear steering-wheel tail optional, dark khaki or brown, about 8 m long. Never a modern or WW2 turreted tank.

SCENES (headline from guion.json; times from timeline.json)
- **01–02 (0–5.5 s), 3D "hook"**
  - Extreme low close-up of a Mark I track already moving over barbed wire on muddy ground with posts, from frame 0.
  - On "crushes" the wire is crushed: the posts snap, wire strands spring (curves animated or particles), and there is a mud and dirt burst.
  - The camera then pulls back and up, revealing the full rhombus by about 3 s while it keeps advancing.
  - In scene 02, a small flat water-tank icon pops next to the headline WATER TANK?. This is the only 2D overlay allowed on a 3D shot, and it is a UI icon, not an effect.
- **03, MAP**
  - Neon dark map of Britain zooming gently. "LATE 1915" chip.
  - A Stick British guard (WW1 khaki, flat Brodie helmet, rifle at rest) slides in next to a factory or shed icon with a padlock.
- **04, 3D "cross"**
  - The same Mark I model crosses a trench: the nose dips, then climbs out, with a mud spray in particles.
  - Camera low and close, filling the frame.
- **05, CHAR**
  - A Stick engineer holds a blueprint with the big word "LANDSHIP" (render the text with PIL, not in the generated image).
  - The guard panics. A red "TOO OBVIOUS" stamp drops on the sheet with a stamp SFX.
- **06, CHAR**
  - "LANDSHIP" is crossed out and the word "TANK" is stamped instead (big pop).
  - Stick guard gives a thumbs-up.
- **07, CHAR**
  - Split comparison: on the left a harmless water tank (a cylinder on legs) with a green check; on the right a tank silhouette under a tarp.
  - On "supposed to sound like it does" a "COVER NAME" label slides in.
- **08, CHAR**
  - A Stick worker paints Cyrillic letters on the side of the tarp-covered vehicle.
  - Render the text with PIL: "ПЕТРОГРАД" and a small English subtitle chip "WITH CARE TO PETROGRAD".
  - The brush moves and the letters appear letter by letter.
- **09, 3D "stall"**
  - The tank engine coughs: a burst of dark exhaust smoke (a volume), the tracks slow and stop for a moment, then restart.
  - Shake small.
- **10, MAP**
  - Neon map of northern France, the Somme: a "FLERS" marker and a "15 SEP 1916" chip.
  - 49 small tank icons pop in a grid, then 32 of them advance to a dashed "START LINE" and 17 turn grey and stay behind (breakdowns; do NOT show them destroyed).
  - Show the numbers "49 → 32".
  - Near the end, a small quote chip: "'A tank is walking up the High Street of Flers…' — RFC aircraft report".
- **11, 3D "crew"**
  - A cutaway section of the Mark I hull showing 8 simple 3D round-head Stick crew (like the S03 Roman Stick style: round white head, dot eyes, simple khaki bodies) in cramped seats around the engine.
  - A hatch closes with a clank. "8 MEN INSIDE" headline.
- **12, 3D "loop"**
  - Return to the SAME close track-over-wire shot as frame 0, so the last frame matches the first and the Short loops seamlessly.
  - You may reuse the hook frames in reverse or re-render the start.
  - Headline WATER TANK? again.

STEPS
1. **Blender.**
   - Write blender_tank.py with the Mark I model, a muddy no-man's-land set (posts, barbed wire, craters, one trench) and overcast light.
   - Shots: hook, cross, stall, crew (cutaway), loop.
   - Check stills first (--still) and look at them. Then render PNG sequences into render3d\<shot>\ in the background and poll.
2. **CHAR stickers.**
   - Generate them with your image tool: PNG on pure white, then cut out with a white sticker border.
   - Characters and objects: Stick British guard, Stick engineer, Stick painter, water tank on legs, tarp-covered tank, blank blueprint sheet, rubber stamp, factory shed with padlock, small tank icon (side view, rhomboid).
   - No text in the images.
3. **MAP scenes** with the mapa.py style (scenes 03 and 10).
4. **build.py:** all 12 scenes, headlines, subtitles, chips, SFX and shake ("crushes" is the big hit; the stamps are medium; the stall cough is small).
5. **Render.**
   - Output: E:\Historias TIK\WarMap Stick\Render\Shorts\S05_Tanks.mp4, at −14 LUFS ±0.5.
   - Upload copy: S05_upload.mp4, ≤ 10 MB.
6. **Review.**
   - Frames 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0, then every 2 s, plus the very last frame.
   - Put them in _review\ with contact sheets (_review\sheet_XX.jpg, 4x3, with timestamps).
   - Look at them yourself and list anything broken: black frames, placeholder shapes, cut text, a tank that looks modern or turreted, a tank too small in the hook, subtitles covering the key action, or a loop that doesn't match.

Long renders run in the background with polling. Do not modify other folders except reading the templates.

FINAL REPLY (Spanish):
- the files created;
- durations, LUFS and sizes;
- the contact sheet paths;
- the suspicious frames;
- anything you could not do.

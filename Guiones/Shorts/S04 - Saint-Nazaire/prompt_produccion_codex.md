Codex: you are producing WarMap Stick Short S04 "St Nazaire: The Warship That Became a Time Bomb" (1080x1920, 30 fps, ~43 s). Claude will review your output; Franco (channel owner) approved the script and hook. Work dir:
E:\Historias TIK\WarMap Stick\Guiones\Shorts\S04 - Saint-Nazaire

ALREADY DONE (do not change): guion.json (11 scenes with style 3D/MAP/CHAR + headline), audio/, voz.wav, timeline.json (total 42.84 s; word timings in "words"; "exploded" starts at 0.81 s, "rammed" at 2.31 s; scene 06 "rammed" and scene 08 "exploded" times are in timeline.json).

TEMPLATES TO COPY (read them first):
- Short renderer: ..\S03 - Alesia\build.py (own frame-by-frame PIL renderer 1080x1920: big yellow/white headline on top, word-by-word subtitles in blocks of 2–3 words ≥0.65 s, SFX list → sfx.wav, screen shake, `--prep` / `--frame t` / no args = full render, two-pass loudnorm −14 LUFS). Shorts KEEP the big headline on top.
- 3D + FX: ..\..\Video 6 - Crimea\blender_puente.py (Blender 5.3 Eevee, bridge model, camera shots, and the FX helpers: mist_domain, vol_shape, fire_column, explosion, water particles with motion blur, `--still a,b,c` stepping frames sequentially). Blender: "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe". Notes: Eevee volumes need Object texture coords (not Generated); Principled Volume emission must be multiplied by the density mask; legacy particles must step frame by frame.
- Neon dark map: ..\..\Video 6 - Crimea\mapa.py (Natural Earth base NE1 dark + country masks + neon borders, View(lon,lat,width°)); Natural Earth data in E:\Historias TIK\WarMap Stick\Recursos\naturalearth\.
- Sticker style for CHAR scenes: E:\Historias TIK\WarMap Stick\Imagenes\Video6\capas\ (WarMap Stick whiteboard style, thick black outlines, flat colours, round white head with dot eyes; cut out with white sticker border).
- ffmpeg: C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe

STYLE RULES (Franco):
- Hook visual in frame 0: action from the very first frame, the climax lands on the word "exploded" (0.81–1.2 s) with flash, shake and a deep boom. No static or empty frame ever.
- Almost everything animated: elements really move (water, smoke, ships sailing, arrows drawing themselves, icons popping, Stick characters entering). Few zooms on still images.
- NO 2D drawn effects on top of 3D shots: water, fire, smoke, debris and explosion in 3D shots must be Blender volumes/particles (reuse the Video 6 helpers). Explosion stickers only on 2D map/CHAR scenes.
- SFX for every movement (boom, metal crunch, water splash, engine, whoosh, pop) plus a low tension pulse.
- No gore: no bodies, no people being thrown, no blood. No swastikas or real insignia (generic grey German uniforms, plain flags). Label 3D shots with a small "ANIMATED RECONSTRUCTION" tag (keep it inside the safe area, not cut by shake).
- Keep text away from the bottom 280 px and right 140 px (YouTube Shorts UI).

STEPS
1. blender_nazaire.py: simplified but recognisable HMS Campbeltown (ex-US four-stack destroyer: long thin grey hull, 4 funnels — historically the raid removed 2 and cut the others at an angle, keep 2 raked funnels), the huge steel caisson gate of the Normandie dock (box gate), dock walls, harbour water, a few dockside buildings/cranes, overcast morning light. Shots (vertical 1080x1920 camera):
   - hook (scene 01, ~3.7 s + 3.2 s for scene 02): DAYLIGHT, ship already wedged in the gate, bow starting to crack at frame 0; on "exploded" (~frame 25) the bow explodes: bright fireball (volumetric), big debris pieces, the gate is pushed/buckled, a water surge and spray (particles + mist), black smoke rising; camera close 3/4 then pulls up. Scene 02 = "rewind": play the hook frames backwards in build.py and crossfade lighting to night (you may render a night still of the intact ship for the end of the rewind).
   - ram (scene 06, ~3.8 s): NIGHT, searchlights, the destroyer approaches fast and on "rammed" crushes its bow into the gate (deformation via shape key or lattice, sparks as particles, water bow wave), camera low near the water.
   - blast (scene 08, ~2.1 s): DAYLIGHT, wider angle repeat of the explosion (can reuse hook simulation with another camera).
   Render PNG sequences into render3d\<shot>\ (keep a render3d.sh like Video 6). Check stills first (--still) before full renders.
2. CHAR stickers: generate with your image tool, PNG on pure white 1024x1024, then cut out: Stick British commando (dark beret, blackened face is fine as simple dark grey), Stick Royal Navy sailor, two Stick German soldiers inspecting (grey uniform, generic helmet, no insignia), a crate of explosives with a clock fuse icon, a Stick general for the ending question, a ship icon, a dock icon, a Tirpitz battleship silhouette (generic grey battleship, no flags). No text in images.
3. MAP scenes with mapa.py-style neon map: 03 Britain → Saint-Nazaire (flotilla arrow drawing itself from Falmouth), 04 Tirpitz icon in Norway + dashed link to the dock + size comparison silhouettes, 09 dock marked "OUT OF ACTION" + timeline to 1945, 10 Tirpitz stays in Norwegian waters (don't draw a physical barrier).
4. build.py from the S03 template: all 11 scenes, headlines from guion.json, subtitles, small time chips "≈01:34" (scene 06) and "≈10:35" (scene 07), "≈600 RAIDERS" (scene 05), SFX + shake on "exploded" (scene 01 and 08) and "rammed" (scene 01 word at 2.31 s gets a small hit, scene 06 the big one).
5. Render → E:\Historias TIK\WarMap Stick\Render\Shorts\S04_Saint_Nazaire.mp4 (−14 LUFS ±0.5) and upload copy S04_upload.mp4 ≤ 10 MB (libx264 two-pass or CRF, AAC 128k, +faststart).
6. Review: extract frames 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0 and then every 2 s into _review\ and contact sheets (_review\sheet_XX.jpg, 4x3 with timestamps). Look at them yourself and list anything broken (black frames, placeholder circles, cut text, ugly 3D artefacts, subtitles covering the key action).

Long renders: run them in the background so a command timeout does not kill them, and poll. Do not touch other folders except reading the templates.

FINAL REPLY (Spanish): files created, durations/LUFS/sizes, contact sheet paths, list of suspicious frames, and anything you could not do.

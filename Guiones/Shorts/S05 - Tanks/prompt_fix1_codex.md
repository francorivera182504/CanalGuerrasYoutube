Codex: corrections for WarMap Stick Short S05 "Why Tanks Are Called 'Tanks'". You produced v1 in this folder:
E:\Historias TIK\WarMap Stick\Guiones\Shorts\S05 - Tanks
(blender_tank.py, build.py, s05_scenes.py, s05_sound.py, render3d\, assets\, _review\).
Read prompt_produccion_codex.md (the original brief and rules) and _review\REVISION.md first. Claude reviewed _review\sheet_01–05.

Do NOT change: guion.json, audio/, voz.wav, timeline.json, the subtitles style, the CHAR stickers' look (they are good), or the overall structure.

FIXES, in priority order:

1. **HOOK, 0–2 s (most important).**
   - **Problem:** the extreme close-up reads as a big tilted box or container. You can't tell it is a tank, and the barbed wire is tiny, so "crushes" (1.15 s) has no visible payoff.
   - **Camera:** re-shoot the hook from a LOW 3/4 FRONT angle (lens 24–28 mm, camera close to the ground about 3–5 m in front-left). From frame 0 we must see:
     - the unmistakable Mark I RHOMBUS silhouette, with the track running over the top and the front horn of the track rising toward the camera;
     - a sponson gun;
     - a BIG barbed-wire entanglement in the FOREGROUND: several posts and thick, clearly visible wire coils, occupying the lower third of the frame.
   - **Motion:** the tank is already moving toward the camera at frame 0.
   - **On "crushes" (frame 34–36):** the front of the track comes down onto the wire. Posts snap and fall, wire strands whip outward and up (big enough to read at phone size), and there is a mud burst (3D particles) with one short shake.
   - **Fill the frame:** the tank must fill at least 70% of the frame width by about 1.5 s.
   - **After the crush:** a slow pull up and back (1.5–5.4 s) keeps the tank BIG, filling at least 65% of the width. No empty sky taking half the frame.
   - **Loop:** scene 12 must match this new frame 0 for the loop.
   - **Check before animating:** render stills at frames 0, 20, 35, 45 and 90 and look at them before rendering the animation.

2. **CREW CUTAWAY, scene 11 (39.1–42.5 s).**
   - **Problem:** it reads as a table with figurines on top, not as the inside of a tank.
   - **Fix it:**
     - Keep the full rhomboid hull, with the tracks visible around it, and remove only the near side wall.
     - Make the interior dark and cramped: dark olive or brown walls, a warm dim interior light, and a big engine block in the CENTRE.
     - Seat the 8 round-head Stick crew around the engine, inside the walls and partially occluded by them. Not standing on a flat plate.
     - Bring the camera closer so the hull fills at least 80% of the width.
     - Add a little engine smoke haze inside (a volume) and the hatch closing with a clank at the end.

3. **3D SHOTS TOO SMALL.** In 2.5–5.4 s, the stall (27.6–30 s) and the loop start (42.5–44.5 s) the tank fills only about 45% of the width, with lots of empty grey sky.
   - Bring the cameras closer and lower so the tank fills at least 65% of the width. The horizon should sit in the upper third, with mud and wire in the foreground.
   - Give the sky a bit more mood: overcast with soft darker clouds or haze. Not flat grey.

4. **NEAR-EMPTY FRAMES AT SCENE STARTS.** No frame may be mostly empty:
   - 13.25 s: the LANDSHIP engineer enters from the side, cut off. Start the scene with him already on screen, popping and scaling in place, then animate.
   - 19.35 s: the water tank is tiny. Start the scene with both panels already visible at full size.
   - 24.10 s: the tarp is alone. The painter should already be there.
   - 30.0 s: the start-line box is black and empty. Show the tank icons popping in right away.
   - Rule: every scene's first frame already shows its main subject at full size.

5. **MAP, scene 10:**
   - Make the RFC quote chip readable on a phone, or drop it: at least 30 px text, 2 lines max, shown 36.9–39 s.
   - Make "17 HELD BACK · BREAKDOWNS" at least 26 px.
   - The curved yellow line from "THE SOMME" to "FLERS" is confusing. Replace it with just a pulsing Flers marker.
   - Make the 49 icons bigger (the grid filling about 85% of the width).

6. **TANK MATERIAL.** It looks like a smooth plastic box.
   - Add rivet rows, visible track plates, mud on the lower tracks and hull, roughness variation, a darker khaki-brown and a little edge wear.
   - Optionally add the rear wheel-tail.
   - Keep the poly count reasonable.

7. **Low-variation stretches** (around 21 s, 33.6–36.4 s, 39.8–42.2 s): add small motion. For example, the water tank wobbles and drips, tank icons bob, or a camera micro-drift in the crew shot.

Then:
- re-render the affected 3D shots (absolute --out paths, in the background, polling);
- rebuild;
- render to E:\Historias TIK\WarMap Stick\Render\Shorts\S05_Tanks.mp4 (−14 LUFS ±0.5) and S05_upload.mp4 (≤ 10 MB), overwriting v1;
- redo the _review frames and sheets, adding frames 1.15, 1.30 and 1.50 s and the last frame.

FINAL REPLY (Spanish):
- what you changed;
- the new sheet paths;
- sizes and LUFS;
- anything still weak.

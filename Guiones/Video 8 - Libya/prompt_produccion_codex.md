Trabajas para WarMap Stick. Responde en español. Carpeta: `Guiones/Video 8 - Libya/`. Video largo de ~15 min. Datos: `Datos (Codex).md`.

PASO 1 — PULIR `guion.json`. Varias escenas suenan a informe editorial y hay que reescribirlas como narración natural, sin hablar de "sources", "this report", "established", "route to animate" ni de lo que el equipo pudo o no verificar. Ejemplos a corregir: 012, 013, 032, 105, 110, 117, 123 (revisa TODAS). La atribución va natural ("Kyiv says", "according to Libyan officials", "it is still unclear"). Mantén ~2100–2250 palabras, la fórmula del hook (clímax en cuadro 0, primera frase ≤14 palabras) y que ninguna escena corte una frase a la mitad de forma que la voz suene rara. Largos: SIN titular grande arriba.

PASO 2 — PRODUCCIÓN con el pipeline del largo anterior `Guiones/Video 7 - Middle East/` (lee build.py, engine.py, mapa.py, prep3d.py/blender_kit.py, sus logs y cómo generó voz, sfx y render final; reutiliza su motor):
- Voz con `Scripts/voz.py` igual que V7.
- Imágenes con generación de imágenes, mismo estilo de V7 (`00_stick_ref.png`, `_prep/cut_el_*.png`): corbeta rusa, buque de carga Angara, dron naval USV, stickmen (marinero ruso, operador ucraniano, oficial libio, Haftar, Zelenski, Putin estilizados sin parecer fotos), puerto de Benghazi, base Tartus, convoy naval, avión de transporte, barril/petrolero. Mapas reales a pantalla completa (Libia, Mediterráneo, Siria, Sahel/África) con zoom a lugares concretos.
- Prohibido: fondo cuadrícula, mapa neón sobre tablero vacío, cápsulas de titular, subtítulos karaoke en caja negra, stickers flotando sin acción, etiquetas de esquina. Estilo casi todo animado: cada elemento entra con movimiento, pocos zooms bruscos, textos lentos de leer. Cambio visual cada ≤8 s.
- Render: `Render/Video8_Libya.mp4` (1920x1080, −14 LUFS) + `Render/Video8_upload.mp4` (≤10 MB, dos pasadas) + .srt.
- Fotogramas de control `_prep/chk_000.jpg…chk_005.jpg` (t=0–5 s) y una hoja de contactos de 1 cuadro cada 30 s en `_prep/sheet.jpg`. Revísalos tú y corrige antes de terminar.

PASO 3 — `Paquete de subida (Codex).md`: TITLE (+2 alt), DESCRIPTION en inglés con capítulos y fuentes, TAGS ≤500, PINNED COMMENT, orden de 3 miniaturas para Test & Compare con sus prompts, y genera las 3 miniaturas 1280x720 en `Miniatura/Libya/`.

No toques otras carpetas salvo Render/ y Miniatura/Libya/.

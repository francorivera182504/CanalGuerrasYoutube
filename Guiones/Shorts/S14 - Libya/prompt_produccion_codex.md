Trabajas para WarMap Stick. Responde en español. Carpeta: `Guiones/Shorts/S14 - Libya/`. Datos verificados: `Guiones/Video 8 - Libya/Datos (Codex).md` (usa solo eso).

PASO 1 — REESCRIBIR `guion.json` (40–45 s, 105–115 palabras). El actual suena a informe editorial: frases como "That cargo claim requires attribution", "The sources do not establish…", "The full video follows…" están PROHIBIDAS (en Shorts no hay enlaces; el narrador no habla de sus fuentes). La atribución se hace natural: "Kyiv says…", "according to…". Fórmula: escena 01 HOOK = clímax (dron naval impactando la corbeta Merkury en Benghazi) en el cuadro 0, primera frase ≤14 palabras con la anomalía antes de 2 s, headline 2–5 palabras; un cambio visual cada ≤1.5 s hasta 5 s; segunda frase que abra un misterio para que se queden; termina con pregunta para comentarios. Mantén las claves del esquema de `Guiones/Shorts/S13 - Krummlauf/guion.json`.

PASO 2 — PRODUCCIÓN copiando el pipeline de `Guiones/Shorts/S13 - Krummlauf/` (lee su build.py, sound.py, master_audio.py, finish_render.py):
- Voz: `python Scripts/voz.py "Guiones/Shorts/S14 - Libya/guion.json" "Guiones/Shorts/S14 - Libya/audio" +8%` y `python Scripts/short_join.py "Guiones/Shorts/S14 - Libya"`.
- Imágenes en `assets/` con generación de imágenes, estilo de referencia `Guiones/Shorts/S05 - Tanks/assets/guard.png` (stickers sobre fondo blanco) + fondos a pantalla completa apagados (puerto de Benghazi de noche, mar). Necesarios: corbeta rusa, buque de carga, dron naval (USV) con estela, stickman marinero ruso, stickman operador ucraniano, stickman oficial libio. Mapa real con Natural Earth como en S13 (Mediterráneo: Ucrania/mar Negro → Benghazi, Siria/Tartus, rutas a África).
- `build.py` propio (no plantilla genérica). Prohibido: fondo cuadrícula, mapa neón sobre tablero vacío, cápsulas de titular, subtítulos karaoke en caja negra, stickers flotando sin acción, etiquetas de esquina. Texto grande simple permitido. Sujeto ≥40 % de la altura en el hook, movimiento desde 0.2 s, acercamiento a la acción y luego abrir al mapa.
- Render: `Render/Shorts/S14_Libya.mp4` y `Render/Shorts/S14_upload.mp4` (≤10 MB, −14 LUFS), con SFX en sound.py.
- Guarda fotogramas de control en `_prep/chk_00.jpg … chk_05.jpg` (t=0,1,2,3,4,5 s) y una hoja de contactos del resto en `_prep/sheet.jpg`. Revísalos tú mismo y corrige cortes, textos que se salen o elementos tapados antes de terminar.

PASO 3 — `Paquete de subida (Codex).md`: TITLE (+2 alt, ≤60, fórmula Why/How/The X who), DESCRIPTION corta en inglés con 2–3 hashtags y fuentes, TAGS ≤500 caracteres, RELATED VIDEO (el largo "Why Ukraine Struck Russian Ships in Libya", aún no publicado; si no existe, el más afín), PINNED COMMENT, texto TikTok.

No toques otras carpetas salvo Render/Shorts.

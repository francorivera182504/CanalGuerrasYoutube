---
name: ideas
description: Proceso de WarMap Stick para decidir y crear el siguiente video o Short — lluvia de ideas con Codex (temas con tendencia y vistas en el nicho), elegir tema con Franco, definir hook auditivo + hook visual sincronizados, y luego crear el video en estilo casi todo animado hasta /subida. Usar cuando Franco diga /ideas o pida pensar el siguiente video.
---

# /ideas — del tema al video terminado

Franco aprueba en cada puerta (tema → hooks → video). No avanzar de fase sin su OK.

## Fase 1 — Lluvia de ideas con Codex
1. Revisar memoria: `warmapstick-channel.md` (qué funcionó, videos ya hechos, video ganador por búsqueda) y `warmapstick-estilo-animado.md`. No repetir temas ya hechos.
2. Escribir `Guiones/Ideas/AAAA-MM-DD prompt_ideas_codex.md` pidiendo, en español salvo títulos en inglés:
   - 8–10 ideas mezclando **actualidad** (noticias de las últimas semanas con vistas en el nicho) y **búsqueda perenne** ("[conflicto] war explained", "why did X…").
   - Para cada una: evidencia de demanda (videos recientes del nicho con vistas, fecha y URL; volumen de búsqueda si hay), formato sugerido (Short 45 s / largo ~6 min), título tentativo, el **momento más impactante** que se puede animar con stickmen y mapa, y riesgos (datos en disputa, políticas de YouTube).
   - Top 3 recomendado con el porqué.
3. Enviar al chat de estrategia «Optimiza estrategia y copy para YouTube» (id `01a2011e-2cee-7540-8844-9dc5273b6f01`): `codex exec resume <id> "$(cat prompt)"`; si responde "already has an active writer", `codex queue --thread <id> --message "$(cat prompt)" --resume` y leer la respuesta del `~/.codex/sessions/AAAA/MM/DD/rollout-...-<id>.jsonl` (mensaje del asistente posterior al envío). Guardar en `Guiones/Ideas/AAAA-MM-DD Lluvia de ideas (Codex).md`.
4. Contrastar con datos propios: WebSearch (¿sigue caliente?) + **TubeAlfred** (`youtube_search_query` / `youtube_search_suggest` / `youtube_videos_batch`: mediana de vistas del top 20 = demanda; videos del último año con +100k = competencia) + **TubeBuddy Keyword Explorer** en el Chrome de Franco (puntaje de búsqueda/competencia) para las frases de título candidatas. Si un Short del canal está creciendo, considerar el largo del mismo tema. Presentar a Franco las ideas en una tabla corta + recomendación. **Esperar que elija.**

## Fase 2 — Hooks (auditivo + visual, juntos)
Regla de oro: **el clímax visual del video va en el cuadro 0 y coincide con la primera frase**; desde el primer cuadro ya hay acción (nada de cuadro quieto) o es scroll fácil.
1. Con Codex (mismo chat), pedir 3 propuestas de hook para el tema elegido. Cada una con:
   - **Hook auditivo**: primera frase en inglés (≤ 18 palabras), agresiva y con dato fuerte; el verbo fuerte ("dropped", "destroyed", "erased") cae ~0.8–1.2 s.
   - **Hook visual**: qué se ve del cuadro 0 a ~2 s, segundo a segundo (qué elemento se mueve, explosión, temblor, SFX), sincronizado con las palabras.
   - Titular grande de arriba para esos 2 s (2–3 palabras).
   - Lo que hace que se queden hasta el segundo 5 (pregunta abierta / "and it keeps…").
2. Revisar exactitud (no exagerar: "part of", fechas en recreaciones). Presentar las 3 a Franco con recomendación. **Esperar que apruebe una.**

## Fase 3 — Creación (estilo casi todo animado)
Seguir `warmapstick-estilo-animado.md` y el pipeline de Shorts (`Guiones/Shorts/S02 - Crimean Bridge/` es la plantilla más reciente):
1. Guion (`guion.json`, ~110–120 palabras para Short) que abre con el hook aprobado y cierra con pregunta para comentarios. Datos verificados con Codex.
2. Voz: `python Scripts/voz.py guion.json audio +8%` y `python Scripts/short_join.py <carpeta>` (→ `voz.wav`, `timeline.json`).
3. Capas con Codex (`codex exec --sandbox workspace-write --skip-git-repo-check -i refs - < prompt_capas_codex.md`): fondos SIN elementos móviles + elementos sueltos sobre blanco; si hace falta un estado "antes/después" del mismo fondo, pedir la edición de la misma imagen y sacar el elemento por diferencia de píxeles. Mapas reales: dibujarlos con coordenadas (ver `mapa.py` de S02) si el de Codex no se reconoce.
4. `build.py` copiando la estructura de S02: escena 1 = hook visual desde t=0 (drones/elementos ya en pantalla, impacto ≤0.3 s, clímax en el verbo del hook, temblor del fondo con `BGK`), SFX por cada movimiento, titulares estables por frase, subtítulos 2–3 palabras ≥0.65 s. `python build.py --prep` y revisar composiciones antes de OpenReel.
5. OpenReel: `Scripts/abrir_openreel_local.bat`, `python -m http.server 8777 --bind 127.0.0.1` en la raíz, `python build.py` (crea proyecto nuevo), `export_video` mp4 → loudnorm −14 LUFS → `Render/Shorts/S0X_*.mp4` + copia comprimida `S0X_upload.mp4`.
6. Revisar fotogramas (sobre todo 0–5 s cuadro por cuadro) y enviar el MP4 a Franco. Tras su aprobación → `/subida`.

## Después
Anotar en memoria el tema elegido, los hooks aprobados y cualquier corrección de estilo de Franco.

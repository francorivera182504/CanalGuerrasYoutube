---
name: subida
description: Proceso de subida de WarMap Stick a YouTube (videos largos y Shorts) — paquete de Codex (título, descripción, etiquetas, comentario fijado), preparar el MP4, llenar YouTube Studio en el Chrome de Franco y dejarlo listo para que él presione Publicar. Usar cuando Franco diga /subida o pida subir un video o Short.
---

# /subida — subir un video o Short de WarMap Stick

Franco presiona **Publicar**. Claude prepara todo y se detiene justo antes. Nunca hacer clic en Publicar/Programar.

## 1. Paquete de subida con Codex
1. Escribir el prompt en `Guiones/<video>/prompt_subida_codex.md` con: tipo (largo o Short), duración, guion final completo, texto en pantalla del inicio, video largo relacionado (título + ID) si es Short. Pedir verificar las cifras/datos y señalar frases que convenga suavizar.
2. Formato pedido: `TITLE` (+2 alternativas; Shorts ≤ ~60 caracteres) / `DESCRIPTION` (inglés, lista para pegar; Shorts: corta, 2–3 hashtags, sin links porque no son clicables) / `TAGS` (≤ 500 caracteres) / `RELATED VIDEO` (solo Shorts) / `PINNED COMMENT` / `SETTINGS` / `NOTAS` (qué revisar a las 24–48 h). En largos además: capítulos en la descripción y orden de miniaturas para Test & Compare.
3. Enviar al chat de estrategia «Optimiza estrategia y copy para YouTube» (id `01a2011e-2cee-7540-8844-9dc5273b6f01`):
   - Si el chat NO está abierto en la app: `codex exec resume <id> "$(cat prompt.md)"` en segundo plano.
   - Si da "already has an active writer" (está abierto en la app): `codex queue --thread <id> --message "$(cat prompt.md)" --resume` y leer la respuesta del `rollout-...-<id>.jsonl` en `~/.codex/sessions/AAAA/MM/DD/` (mensaje del asistente posterior al envío que contenga TITLE y TAGS). Aunque diga "could not resume… start a local daemon", el mensaje queda en cola y la app lo procesa. Lanzar en segundo plano un script de espera que lea el rollout (timestamp > envío, texto con TITLE y TAGS) y lo guarde en el `.md`; mientras tanto subir el MP4 en Studio (Codex tarda ~4 min).
4. Guardar la respuesta en `Paquete de subida (Codex).md` junto al guion. Revisar que los datos tengan sentido antes de usarlos.

## 2. Preparar el archivo
- `file_upload` de Claude in Chrome acepta **≤ 10 MB**.
- **Shorts**: recomprimir para subirlo directo (el estilo pizarra comprime muy bien):
  `ffmpeg -i final.mp4 -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -tune animation -c:a aac -b:a 128k -movflags +faststart S0X_upload.mp4` (45 s ≈ 5 MB). Audio ya normalizado a −14 LUFS.
- **Videos largos** (>10 MB): Franco arrastra el MP4 al cuadro de subida; Claude llena todo lo demás.
  Si Franco no está y pidió subirlo igual: recomprimir a ≤10 MB en dos pasadas (`-c:v libx264 -b:v 200k -maxrate 550k -bufsize 1100k -preset slow -tune animation -pix_fmt yuv420p`, `-c:a aac -b:a 96k`; 4:16 ≈ 9,7 MB), revisar un cuadro cargado y avisarle que puede reemplazarlo por el MP4 completo.
- Nunca intentar que Studio lea archivos por `fetch` a localhost: congela la pestaña.

## 3. YouTube Studio (Chrome de Franco, canal WarMap Stick `UCb0A2jU8w7pFxqgR66Ed2BQ`)
1. Abrir `https://studio.youtube.com/channel/UCb0A2jU8w7pFxqgR66Ed2BQ/videos/upload?d=ud`.
2. `find` → "file-input (hidden)" → `file_upload` con el MP4 (o esperar a que Franco lo arrastre).
3. **Detalles**: título (clic en el campo, ctrl+a, escribir) · descripción (NO pulsar Escape: si no hay sugerencia abierta, Escape cierra toda la ventana de subida; para cerrar la sugerencia de hashtags hacer clic en un área vacía del formulario. Si se cerró, el borrador queda guardado: pestaña Shorts/Videos → «Editar borrador») · miniaturas (solo largos: subir A/B/C con Test & Compare en el orden de Codex) · Público: «No, no es contenido creado para niños».
4. «Mostrar configuración avanzada»:
   - **Uso de la IA → «No»**: la pregunta es solo sobre personas reales, alterar hechos/lugares reales, escenas realistas o música de IA como foco. Dibujos de stickmen + voz narradora genérica + música/efectos por código no aplican. Si algún día hay escenas fotorrealistas o música de IA protagonista → «Sí».
   - Etiquetas: pegar la lista de Codex terminando en coma.
   - Idioma del video: **Inglés (Reino Unido)**. Categoría: **Educación** (ya viene por defecto). Licencia estándar.
5. **Elementos de video**: en Shorts, «Video relacionado → Agregar» → elegir el largo del mismo tema (el buscador del selector no filtra al escribir: elegir de la cuadrícula; si el video que sugiere Codex no aparece, usar el largo más afín y anotarlo). En largos: pantalla final/tarjetas si Codex lo indica. Ojo: el editor de pantalla final congela la pestaña con screenshots → usar solo `find`/`read_page`, y si se cuelga, dejarlo a Franco.
6. **Verificación inicial**: esperar «No se encontraron problemas».
7. **Visibilidad**: marcar **Público** (o lo que Franco pida) y DETENERSE. El botón queda en «Publicar» para Franco.
   - **Si Franco pide programar** (fecha/hora): abrir «Programar» (desplegable) → fecha en el calendario (viene por defecto el día siguiente 12:00 a. m.) → hora en la lista (`find` "12:00 p.m." + `scroll_to`) → zona horaria «(GMT-0500) Hora local» (Perú). Verificar con `zoom` y DETENERSE: el botón queda en «Programar» para Franco.

## 3b. TubeBuddy (extensión en el Chrome de Franco)
- Al llenar Detalles, revisar el panel/puntaje SEO de TubeBuddy si aparece (título, etiquetas, descripción) y ajustar solo si mejora sin cambiar el sentido del paquete de Codex; anotar el puntaje.

## 4. Después
- Avisar a Franco con un solo mensaje: listo para Publicar + título elegido + qué falta.
- Tras publicar: fijar el comentario de Codex (Franco, o Claude si lo pide).
- Anotar en la memoria (`warmapstick-channel.md`): ID del video, título, configuración, pendientes y revisiones de 24 h (CTR / viewed vs swiped) y 48 h (retención). No cambiar título ni miniatura durante un Test & Compare.

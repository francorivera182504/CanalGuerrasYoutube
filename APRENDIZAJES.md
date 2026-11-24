# Aprendizajes del canal WarMap Stick

Resumen vivo de lo que funcionó, lo que no y cómo producimos. Actualizado: 23-nov-2026.

## 1. Datos del canal
- **Ganador por búsqueda:** "The Russia–Ukraine War Explained in 6 Minutes (Fast Guide)" (JjQRgKbusdE). Tiene más de 10.000 vistas y el 89 % llega por YouTube Search ("russia ukraine war explained"). La retención es del 43 % y apenas gana suscriptores.
- **Shorts:**
  - El S01 Fuel Tanks sacó 53 vistas. Hook débil y tema frío.
  - El S02 Crimean Bridge sacó unas 1.000 el primer día. El hook visual en el cuadro 0 y el tema de actualidad funcionaron.
- **Lo que se lleva el clic:** títulos en forma de pregunta ("Why did X…?", "The Real Reason…") en lugar de "Explained in 6 Minutes".

## 2. Videos publicados o listos (IDs)
| Video | ID | Estado |
|---|---|---|
| Russia–Ukraine War Explained | JjQRgKbusdE | publicado (el que crece por búsqueda) |
| V4 Pearl Harbor | n4GD5rsRCPI | Test & Compare de 3 títulos y miniaturas |
| V5 The Winter War: How Finland Survived Stalin | 1OXSE1tSKXE | falta la pantalla final |
| V6 Why Russia Wants Crimea—and Why Its Bridge Is a Target | _n1757a1eAM | faltan la pantalla final y la tarjeta |
| S01 Pearl Harbor Fuel Tanks | Dsg5cVBe2-w | publicado |
| S02 Why Ukraine Keeps Hitting the Crimean Bridge | -8UN7oEhyhQ | publicado; su video relacionado debe pasar a ser V6 |
| S03 Why Caesar Built a Wall Around His Own Army | — | programado |
| S04 Why Britain Blew Up Its Own Warship | 5f8-nBQIWa8 | listo para Publicar |

## 3. Reglas de estilo (aprobadas por Franco)
- **Casi todo animado.** Los fondos quedan fijos y el movimiento lo ponen los elementos: fuego, humo, aviones, flechas, Stick entrando a escena. Pocos zooms. Cada movimiento lleva su efecto de sonido.
- **Hook visual en el cuadro 0.** El momento más impactante va al principio, sincronizado con la primera frase. El verbo fuerte ("dropped", "exploded") cae a ~0,8–1,2 s, con temblor de pantalla y SFX. Si no hay acción desde el primer cuadro, el espectador hace scroll.
- **Hooks agresivos** con un dato fuerte, seguidos de una pregunta abierta que retenga hasta el segundo 5.
- **Textos más lentos.** Subtítulos de 2–3 palabras que duren al menos 0,65 s, en Arial Black/Inter blanco con contorno negro y la palabra clave en amarillo.
- **Titulares grandes arriba:** sí en Shorts, no en videos largos (en los largos solo van subtítulos).
- **Videos largos de 6–10 min:** guion de 1.000–1.400 palabras con voz Ryan +4 %. Se amplía con contexto real, no con relleno.
- **Nada de efectos 2D dibujados sobre tomas 3D.** Agua, fuego, humo y explosiones se hacen en Blender. Los stickers 2D de explosión quedan solo para los mapas.
- **Estilo mixto (V6, S03, S04):** mapa oscuro con contornos neón (Natural Earth) + stickers de Stick 2D con borde blanco + una toma 3D en Blender solo para el objeto clave.
- **Exactitud:** decir "around" antes de las cifras, fechar las recreaciones y no exagerar los efectos ("part of", "helped keep…"). Rotular las reconstrucciones como ANIMATED RECONSTRUCTION.

## 4. Proceso (skills en `.claude/skills/`)
1. **`/ideas`**
   - Codex hace la lluvia de ideas, cruzando actualidad con búsqueda perenne.
   - Medimos demanda y competencia: TubeAlfred, más la mediana de vistas del top 20 frente a los videos del último año con más de 100k.
   - Franco elige; Codex propone 3 hooks (auditivo + visual) y Franco aprueba uno.
   - Producción.
2. **`/subida`**
   - Codex arma el paquete: título, descripción, etiquetas, comentario fijado y notas de revisión.
   - Claude llena YouTube Studio en Chrome y se detiene antes de Publicar, que siempre lo pulsa Franco.
3. **Reparto de trabajo:** Codex ejecuta (renders, capas, paquetes) con `codex exec --sandbox workspace-write` y Claude revisa los fotogramas y los datos. El hilo de estrategia de Codex queda solo para textos.
   - **Lección del S04:** en tomas de hook, pedir a Codex una cámara cercana que llene el cuadro vertical. Su primera versión quedó lejana y pequeña.

## 5. Pipeline técnico
- **Voz:** `Scripts/voz.py` (edge-tts, en-GB-RyanNeural; +4 % en largos, +6–8 % en Shorts) y `Scripts/short_join.py`, que genera `voz.wav` y `timeline.json` con los tiempos de cada palabra.
- **Render propio:** `build.py` por video y `Scripts/render_layers.py` (PIL + ffmpeg en paralelo, loudnorm a −14 LUFS). OpenReel no sirve para videos largos con muchas capas.
- **Mapas:** `mapa.py` del V6 o del S04, con Natural Earth (NE1 + 10m). Ojo: las fronteras son las actuales; en NE 10m Crimea viene dentro de "Russia".
- **Blender 5.3 (Eevee, RTX 3060):**
  - Correr con `blender -b -P script.py -- --out <RUTA ABSOLUTA>`. Una ruta relativa se escribe en la raíz de C:.
  - `bevel_factor_end` no se anima: hay que rehacer la curva en `frame_change_pre`.
  - En volúmenes, usar la coordenada *Object* (no *Generated*) y multiplicar la emisión por la máscara.
  - Las partículas legacy se simulan avanzando cuadro a cuadro.
  - Con AgX, la emisión fuerte se quema a blanco: bajar la emisión (×0,3) y usar color naranja (1,0.38,0.04).
  - Para explosiones verticales: lente de 22 mm, cámara que se aleja mientras la bola de fuego crece, y un temblor que decae.
- **Subida:**
  - El MP4 debe pesar como máximo 10 MB para `file_upload`. En Shorts, recomprimir con CRF 23 y `-tune animation`.
  - Los videos largos los arrastra Franco.
  - El editor de pantalla final congela la pestaña si se toman capturas.

## 6. Análisis de competencia: Ambos Bandos (español, 23-nov-2026)
Lleva 430k vistas en 6 semanas, casi todas de 2 videos "¿Por qué X NO hizo Y?". Detalle en `Guiones/Ideas/2026-11-23 Analisis canal Ambos Bandos (Claude).md`.
- **Para probar:**
  - Formato "Why didn't…?" / "Why X Never…".
  - Miniatura con Stick-caricatura del líder, sin insignias reales.
  - Sellos MYTH / HALF TRUE / TRUE por "expediente".
  - Descripción con arranque de película y fuentes.
  - Español mediante doblaje automático o una pista de audio propia.
- **No copiar:** su ritmo de 4–5 videos de 29 min el mismo día, por el riesgo de que YouTube lo trate como contenido repetitivo.

## 6b. Competencia en Shorts: Datoon (23-nov-2026)
"Why trenches were never straight" sacó 167k vistas con un canal de 6 semanas. Su fórmula:
- una curiosidad sobre un detalle físico de la guerra;
- narración en segunda persona ("You are in France…");
- el problema contra la solución en antes y después;
- un giro, un dato de escala sobre el globo y un cierre emocional;
- una toma 3D aérea en el cuadro 0.

Para nosotros: una serie "You Are the Soldier" con Stick 3D, mapa neón y Blender. Ideas y detalle en `Guiones/Ideas/2026-11-23 Analisis Shorts Datoon (Claude).md`.

## 7. Qué revisar tras publicar
- **Shorts:** a las 24–48 h, "Stayed to watch" (viewed vs swiped) y la retención de los primeros 3 s. Comparar con el S02 a la misma edad.
- **Largos:** a las 24 h, el CTR por fuente; a las 48 h, la retención de 0:00–0:30. No tocar título ni miniatura mientras corre un Test & Compare.

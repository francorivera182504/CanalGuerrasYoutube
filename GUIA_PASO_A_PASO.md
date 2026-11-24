# Guía paso a paso: cómo hacer un video de WarMap Stick (para principiantes)

Esta guía va desde cero hasta el video subido a YouTube. Sigue los pasos en orden y no te saltes ninguno. Si algo no te funciona, revisa el apartado de problemas comunes al final.

> Idea clave: **WarMap Stick explica guerras con un muñeco de palitos (Stick) y mapas.** Lo que más importa es que **desde el primer segundo pase algo impactante** (una explosión, un puente que cae) y que **todo se mueva**: el fondo queda quieto y los elementos se mueven sobre él.

---

## PARTE 0: Qué es cada cosa (vocabulario mínimo)

| Palabra | Qué significa |
|---|---|
| **Short** | Video vertical de unos 45 segundos (1080×1920). |
| **Largo** | Video horizontal de 6 a 10 minutos (1920×1080). |
| **Hook** | Lo primero que se ve y se escucha. Si es aburrido, la gente pasa al siguiente video. |
| **Guion** | El texto que dice la voz, separado en escenas (`guion.json`). |
| **Capas / stickers** | Dibujos sueltos (Stick, aviones, flechas) que se ponen encima del fondo y se mueven. |
| **Render** | Convertir todas las piezas (fondos, capas, voz, sonidos) en el MP4 final. |
| **Codex** | La otra IA (de ChatGPT) que usamos para dibujar, investigar datos y escribir títulos y etiquetas. |
| **Claude** | La IA que coordina todo, escribe el código y revisa. |

---

## PARTE 1: Instalar las herramientas (solo la primera vez)

Instálalas una por una. Al lado de cada una dice para qué sirve.

1. **Python 3** (python.org). Durante la instalación marca la casilla **"Add Python to PATH"**. Sirve para correr todos los scripts.
2. **Librerías de Python.** Abre PowerShell y pega:
   ```powershell
   pip install edge-tts numpy scipy pillow pyshp
   ```
   - `edge-tts` genera la voz.
   - `numpy`, `scipy` y `pillow` sirven para dibujar y mezclar imágenes y sonido.
   - `pyshp` sirve para leer mapas.
3. **ffmpeg.** Sirve para crear y comprimir el MP4. Instálalo con:
   ```powershell
   winget install Gyan.FFmpeg
   ```
4. **Blender 5.3** (blender.org). Es gratis y sirve para las tomas 3D: barcos que explotan, puentes que caen.
5. **Codex CLI.** Inicia sesión con tu cuenta de ChatGPT. Sirve para generar dibujos y textos.
6. **Claude Code** (app de escritorio). Abre la carpeta del proyecto `WarMap Stick` dentro de Claude.
7. **Google Chrome** con la extensión **Claude in Chrome**, y la sesión de YouTube Studio del canal abierta. Sirve para que Claude llene los datos de la subida.
8. **Mapas Natural Earth** (naturalearthdata.com). Descarga el relieve *NE1_HR_LC_SR_W_DR* y los vectores 10m (*countries*, *coastline*, *land*, *lakes*, *rivers*). Ponlos en `Recursos/naturalearth/`. No están en git porque pesan mucho.

Opcionales, para investigar: **TubeAlfred** (datos de YouTube dentro de Claude), **vidIQ**, **TubeBuddy** (extensión de Chrome) y **Windsor.ai** (estadísticas del canal).

> ✅ Comprobación: escribe `python --version` y `ffmpeg -version` en PowerShell. Si los dos responden con un número de versión, vas bien.

---

## PARTE 2: Entender cómo está organizada la carpeta

```
WarMap Stick/
├─ APRENDIZAJES.md        ← lo que ya aprendimos (léelo una vez)
├─ GUIA_PASO_A_PASO.md    ← esta guía
├─ .claude/skills/        ← los "botones mágicos": /ideas y /subida
├─ Scripts/               ← herramientas comunes (voz, render, sonidos)
├─ Guiones/
│   ├─ Ideas/             ← lluvias de ideas y hooks
│   ├─ Shorts/S04 - .../  ← una carpeta por Short
│   └─ Video 6 - .../     ← una carpeta por video largo
├─ Miniatura/             ← miniaturas finales
├─ Recursos/              ← mapas descargados (no está en git)
└─ Render/                ← los MP4 terminados (no está en git)
```

**Truco de oro:** para un video nuevo, **copia la carpeta del último video que salió bien** y cambia el contenido. Las mejores plantillas son:
- Short: `Guiones/Shorts/S04 - Saint-Nazaire/`
- Largo: `Guiones/Video 6 - Crimea/`

---

## PARTE 3: Elegir el tema (`/ideas`, fase 1)

1. En Claude escribe **`/ideas`**.
2. Claude le pide a Codex de 8 a 10 temas. Mezcla temas de **noticias recientes** y temas que la gente **busca siempre** ("why did Japan attack Pearl Harbor").
3. Claude mide la competencia: cuántas vistas tienen los videos de ese tema y cuántos se subieron este año.
4. **Tú eliges** el tema.

¿Qué tema conviene? Uno que **mucha gente busca** pero que **pocos videos nuevos** cubren. Los títulos que mejor funcionan son preguntas:
- "Why Did Japan Attack Pearl Harbor?"
- "Why Britain Blew Up Its Own Warship"
- "Why Hitler Never Invaded Switzerland" (formato que vamos a probar)

---

## PARTE 4: Crear el hook (`/ideas`, fase 2)

Codex propone 3 hooks y **tú eliges uno**. Cada hook tiene dos partes que van **juntas**:

- **Hook auditivo:** la primera frase, de 18 palabras como máximo, con un verbo fuerte. Ejemplo: *"This destroyer **exploded** hours after its crew rammed a dock gate."*
- **Hook visual:** lo que se ve en el primer segundo. Ejemplo: el barco explota **justo** cuando la voz dice "exploded" (hacia el segundo 0,8).

Reglas del hook:
- ❌ Nada de pantalla quieta o vacía al inicio.
- ✅ El momento más espectacular del video va **al principio**. Después se puede repetir en su escena.
- ✅ Temblor de pantalla y sonido de explosión en ese momento.
- ✅ Después del hook, una pregunta que obligue a quedarse: *"Why sacrifice a warship just to destroy a dock gate?"*
- ✅ No exageres los datos: di "around six hundred" y "helped keep…", y rotula **ANIMATED RECONSTRUCTION**.

---

## PARTE 5: Escribir el guion

Se escribe en `guion.json`, dentro de la carpeta del video. Así se ve:

```json
{
 "title": "Why Britain Blew Up Its Own Warship",
 "voice": "en-GB-RyanNeural",
 "scenes": [
  {"id": "01", "style": "3D",  "headline": "FLOATING TIME BOMB", "text": "This destroyer exploded hours after its crew rammed a dock gate."},
  {"id": "02", "style": "MAP", "headline": "28 MAR 1942",        "text": "On March twenty-eighth, nineteen forty-two, Britain targeted Saint-Nazaire."}
 ]
}
```

- **id:** el número de la escena (01, 02…).
- **style:** cómo se ve la escena.
  - `MAP`: mapa oscuro con bordes neón.
  - `3D`: toma de Blender.
  - `CHAR`: Stick actuando.
- **headline:** el titular grande de arriba. **Solo en Shorts**; en videos largos no se usa.
- **text:** lo que dice la voz. Escribe los números con letras ("nineteen forty-two") para que la voz los lea bien.

Largos recomendados:
- **Short:** 110–120 palabras, unos 45 segundos.
- **Largo:** 1.000–1.400 palabras, de 6 a 10 minutos.

Antes de seguir, pide a Codex que **revise los datos** (fechas, cifras, nombres).

---

## PARTE 6: Generar la voz

Desde la carpeta del video, en PowerShell:

```powershell
python "..\..\..\Scripts\voz.py" guion.json audio +6%
```
```powershell
python "..\..\..\Scripts\short_join.py" .
```

- El primer comando crea `audio/01.mp3`, `02.mp3`… con la voz **Ryan** (inglés británico).
  - Para Shorts usa una velocidad de `+6%` a `+8%`.
  - Para largos usa `+4%`.
- El segundo une todo en `voz.wav` y crea `timeline.json`, con el segundo exacto en que se dice cada palabra. Gracias a eso la explosión puede caer justo en "exploded".

> Si sale el error `NoAudioReceived`, vuelve a correr el comando. Es un fallo pasajero de internet.

---

## PARTE 7: Los dibujos (capas y stickers)

Codex los dibuja. Se le pide con un archivo `prompt_capas_codex.md` (copia el de la carpeta plantilla) y se ejecuta así:

```powershell
codex exec --sandbox workspace-write --skip-git-repo-check - < prompt_capas_codex.md
```

Qué pedirle:
- **Fondos SIN cosas que se muevan.** Por ejemplo, el puerto sin el barco.
- **Cada elemento suelto sobre fondo blanco:** el barco, Stick con distintas caras, aviones, flechas, íconos. El script quita el blanco solo.
- **Stick siempre igual:** cabeza redonda, brazos de palito, borde blanco tipo sticker.
- Nada de esvásticas ni insignias reales.

Si Codex se niega a dibujar algo (a veces bloquea temas de "violencia"), ese elemento se dibuja con código usando PIL.

---

## PARTE 8: Los mapas

Copia `mapa.py` de la plantilla. Con los archivos de Natural Earth, dibuja:
- fondo de relieve oscuro;
- bordes de países en **neón**;
- la zona importante resaltada;
- etiquetas pequeñas de fecha o lugar.

Lo único que cambias es **la vista**: longitud, latitud y cuánto se ve. Por ejemplo, `View(-2.2, 47.3, 4)` muestra Saint-Nazaire.

⚠️ Las fronteras de Natural Earth son las de **hoy**, no las históricas. Si el tema es antiguo, explícalo en el video o dibuja la frontera a mano.

---

## PARTE 9: Las tomas 3D con Blender (solo para el objeto clave)

Usa el 3D solo para lo más espectacular: el barco que explota o el puente que cae. Para todo lo demás bastan el mapa y Stick.

1. Copia el script de la plantilla: `blender_nazaire.py` o `blender_puente.py`.
2. Renderiza los cuadros. **Usa siempre una ruta completa** en `--out`:
   ```powershell
   & "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P blender_nazaire.py -- --shot hook --out "E:\Historias TIK\WarMap Stick\Guiones\Shorts\S05 - X\render3d\hook"
   ```
3. Para probar antes, usa `--still 30` (un solo cuadro) y mira si se ve bien.

Reglas 3D:
- 🔥 Fuego, humo y agua se hacen **en Blender**. **Nunca** pegues dibujitos 2D de explosión encima del 3D.
- 💡 Si la explosión sale **blanca y quemada**, baja la intensidad de emisión y usa un color naranja.
- 🎥 En Shorts (verticales), pon la cámara **cerca**. Una lente de 22 mm hace que el objeto llene la pantalla. Si se ve pequeño y lejos, no impresiona.

---

## PARTE 10: Armar el video (render)

`build.py` (copiado de la plantilla) pone todo junto: fondos, capas animadas, tomas 3D, voz, efectos de sonido y subtítulos.

```powershell
python build.py --prep
```
```powershell
python build.py --frame 0 0.8 5 12
```
```powershell
python build.py
```

1. `--prep` prepara las piezas.
2. `--frame` saca fotos de prueba de esos segundos. Míralas en `_prep/`: así revisas sin esperar todo el render.
3. Sin argumentos hace el **render completo** y guarda el MP4 en `Render/`.

Reglas de animación (las aprobó Franco):
- Todo se mueve: fuego que parpadea, humo que sube, aviones que cruzan, flechas que se dibujan solas, Stick que entra a escena.
- **Pocos zooms.**
- **Un sonido por cada movimiento:** whoosh, boom, clic, pop.
- **Subtítulos:** bloques de 2–3 palabras, al menos 0,65 s cada uno, letra gruesa blanca con borde negro y la palabra clave en **amarillo**.
- El audio final queda normalizado a **−14 LUFS**, el volumen estándar de YouTube.

---

## PARTE 11: Revisar antes de subir

Mira el video completo y, sobre todo, **los primeros 5 segundos cuadro por cuadro**:

- [ ] ¿Hay acción desde el cuadro 0?
- [ ] ¿La explosión o el clímax cae justo en el verbo fuerte?
- [ ] ¿Se leen los subtítulos y ninguno tapa algo importante?
- [ ] ¿Algo se ve demasiado oscuro en el celular?
- [ ] ¿Los datos dicen "around" y no exageran?

Si algo falla, se corrige y se vuelve a hacer el render.

---

## PARTE 12: Subir a YouTube (`/subida`)

1. En Claude escribe **`/subida`**.
2. Codex arma el **paquete de subida**: título más 2 alternativas, descripción, etiquetas, comentario fijado y qué revisar después.
3. Prepara el archivo:
   - **Short:** Claude lo comprime para que pese menos de 10 MB y lo sube solo.
   - **Largo:** **tú arrastras** el MP4 a YouTube Studio, porque pesa demasiado para que Claude lo suba.
4. Claude llena todo en Studio:
   - título, descripción y etiquetas;
   - idioma **Inglés (Reino Unido)**, categoría **Educación** y "no es para niños";
   - **Uso de IA: "No"**, porque son dibujos animados y una voz narradora (si algún día hay escenas fotorrealistas, la respuesta sería "Sí");
   - en Shorts, el **video relacionado**: el largo del mismo tema;
   - en largos, **3 miniaturas para Test & Compare**.
5. 🛑 **Claude se detiene antes de "Publicar".** El botón lo pulsas **tú**.
6. Después de publicar, fija el comentario que propuso Codex.

---

## PARTE 13: Medir y aprender

| Cuándo | Qué mirar | Dónde |
|---|---|---|
| 24 h | Short: **"Stayed to watch"** (quién se quedó frente a quién pasó). Largo: **CTR** (cuántos hicieron clic en la miniatura). | YouTube Studio → Analytics |
| 48 h | **Retención**: en qué segundo se va la gente. | Studio → gráfico de retención |
| Siempre | Comparar con el mejor video parecido: el Short S02 o el largo Russia–Ukraine. | — |

- ⚠️ **No cambies el título ni la miniatura** mientras corre un Test & Compare (puede durar hasta 2 semanas).
- Lo que aprendas, anótalo en `APRENDIZAJES.md`.

---

## Problemas comunes

| Problema | Solución |
|---|---|
| `NoAudioReceived` al generar la voz | Vuelve a correr el comando. |
| Blender guardó los cuadros en `C:\render3d` | Pusiste una ruta relativa en `--out`. Usa la ruta completa. |
| La explosión 3D se ve blanca | Baja la emisión (×0,3) y usa un color naranja. |
| El objeto 3D se ve pequeño en el Short | Acerca la cámara y usa una lente de 22 mm. |
| Codex responde "already has an active writer" | El chat está abierto en la app de Codex. Usa `codex queue --thread <id> --message "..." --resume`. |
| `file_upload` no acepta el video | Pesa más de 10 MB. Comprímelo o arrástralo tú. |
| Studio se congela en "Pantalla final" | No tomes capturas ahí; hazla a mano. |
| Codex no quiere dibujar un elemento | Dibújalo con PIL en el código. |

---

## Resumen en una línea

**Tema que la gente busca → hook espectacular en el segundo 0 → guion corto y exacto → voz Ryan → Codex dibuja las capas → mapa neón + Stick + una toma 3D → todo animado con sonido → revisar los primeros 5 s → /subida → tú pulsas Publicar → medir a las 24 y 48 h.**

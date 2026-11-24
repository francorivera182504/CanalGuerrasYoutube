# S05 — Why Tanks Are Called 'Tanks'

Inputs aprobados: `guion.json`, `timeline.json`, `voz.wav` y `audio/`. No se editan.

## Reproducir

Desde esta carpeta, con Python 3.14, Pillow, NumPy, SciPy y pyshp:

```powershell
python build.py --prep
python render_all_3d.py
python build.py
python review.py
python qa.py
```

`build.py --frame 0 .2 1.2 3 26.8 40.7 48.5` guarda muestras en `_prep/`. El render completo exige todos los PNG; no acepta sustitutos ni placeholders. `render_all_3d.py --still hook cross stall crew` hace pruebas de encuadre. Todas las llamadas a Blender llevan `--out` absoluto. Los procesos largos deben lanzarse ocultos y seguirse mediante sus logs.

## Implementación

- `blender_tank.py`: Mark I macho de aproximadamente 8 m, sin torreta, orugas que rodean el casco y sponsons con cañones cortos. Luz nublada, barro procedural, cráteres, postes partidos y alambre 3D deformable. Los PNG finales son 1080×1920.
- `tank_fx.py`: funciones de FX copiadas de S04. Partículas de tierra con avance secuencial; humo volumétrico con coordenadas Object y máscaras de densidad. Sin FX dibujados sobre los planos 3D.
- `build.py`: renderer PIL derivado de S04, 12 escenas, titulares grandes arriba, 51 bloques de subtítulos de 2–3 palabras y duración mínima de 0,65 s. El texto queda dentro de x≤940 e y≤1640.
- `sound.py`: motor, eslabones, crujido metálico, alambre, sellos, pincel, pops, whooshes, tos del motor y pulso grave; produce `sfx.wav` y `sfx.json`. `master_audio.py` limita picos y normaliza a −14 LUFS.
- `mapa.py`: estilo neón de S04 y datos Natural Earth locales. En Flers, 49 iconos aparecen; 32 cruzan la línea y 17 permanecen grises por averías. La cita se añade como rótulo editorial.
- `assets/`: 11 PNG generados con la herramienta integrada image_gen, incluyendo dos poses adicionales del guardia. `prompts.json` conserva sujetos y estilo. `_prep/` contiene recortes con borde blanco y el brazo/pincel separado para animar las letras cirílicas.
- `review.py`: extrae el MP4 codificado en los tiempos pedidos, añade muestras en cortes y golpes, y genera hojas 4×3 con tiempos. `qa.py` verifica entradas, subtítulos, PNG, formato, duración, LUFS, tamaño de upload y loop.

La entrega final contiene 82 muestras y 7 hojas. La extracción selecciona índices de fotograma en una decodificación continua, incluida la última imagen, para evitar saltos por redondeo de timestamps. El mapa de Flers tiene zoom suave y entrada escalonada de fichas; los tripulantes gesticulan y el volante del motor gira. Los intervalos que el detector aún marca como baja variación están documentados para Claude en `_review/REVISION.md`.

## Sincronía y loop

El golpe principal ocurre en **crushes = 1,15 s**. Sellos, cambio de nombre, pintado, cifras y el aplastamiento en **smash** se sincronizan con `timeline.json`.

El plano final reutiliza el hook en reversa, opción expresamente permitida. El manifiesto está en `render3d/loop/reuse_manifest.json`; no necesita una segunda secuencia duplicada. En los últimos cuatro fotogramas vuelve también el subtítulo de apertura, después de terminar la palabra “you”. El primer y último fotograma del renderer son idénticos píxel a píxel.

El campo `total` y la voz duran **48,526 s**. La suma de inicio y duración de la escena 12 termina en 48,706 s; se respeta el total aprobado y se exportan **1456 fotogramas / 48,533333 s**. El timeline se conserva intacto.

## Entrega y revisión

Los videos se escriben en `Render/Shorts/S05_Tanks.mp4` y `Render/Shorts/S05_upload.mp4`. Las mediciones definitivas quedan en `render_report.json` y `_review/technical_qa.json`. La inspección visual final queda en `_review/REVISION.md`.

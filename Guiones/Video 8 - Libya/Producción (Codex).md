# Producción de Video 8 — Libya

Guion: 2166 palabras, 175 escenas, primera frase de 5 palabras. Cada escena termina una frase completa. Máster de 15:00, 1920×1080 a 30 fps. Voz Ryan generada con Scripts/voz.py a +4 %, seguida de atempo 0.8998809126 con tono preservado. Los tiempos y subtítulos proceden de las marcas de palabra originales escaladas con el audio.

Motor: engine.py, mapa.py y build.py locales, con storyboard de Libia, mapas Natural Earth, subtítulos por frases sin caja y sin titular superior. Hook ilustrado en hook2d.py sobre el mismo puerto de Benghazi del resto del vídeo. No utiliza los fotogramas de Blender.

El dron avanza desde el cuadro cero e impacta a los 0,20 segundos. La corbeta 734 ocupa más del 40 % de la altura inicial; el plano se abre al puerto. Fuego deformable multicapa, destello, chispas balísticas, agua, ondas y humo ascendente se calculan por fotograma; temblor decreciente y escora animada. No hay sprite de explosión. Se retiraron las notas editoriales; ANIMATED RECONSTRUCTION aparece solo en el ataque y el pecio. Nombres geográficos de 34 px. Los mapas tienen acercamientos suaves de seis segundos a sus lugares, barcos en navegación, conexiones que se trazan y personajes con movimiento de torso y brazo. Las frases de más de ocho segundos cambian composición a los 7,5 segundos.

Correcciones durante la revisión: márgenes transparentes de los personajes; diferenciación de carguero, petrolero y gasero; buque de desembarco distinto de Merkury para Crimea; corbeta volcada y parcialmente sumergida; barcos situados en el mar y traslados terrestres anclados a lugares; conexiones de personajes y acuerdos con puntos del mapa; retirada de dos mapas generados incorrectos de las miniaturas.

## Mediciones finales

- Máster: -14.00 LUFS; -0.82 dBTP; 393,027,137 bytes.
- Copia ligera: -15.03 LUFS; 9,613,067 bytes; 480×270 a 10 fps; vídeo H.264 de dos pasadas y audio AAC mono. Su compresión permite cumplir el límite de 10 MB; publicar el máster de 1080p.
- Decodificación completa con -xerror y -err_detect explode: ambos archivos pasan.
- Fotogramas de control y hoja cada 30 segundos extraídos del máster codificado. Estado de revisión visual final: consultar _prep/verification.json.

## Reproducción del montaje final

Desde la raíz del proyecto, con los audios y recursos ya presentes:

```powershell
python 'Guiones/Video 8 - Libya/build.py'
python 'Guiones/Video 8 - Libya/finalize.py'
python 'Guiones/Video 8 - Libya/package.py'
```

Para regenerar la voz desde el guion: Scripts/voz.py, luego Scripts/short_join.py y retime.py. retime.py conserva _prep/voz_raw.wav y _prep/timeline_raw.json para que el ajuste de tempo sea reproducible y no se aplique dos veces. prepare.py y configure.py documentan la importación inicial de V7; no son necesarios para reconstruir la versión final.

# Revisión final de Codex — S05 Tanks

Se inspeccionaron visualmente los **82 fotogramas del MP4 final**, en **7 hojas de contacto 4×3**. Incluyen todos los tiempos del hook pedidos, cada segundo desde 6 s, cortes/golpes adicionales y el último fotograma, índice 1455, a 48,500 s. `frame_manifest.json` relaciona tiempo solicitado, índice real y archivo.

## Archivos finales

| Archivo | Duración | Resolución / fps | Tamaño decimal | LUFS integrados | True peak |
|---|---:|---|---:|---:|---:|
| `Render/Shorts/S05_Tanks.mp4` | 48,533333 s | 1080×1920 / 30 | 18.483.693 bytes | −14,09 | −1,31 dBTP |
| `Render/Shorts/S05_upload.mp4` | 48,533333 s | 1080×1920 / 30 | 9.528.798 bytes | −14,11 | −1,02 dBTP |

Ambos son H.264, yuv420p, audio AAC. La copia de upload queda por debajo de 10.000.000 bytes. Se decodificaron ambos MP4 completos sin error. Las mediciones y hashes están en `../render_report.json`, `technical_qa.json` y `../delivery_manifest.json`.

## Resultado visual

- El hook arranca con la oruga grande, terreno y alambre en contacto. La oruga y las partículas ya tienen movimiento desde el primer fotograma. El golpe, SFX y shake principal caen a 1,15 s; la tierra sale durante “crushes”.
- Por 3 s se ve el rombo completo y el cañón lateral. No hay torreta moderna, insignias, cuerpos ni sangre.
- Tierra y humo de los planos 3D proceden de Blender. El icono pequeño del depósito en la escena 02 es la superposición UI autorizada. Todos los planos 3D llevan el aviso de reconstrucción.
- Se corrigieron el sello que quedaba fuera del papel, el pincel que aparecía separado antes del pintor y la escotilla que ocultaba dos cabezas. La versión final tiene los ocho Stick sentados, brazos gesticulando, volante del motor girando y escotilla cerrándose.
- Los 49 iconos entran progresivamente; 32 avanzan y 17 quedan grises atrás. No se representan destruidos. La cita y el rótulo de averías quedan separados de los subtítulos.
- Titulares y subtítulos quedan legibles y dentro del área segura. Los 51 bloques contienen 2–3 palabras y duran al menos 0,65 s. Se conservan todas las palabras de `timeline.json`.
- No se detectaron fotogramas negros. No encontré placeholders de recursos ausentes ni texto UI recortado.
- El loop reutiliza el hook en reversa, opción autorizada. Primer y último frame del renderer son idénticos. Entre los JPEG del primer y último frame codificado hay una diferencia media de 1,117 niveles RGB de 255, atribuible a compresión; el encuadre y el contenido coinciden visualmente.

## Puntos que debe mirar Claude

El detector de baja variación (`freezedetect`, −50 dB, mínimo 0,7 s) aún marca estos intervalos. **No son imágenes idénticas repetidas**: `motion_checks.json` compara fotogramas decodificados dentro de cada tramo y confirma cambios. Aun así, son los puntos más tranquilos y conviene juzgar su energía a velocidad normal:

| Intervalo | Qué ocurre |
|---|---|
| 20,967–21,733 s | Comparación depósito / vehículo cubierto; balanceo leve y gotas del grifo. |
| 33,567–34,267 s | Termina de entrar la cuadrícula de 49; zoom suave del mapa y marcador. |
| 35,467–36,400 s | Los 49 esperan antes de que “Only” dispare el avance de 32. |
| 39,800–42,200 s | Corte del interior: gestos de brazos, volante girando y cierre de escotilla; el fondo queda fijo. |

Otros puntos de atención:

- **13,250 s**: el ingeniero y su papel están entrando por la izquierda; parte de “LANDSHIP” queda momentáneamente fuera del cuadro durante la entrada. No es un titular ni un recorte persistente.
- **24,100 s**: empieza la entrada del pintor desde la izquierda; el extremo del pincel cruza primero el borde. Ya no aparece flotando en el centro antes del cuerpo.
- **25–26,8 s**: el pincel tapa brevemente la letra que está pintando. Al retirarse, desde aproximadamente 27,1 s, “ПЕТРОГРАД” se lee completo.
- **42,537–48,533 s**: el cierre usa reversa de la animación original, tal como se permitió. El alambre se recompone al retroceder hacia el inicio; no es una nueva acción histórica.

No quedan fallos técnicos bloqueantes encontrados. La posible falta de energía en los intervalos señalados es el principal punto editorial pendiente para la revisión independiente de Claude.

## Hojas de contacto

Todas están en `E:\Historias TIK\WarMap Stick\Guiones\Shorts\S05 - Tanks\_review\`:

- `sheet_01.jpg`
- `sheet_02.jpg`
- `sheet_03.jpg`
- `sheet_04.jpg`
- `sheet_05.jpg`
- `sheet_06.jpg`
- `sheet_07.jpg`

Las entradas aprobadas —guion, timeline, voz y los archivos dentro de audio— conservan sus hashes registrados en `../approved_inputs_sha256.json`. El campo `total` es 48,526 s, aunque la última duración de escena suma hasta 48,706 s; se usó el total y se redondeó a 1456 fotogramas, sin editar el timeline.

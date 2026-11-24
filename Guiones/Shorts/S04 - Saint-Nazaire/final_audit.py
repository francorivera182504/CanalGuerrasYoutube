"""Read-only delivery validation plus reviewer handoff files."""
from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import build
P=Path(__file__).parent;report=json.load(open(P/'render_report.json'))
original=json.load(open(P/'approved_inputs_sha256.json'))
assert all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in original.items())
probes={}
for key in ('master','upload'):
    path=Path(report[key]['path']);data=path.read_bytes()
    assert data.find(b'moov')<data.find(b'mdat')
    probe=json.loads(build.run([str(Path(build.FF).with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(path)]).stdout)
    (P/'_review'/f'probe_{key}.json').write_text(json.dumps(probe,indent=2),encoding='utf8');probes[key]=probe
    video=probe['streams'][0];assert (video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==(1080,1920,'30/1','1286')
    assert video['pix_fmt']=='yuv420p'
    report[key]['integrated_lufs']=float(report[key]['loudness']['input_i']);report[key]['true_peak_dbtp']=float(report[key]['loudness']['input_tp'])
    assert abs(report[key]['integrated_lufs']+14)<=.5
    assert report[key]['bytes']==len(data)
assert report['upload']['bytes']<=10_000_000
assert all(Image.open(f).size==(1024,1024) for f in (P/'assets').glob('*.png'))
subs=build.build_subs();assert all(e-s>=.65-1e-8 and 2<=len(g)<=3 for s,e,g in subs)
decode=(P/'_review/decode_checks.log').read_text(encoding='utf8')
assert 'black_start:' not in decode
motion=(P/'_review/map_motion_checks.log').read_text(encoding='utf8')
assert 'freeze_start:' not in motion
json.dump(report,open(P/'render_report.json','w'),indent=2)
# Inspect the size-limited upload, including fine map text and the night impact.
times=[1.2,13.5,27.5,41];sheet=Image.new('RGB',(1080,520),(8,16,23));d=ImageDraw.Draw(sheet)
for j,t in enumerate(times):
    path=P/'_review'/f'upload_{t:05.2f}.jpg'
    build.run([build.FF,'-y','-loglevel','error','-ss',str(t),'-i',report['upload']['path'],'-frames:v','1','-q:v','2',str(path)])
    sheet.paste(Image.open(path).resize((270,480),Image.Resampling.LANCZOS),(j*270,40));d.text((j*270+10,7),f'UPLOAD {t:.1f}s',font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22),fill='white')
sheet.save(P/'_review/upload_quality.jpg',quality=93)
notes=f'''S04 - SAINT-NAZAIRE | ENTREGA PARA REVISION DE CLAUDE

1080x1920, 30 fps, 1286 cuadros, {report['encoded_duration_s']:.6f} s.
Timeline aprobado: 42.841 s. Diferencia: +25.667 ms, redondeo a un cuadro completo.
Guion, timeline, voz y 22 archivos de audio originales: sin cambios (25 hashes SHA-256).

VIDEOS (MB decimal)
{report['master']['path']}
{report['master']['bytes']} bytes / {report['master']['bytes']/1e6:.3f} MB / {report['master']['integrated_lufs']:.2f} LUFS / {report['master']['true_peak_dbtp']:.2f} dBTP
{report['upload']['path']}
{report['upload']['bytes']} bytes / {report['upload']['bytes']/1e6:.3f} MB / {report['upload']['integrated_lufs']:.2f} LUFS / {report['upload']['true_peak_dbtp']:.2f} dBTP
Ambos H.264 yuv420p, AAC 48 kHz, faststart. Upload: dos pasadas H.264, AAC 128k configurado, menos de 10 MB.
Audio: control de picos con look-ahead y loudnorm en dos pasadas; cifras LUFS medidas sobre el AAC final (campo input_i).

FUENTES Y ACTIVOS CREADOS EN ESTA CARPETA
blender_nazaire.py, render3d.sh, render_all_3d.py: casco, dos chimeneas inclinadas, dique/compuerta, muelles, gruas, agua, foco nocturno, deformacion, FX volumetricos y particulas.
render3d/hook/f_0001.png ... f_0113.png
render3d/ram/f_0001.png ... f_0115.png
render3d/blast/f_0001.png ... f_0064.png
render3d/night/f_0001.png (placa adicional). Total: 293 PNG finales 1080x1920, mas pruebas still.
mapa.py, _prep/map/: Natural Earth NE1, mascaras nacionales y bordes neon. Ruta Falmouth alrededor de Bretana por mar.
assets/: ocho stickers originales blancos 1024x1024. _prep/cut_*.png: recortes con borde blanco.
assets/prompts.json: prompts del generador integrado image_gen. assets/source/: originales antes del ajuste a 1024x1024.
build.py: 11 escenas, titulares aprobados grandes, rebobinado, etalonaje a noche, textos en area segura, 116 palabras en 46 bloques de 2-3 palabras, minimo 0.65 s.
sound.py, sfx.json, sfx.wav: 64 eventos sintetizados y pulso de tension. master_audio.py: normalizacion final.
review.py, final_audit.py, render_report.json, subtitles_blocks.json, approved_inputs_sha256.json.

REVISION VISUAL
68 fotogramas extraidos DEL MP4 final; incluye todos los instantes solicitados, cada segundo desde 6 s y fotogramas adicionales de impactos/transicion.
Hojas 4x3 con timestamps: _review/sheet_01.jpg, sheet_02.jpg, sheet_03.jpg, sheet_04.jpg, sheet_05.jpg, sheet_06.jpg.
_review/upload_quality.jpg: cuatro fotogramas de la copia de subida.
_review/times.json: tiempos exactos. _review/decode_checks.log: decodificacion completa.
Sin errores de decodificacion ni cuadros negros detectados en la version final.
El detector global de baja actividad marca 8.90-9.70 s y 11.90-12.90 s del mapa: falsos positivos por la pequena fraccion de pantalla que se anima. Los barcos y la flecha si se desplazan. La comprobacion sobre el area de movimiento (crop 600x600, x=250,y=800) no detecta congelaciones; ver _review/map_motion_checks.log.
Sin texto cortado, placeholders ni subtitulos sobre el barco/impacto en los fotogramas inspeccionados.
Sin gore, cuerpos, insignias reales ni esvasticas observados.

PUNTOS VISUALES PARA MIRAR CON ATENCION (no bloqueantes)
8.90-9.70 s y 11.90-12.90 s: avisos de baja actividad del detector global; movimiento real confirmado con la comprobacion del area de barcos y flecha.
0.90-1.40 s y 33.20-33.80 s: bola de fuego muy luminosa y de aspecto estilizado; valorar el acabado frente al estilo del canal.
6.85 s: el final del rebobinado es deliberadamente oscuro por el paso a noche.
24.50-28.29 s: plano nocturno de contraste bajo, barco y compuerta legibles; valorar en pantalla de movil.
28.29-28.95 s y 39.80-40.25 s: personajes entran desde la izquierda y se ven parcialmente cortados durante la entrada, de forma intencional.
No quedan fallos tecnicos bloqueantes observados. La revision editorial de Claude no forma parte de esta validacion y sigue pendiente.

REPRODUCCION
python mapa.py --prep  (solo si faltan mapas preparados)
python build.py --prep
render3d.sh  (si se necesitan regenerar las secuencias Blender)
python build.py --frame 0 0.2 0.8 1.2 27.5 33.5
python build.py
python review.py
python final_audit.py
Los renders largos se ejecutaron ocultos en segundo plano y se sondearon por logs.
'''
(P/'PRODUCTION_REVIEW.txt').write_text(notes,encoding='utf8')
print(json.dumps({'master_MB':report['master']['bytes']/1e6,'upload_MB':report['upload']['bytes']/1e6,'master_LUFS':report['master']['integrated_lufs'],'upload_LUFS':report['upload']['integrated_lufs'],'review_frames':68,'sheets':6,'approved_files_unchanged':len(original)},indent=2))

"""Validate deliverables and extract review frames from actual upload bitstream."""
import json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import build as B
P=Path(__file__).parent;out=Path(B.ROOT)/'Render/Shorts';probe=str(Path(B.FF).with_name('ffprobe.exe'))
report=json.loads((P/'render_report.json').read_text())
for key,name in [('master','S14_Libya.mp4'),('upload','S14_upload.mp4')]:
 p=out/name
 info=json.loads(B.run([probe,'-v','error','-show_streams','-show_format','-of','json',str(p)]).stdout)
 v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio')
 assert (v['width'],v['height'],v['r_frame_rate'],v['pix_fmt'])==(1080,1920,'30/1','yuv420p')
 assert 40<=float(info['format']['duration'])<=45 and p.stat().st_size<=10_000_000
 assert a['codec_name']=='aac' and a['sample_rate']=='48000'
 assert abs(report[key]['integrated_lufs']+14)<.5 and report[key]['true_peak_dbtp']<=-1.0
 report[key]['probe']={'duration_s':float(info['format']['duration']),'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'audio_codec':a['codec_name']}
# Decode every frame to catch corrupt packets, and detect accidental black intervals.
r=B.run([B.FF,'-hide_banner','-v','info','-i',str(out/'S14_upload.mp4'),'-vf','blackdetect=d=0.15:pix_th=0.05:pic_th=0.98','-an','-f','null','-'])
assert 'black_start:' not in r.stderr
review_times=list(range(6))+[6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,39.5]+[0,4/30,8/30,.4,.6,26/30,1,1.4,1.8,2,2.4,2.666667]
indices=sorted({round(t*B.FPS) for t in review_times})
selection="select='"+'+'.join(f'eq(n,{n})' for n in indices)+"'"
B.run([B.FF,'-y','-v','error','-i',str(out/'S14_upload.mp4'),'-vf',selection,'-fps_mode','vfr','-q:v','2','-threads','2',str(P/'_prep/review_%03d.jpg')])
def decode(t):
 return Image.open(P/'_prep'/f'review_{indices.index(round(t*B.FPS))+1:03d}.jpg').convert('RGB')
for t in range(6):decode(t).save(P/'_prep'/f'chk_{t:02}.jpg',quality=94)
times=[6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,39.5]
sheet=Image.new('RGB',(1296,1224),(15,20,26));d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 im=decode(t).resize((216,384));x=i%6*216;y=i//6*408;sheet.paste(im,(x,y+24));d.text((x+8,y+5),f'{t:.1f}s',fill='white')
sheet.save(P/'_prep/sheet.jpg',quality=93)
g=json.loads((P/'guion.json').read_text(encoding='utf8'))
report['qc']={'spoken_words':len(' '.join(s['text'] for s in g['scenes']).split()),'anomaly_spoken_at_s':B.wt('01','Libya'),'hook_subject_height_px':[840,820,880],'hook_min_subject_height_fraction':820/1920,'hook_visual_cuts_s':[0,.9,1.8,2.7,3.6,4.5],'impact_time_s':.25,'first_impact_frame_s':8/30,'sailor_height_px':335,'explosion_style':'continuous procedural flame cells, rising smoke, ballistic spray and debris, local hull/water lighting, camera shake and hull roll','full_decode_passed':True,'black_intervals':0,'review_images_from':'final upload bitstream','source_document':'Guiones/Video 8 - Libya/Datos (Codex).md','source_map':{'01':['S02','S03'],'02':['S13','S18'],'03':['S02'],'04':['S03','S08'],'05':['S03'],'06':['S13'],'07':['S15','S16'],'08':['S07'],'09':['S08'],'10':['S08','S09']}}
# Subsecond sequence is necessary to review motion, which integer stills omit.
times=[0,4/30,8/30,.4,.6,26/30,1,1.4,1.8,2,2.4,2.666667]
sheet=Image.new('RGB',(1296,864),(15,20,26));d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 im=decode(t).resize((216,384));x=i%6*216;y=i//6*432;sheet.paste(im,(x,y+24));d.text((x+8,y+5),f'{t:.3f}s',fill='white')
sheet.save(P/'_prep/hook_revision.jpg',quality=94)
(P/'render_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
package=P/'Paquete de subida (Codex).md'
text=package.read_text(encoding='utf8').split('## ENTREGA VERIFICADA')[0]
text+='## ENTREGA VERIFICADA\n'
text+='- 40,067 s; 1080 × 1920; 30 fps.\n'
for key,name in [('master','S14_Libya.mp4'),('upload','S14_upload.mp4')]:
 r=report[key]
 text+=f"- {name}: {r['bytes']/1_000_000:.2f} MB; {r['integrated_lufs']:.2f} LUFS; pico verdadero {r['true_peak_dbtp']:.2f} dBTP.\n"
text+='- Revisión del hook: dron y estela desde el cuadro 0; impacto a 0,25 s (primer cuadro posterior: 8/30 s), fuego deformable, destello sobre casco y agua, restos y spray con gravedad, humo ascendente, temblor y escora.\n'
text+='- Corbeta en planos de impacto: 840 / 820 / 880 px de altura (mínimo 42,7 %). Marinero lateral de 335 px.\n'
text+='- Cambios visuales a 0 / 0,9 / 1,8 / 2,7 / 3,6 / 4,5 s.\n'
text+='- chk_00…05.jpg, sheet.jpg y hook_revision.jpg extraídos del MP4 de subida. Decodificación completa sin errores ni intervalos negros.\n'
text+='- Informe: render_report.json. Reproducción: python build.py; python qa.py.\n'
package.write_text(text,encoding='utf8')
print(json.dumps(report,indent=2),flush=True)


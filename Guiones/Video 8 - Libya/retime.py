"""Ajusta el montaje a 15 min sin cambiar el tono de Ryan ni cortar frases."""
import json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
FF=shutil.which('ffmpeg')
TL=json.loads((P/'timeline.json').read_text(encoding='utf-8'))
raw=P/'_prep/timeline_raw.json'
if raw.exists():TL=json.loads(raw.read_text(encoding='utf-8'))
else:
    raw.write_text(json.dumps(TL,ensure_ascii=False,indent=1),encoding='utf-8')
    shutil.copy2(P/'voz.wav',P/'_prep/voz_raw.wav')
factor=898.5/TL['total']
subprocess.run([FF,'-y','-loglevel','error','-i',str(P/'_prep/voz_raw.wav'),'-af',f'atempo={1/factor:.10f},apad,atrim=duration=898.5','-ar','48000',str(P/'voz.wav')],check=True)
for s in TL['timeline']:s['start']=round(s['start']*factor,4);s['dur']=round(s['dur']*factor,4)
for w in TL['words']:w['s']=round(w['s']*factor,4);w['e']=round(w['e']*factor,4)
TL['total']=898.5
(P/'timeline.json').write_text(json.dumps(TL,ensure_ascii=False,indent=1),encoding='utf-8')
g=json.loads((P/'guion.json').read_text(encoding='utf-8'))
for s,x in zip(g['scenes'],TL['timeline']):s['start_seconds']=x['start'];s['duration_seconds']=x['dur']
g['production_voice']={'synth':'Scripts/voz.py','voice':g['voice'],'rate':'+4%','post_atempo':1/factor,'note':'Ryan, tono preservado; ritmo final aproximado 145 palabras/min con pausas.'}
(P/'guion.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Timeline final',TL['total'],'s; atempo',1/factor)

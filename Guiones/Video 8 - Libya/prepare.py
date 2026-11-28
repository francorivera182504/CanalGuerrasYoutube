import json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[1]
prep=P/'_prep'; prep.mkdir(exist_ok=True)
old=json.loads((P/'guion.json').read_text(encoding='utf-8'))
if not (prep/'guion_antes.json').exists(): shutil.copy2(P/'guion.json',prep/'guion_antes.json')
parts=re.split(r'(?m)^([IVX]+\. .+)\n',(P/'narrativa.txt').read_text(encoding='utf-8'))
refs=[['S01','S02','S03','S04','S07','S08'],['S07','S13','S14'],['S15','S16','S13'],['S03','S08','S17','S18'],['S01','S02','S03','S19','S20','S21'],['S06','S07','S08','S09','S10','S11','S22']]
scenes=[]; t=0
for c in range(1,len(parts),2):
    chapter=parts[c]
    for text in re.split(r'(?<=[.!?])\s+',parts[c+1].strip()):
        dur=round(len(text.split())/148*60+.4,2)
        scenes.append(dict(id=f'{len(scenes)+1:03}',chapter=chapter,style='MAP',headline='',text=text,visual='Mapa real a pantalla completa con acciones de elementos ancladas al lugar; storyboard.py define encuadre y movimiento. Reconstrucciones identificadas junto a la acción.',start_seconds=round(t,2),duration_seconds=dur,sources=refs[(c-1)//2],soften=[]))
        t+=dur
old['scenes']=scenes
old['rule']='Narración inglesa revisada a partir de Datos (Codex).md, corte 28-11-2026. Frases completas por escena, sin metanarración editorial. Sin titular superior. Mapas reales a pantalla completa. Reconstrucciones rotuladas junto a la acción. Secuencias de botadura conceptuales sin ubicación o ruta ficticia. Cortes visuales como máximo cada 8 segundos; tiempos finales en timeline.json medidos con Ryan +4%.'
(P/'guion.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for f in ['engine.py','mapa.py','build.py']:
    shutil.copy2(R/'Guiones'/'Video 7 - Middle East'/f,P/f)
shutil.copy2(R/'Guiones'/'Video 7 - Middle East'/'00_stick_ref.png',P/'00_stick_ref.png')
for f in ['base.png','geo.json']:
    shutil.copy2(R/'Guiones'/'Video 7 - Middle East'/'_prep'/f,prep/f)
print(len(scenes),'scenes',sum(len(s['text'].split()) for s in scenes),'words')

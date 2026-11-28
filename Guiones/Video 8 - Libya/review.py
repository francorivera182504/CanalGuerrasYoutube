"""Preflight y comprobación visual reproducibles para V8."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import engine as E
import storyboard
P=Path(__file__).resolve().parent
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
if __name__=='__main__':
    E.init();subs=E.D['subs'];out=[]
    for i,(a,b,g) in enumerate(subs,1):out.append(f"{i}\n{stamp(a)} --> {stamp(b)}\n{' '.join(w['w'] for w in g)}\n")
    srt='\n'.join(out)
    (P/'Video8_Libya.srt').write_text(srt,encoding='utf-8')
    (Path(E.ROOT)/'Render/Video8_Libya.srt').write_text(srt,encoding='utf-8')
    for t in range(6):E.frame(t).save(P/'_prep'/f'chk_{t:03}.jpg',quality=92)
    times=list(range(0,math.ceil(E.TOTAL),30));sheet=Image.new('RGB',(4*480,math.ceil(len(times)/4)*290),(17,23,28));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=E.frame(t).resize((480,270),Image.Resampling.LANCZOS);x=i%4*480;y=i//4*290
        sheet.paste(im,(x,y));d.text((x+8,y+270),f'{t//60:02}:{t%60:02}',fill='white')
    sheet.save(P/'_prep/sheet.jpg',quality=88)
    checks={'words':sum(len(s['text'].split()) for s in E.G.values()),'scenes':len(E.ORDER),'first_sentence_words':len(E.G[E.ORDER[0]]['text'].split()),'duration':E.TOTAL,'max_visual_hold':7.5,'top_headlines':False,'black_subtitle_boxes':False,'source':'Natural Earth + generated harbour illustrations; action is reconstruction','contact_times_seconds':times,'subtitle_min_seconds':min(b-a for a,b,g in subs)}
    (P/'_prep/preflight.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))

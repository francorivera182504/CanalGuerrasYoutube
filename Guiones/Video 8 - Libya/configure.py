"""Adapta copias locales del motor V7; no escribe en V7 ni en recursos compartidos."""
import json,shutil
from pathlib import Path
from PIL import Image,ImageEnhance
P=Path(__file__).resolve().parent; R=P.parents[1]; V7=P.parent/'Video 7 - Middle East'
engine=(V7/'engine.py').read_text(encoding='utf-8')
engine=engine.replace('Video7','Video8').replace('Video6','Video8')
engine=engine.replace('PREP = os.path.join(HERE, "_prep"); R3 = os.path.join(HERE, "render3d"); CAPDIRS = [os.path.join(ROOT, "Imagenes", "Video8", "capas"), os.path.join(ROOT, "Imagenes", "Video8", "capas")]', 'PREP = os.path.join(HERE, "_prep"); R3 = os.path.join(HERE, "render3d"); CAPDIRS = [os.path.join(HERE, "assets")]')
engine=engine.replace('def headline(can, t, sid):','def headline(can, t, sid):\n    return\n')
a=engine.index('def build_subs():'); b=engine.index('# ---------------- neón',a)
engine=engine[:a]+'''def build_subs():
    groups=[]
    for sid in ORDER:
        ws=[w for w in WORDS if w['scene']==sid]
        cur=[]
        for w in ws:
            if cur and (len(cur)>=5 or len(' '.join(x['w'] for x in cur))+len(w['w'])>38):
                groups.append(cur);cur=[]
            cur.append(w)
        if cur: groups.append(cur)
    return [(g[0]['s'], min(SC[g[0]['scene']][1],groups[i+1][0]['s'] if i+1<len(groups) else TOTAL),g) for i,g in enumerate(groups)]

def subtitle(can,t):
    for a,b,g in D['subs']:
        if a<=t<b:
            put_text(can,' '.join(w['w'] for w in g),46,'WHITE',960,974,t,a,stroke=5,pop=False)
            return

''' +engine[b:]
engine=engine.replace('"-preset", "medium"','"-preset", "fast", "-threads", "2"')
engine=engine.replace('p.stdin.close(); p.wait(); return out','p.stdin.close(); code=p.wait();\n    if code: raise RuntimeError(f"ffmpeg segment {i}: {code}")\n    return out')
(P/'engine.py').write_text(engine,encoding='utf-8')
build=(V7/'build.py').read_text(encoding='utf-8').replace('Video7_MiddleEast.mp4','Video8_Libya.mp4').replace('Video7_parte_','Video8_parte_').replace('_v7_','_v8_')
build=build.replace('nw = 7','nw = 6')
(P/'build.py').write_text(build,encoding='utf-8')
# Natural Earth source texture retains its natural land colours and sea instead of empty board.
mp=(V7/'mapa.py').read_text(encoding='utf-8')
mp=mp.replace('PPD = 60','PPD = 60')
start=mp.index('    def draw(self, can):'); end=mp.index('# ---------------- render de mapa',start)
mp=mp[:start]+'''    def draw(self, can):
        d=ImageDraw.Draw(can)
        for it in self.items:
            if it[0]=='l':
                _,pts,col,w,closed,k=it
                if len(pts)>1: d.line(list(pts)+([pts[0]] if closed else []),fill=col,width=w,joint='curve')
            elif it[0]=='d':
                _,(x,y),col,r,k=it;d.ellipse((x-r,y-r,x+r,y+r),fill=col)
            else:
                _,mask_,col,k=it;can.paste(col,mask=edge_of(mask_,3).point(lambda x:int(x*.65)))
        return can

''' +mp[end:]
mp=mp.replace('enhance(0.82 * land_k)','enhance(1.15 * land_k)')
(P/'mapa.py').write_text(mp,encoding='utf-8')
# Use full-resolution Natural Earth crop with the established projection.
src=R/'Recursos/naturalearth/NE1_HR_LC_SR_W_DR/NE1_HR_LC_SR_W_DR.tif'
if src.exists():
    Image.MAX_IMAGE_PIXELS=None
    im=Image.open(src); box=(160*60,42*60,260*60,128*60)
    im=im.crop(box).convert('RGB').resize((5196,5160),Image.Resampling.LANCZOS)
    ImageEnhance.Color(im).enhance(.8).save(P/'_prep/base.png')
for name in ['crate','aid_truck','contract','jet','fire','explosion','anchor']:
    src=V7/'_prep'/f'cut_el_{name}.png'
    if src.exists():shutil.copy2(src,P/'_prep'/src.name)
print('V7 engine adapted locally')

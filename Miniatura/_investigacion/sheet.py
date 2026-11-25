import sys
from PIL import Image, ImageDraw, ImageFont
rows=[l.strip().split('|') for l in open('list.txt',encoding='utf8') if l.strip()]
f=ImageFont.truetype('arialbd.ttf',18)
for g in 'ABC':
    it=[r for r in rows if r[0]==g]
    cols=4; W,H=480,270; lab=28
    n=len(it); R=(n+cols-1)//cols
    S=Image.new('RGB',(cols*W,R*(H+lab)),'white'); d=ImageDraw.Draw(S)
    for i,(_,id,ch,v) in enumerate(it):
        im=Image.open(f'thumbs/{id}.jpg').convert('RGB').crop((0,45,480,315))
        x,y=(i%cols)*W,(i//cols)*(H+lab)
        S.paste(im,(x,y+lab)); d.text((x+6,y+4),f'{i+1}. {ch} · {v}',fill='black',font=f)
    S.save(f'sheet_{g}.jpg',quality=88)

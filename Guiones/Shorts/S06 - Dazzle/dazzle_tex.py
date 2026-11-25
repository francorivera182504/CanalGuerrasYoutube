"""Textura de camuflaje dazzle (rayas y cuñas) para el casco. 4096x1024: x = eslora, y = altura."""
from PIL import Image, ImageDraw
import random, math
random.seed(7)
W,H=4096,1024
BLK=(14,16,20); WHT=(236,238,234); BG=(112,134,156); BLU=(40,78,128); LBL=(140,172,200); GRY=(96,104,112)
im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
# bandas anchas inclinadas en direcciones opuestas por tramos (rompen proa/popa)
x=-600; band=0
while x<W+600:
    w=random.randint(110,260); ang=random.choice([-1,1])*random.uniform(0.6,1.4)
    col=[BLK,WHT,BLU,BLK,WHT,GRY][band%6]
    dx=H*ang
    d.polygon([(x,0),(x+w,0),(x+w+dx,H),(x+dx,H)],fill=col)
    x+=w+random.randint(90,230); band+=1
# cuñas grandes que cruzan bandas
for i in range(10):
    cx=random.randint(0,W); cy=random.randint(0,H); r=random.randint(250,520); a=random.uniform(0,math.pi)
    pts=[(cx+r*math.cos(a),cy+r*math.sin(a)),(cx-r*math.cos(a),cy-r*math.sin(a)),(cx+r*.35*math.cos(a+1.6),cy+r*.35*math.sin(a+1.6))]
    d.polygon(pts,fill=random.choice([BLK,WHT,BLU,LBL]))
im.save('dazzle.png')
print('ok')

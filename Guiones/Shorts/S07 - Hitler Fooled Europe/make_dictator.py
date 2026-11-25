"""Dibuja el Stick 'dictador' (estilo WarMap Stick) en 4 poses, sin insignias.
El generador de imágenes de Codex lo rechazó; se hace con PIL. Salida: assets/dictator_*.png (1024x1536, fondo blanco).
"""
import os, math
from PIL import Image, ImageDraw
HERE=os.path.dirname(os.path.abspath(__file__));S=2
UNI=(118,124,104);UNI_D=(88,94,78);BELT=(92,62,38);INK=(0,0,0);SKIN=(255,255,255);BOOT=(30,30,32);OL=14
def s(*v):return [x*S for x in v]
def line(d,pts,w,fill):
    p=[(x*S,y*S) for x,y in pts]
    d.line(p,fill=INK,width=(w+2*OL)*S,joint='curve')
    for q in (p[0],p[-1]):r=(w/2+OL)*S;d.ellipse((q[0]-r,q[1]-r,q[0]+r,q[1]+r),fill=INK)
    d.line(p,fill=fill,width=w*S,joint='curve')
    for q in p:r=w/2*S;d.ellipse((q[0]-r,q[1]-r,q[0]+r,q[1]+r),fill=fill)
def hand(d,x,y,r=40):d.ellipse(s(x-r,y-r,x+r,y+r),fill=SKIN,outline=INK,width=OL*S)
def crossed(d,x,y):
    """Mano con dedos cruzados (dos dedos en X)."""
    for ang in (-20,20):
        a=math.radians(ang-90);L=115;x2,y2=x+math.cos(a)*L+(ang/4),y+math.sin(a)*L
        line(d,[(x-ang*.8,y-10),(x2,y2)],30,SKIN)
    hand(d,x,y+12,46)
def dagger(d,x,y):
    d.polygon(s(x-22,y,x+22,y,x,y-190),fill=(205,210,218),outline=INK,width=8*S)
    d.rectangle(s(x-55,y,x+55,y+24),fill=(70,70,70),outline=INK,width=8*S);d.rectangle(s(x-15,y+24,x+15,y+95),fill=(110,70,40),outline=INK,width=8*S)
def body(d):
    # piernas y botas
    for x0 in (408,522):
        d.rounded_rectangle(s(x0,930,x0+96,1300),20*S,fill=UNI_D,outline=INK,width=OL*S)
        d.rounded_rectangle(s(x0-14,1270,x0+112,1385),28*S,fill=BOOT,outline=INK,width=OL*S)
    # torso (guerrera) con cuello, cinturón y botones
    d.rounded_rectangle(s(378,560,648,960),46*S,fill=UNI,outline=INK,width=OL*S)
    d.polygon(s(458,566,512,640,566,566),fill=UNI_D,outline=INK,width=10*S)
    d.rectangle(s(386,850,640,892),fill=BELT,outline=INK,width=10*S);d.rectangle(s(494,846,532,896),fill=(170,150,90),outline=INK,width=8*S)
    for y in (680,740,800):d.ellipse(s(504,y-9,522,y+9),fill=(60,60,50))
    for x in (410,560):d.rounded_rectangle(s(x,690,x+58,740),8*S,outline=INK,width=8*S,fill=UNI)
def head(d,face):
    cx,cy,r=512,385,165
    d.ellipse(s(cx-r,cy-r,cx+r,cy+r),fill=SKIN,outline=INK,width=OL*S)
    # flequillo de lado (negro) que asoma bajo la gorra
    d.polygon(s(cx-140,cy-110,cx+30,cy-120,cx-60,cy-40,cx-115,cy-20),fill=INK)
    # gorra de plato sin insignia
    d.ellipse(s(cx-200,cy-250,cx+200,cy-110),fill=UNI,outline=INK,width=OL*S)
    d.rounded_rectangle(s(cx-150,cy-170,cx+150,cy-108),14*S,fill=UNI_D,outline=INK,width=OL*S)
    d.chord(s(cx-150,cy-150,cx+150,cy-50),0,180,fill=INK)
    ey=cy+20
    if face=='shock':
        for ex in (cx-62,cx+62):d.ellipse(s(ex-26,ey-26,ex+26,ey+26),fill=SKIN,outline=INK,width=8*S);d.ellipse(s(ex-9,ey-9,ex+9,ey+9),fill=INK)
    else:
        for ex in (cx-62,cx+62):d.ellipse(s(ex-14,ey-14,ex+14,ey+14),fill=INK)
    if face=='smug':
        d.line(s(cx-90,ey-50,cx-35,ey-38),fill=INK,width=9*S);d.line(s(cx+35,ey-58,cx+90,ey-40),fill=INK,width=9*S)
    # bigote corto
    d.rounded_rectangle(s(cx-30,cy+70,cx+30,cy+100),6*S,fill=INK)
    if face=='shock':d.ellipse(s(cx-28,cy+108,cx+28,cy+160),fill=(120,30,30),outline=INK,width=8*S)
    elif face=='smug':d.arc(s(cx-20,cy+80,cx+60,cy+130),20,120,fill=INK,width=9*S)
    else:d.arc(s(cx-50,cy+70,cx+50,cy+130),25,155,fill=INK,width=9*S)
def sweat(d,x,y):d.polygon(s(x,y,x-16,y+34,x+16,y+34),fill=(120,190,255),outline=INK,width=6*S);d.ellipse(s(x-16,y+20,x+16,y+52),fill=(120,190,255),outline=INK,width=6*S)
def make(pose):
    im=Image.new('RGB',(1024*S,1536*S),'white');d=ImageDraw.Draw(im)
    if pose=='promise':
        crossed_xy=(700,900)
        line(d,[(640,610),(690,760),(672,880)],58,UNI)  # brazo izquierdo hacia atrás
        body(d);head(d,'promise')
        line(d,[(392,610),(300,560),(282,410)],58,UNI);hand(d,282,370,44)
        crossed(d,*crossed_xy)
    elif pose=='smug':
        body(d)
        line(d,[(392,620),(420,760),(610,740)],58,UNI);line(d,[(634,620),(606,770),(420,750)],58,UNI)
        hand(d,612,738,36);hand(d,418,748,36);head(d,'smug')
    elif pose=='shock':
        body(d)
        line(d,[(392,610),(300,520),(330,360)],58,UNI);line(d,[(634,610),(726,520),(694,360)],58,UNI)
        head(d,'shock');hand(d,346,350,42);hand(d,678,350,42);sweat(d,250,250);sweat(d,770,230)
    elif pose=='handshake':
        line(d,[(400,620),(352,760),(345,880)],58,UNI)
        dagger(d,320,860)
        body(d);head(d,'promise')
        line(d,[(634,620),(780,700),(905,690)],58,UNI);hand(d,930,690,42)
    out=im.resize((1024,1536),Image.LANCZOS);out.save(os.path.join(HERE,'assets',f'dictator_{pose}.png'))
for p in ('promise','smug','shock','handshake'):make(p)
print('ok')

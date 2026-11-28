"""Recreación ilustrada: geometría animada, sin sprite de explosión."""
import math
from PIL import Image, ImageDraw
import engine as E

def render(t):
    E.init()
    if 'harbour2d' not in E.D:
        E.D['harbour2d']=Image.open(E.HERE+'/assets/benghazi.png').convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
    can=E.D['harbour2d'].copy()
    # Abrir desde el casco en primer plano hacia el puerto.
    pull=E.ramp(t,1.1,7.8)
    size=int(E.lerp(1720,1120,pull))//4*4
    ship,_=E.icon('el_corvette',size)
    hit=max(0,t-.2)
    heel=E.lerp(0,-12,E.ramp(t,.22,5))+math.sin(hit*7)*3*math.exp(-hit*.8)
    ship=ship.rotate(heel,Image.Resampling.BICUBIC,expand=True)
    sx=E.lerp(960,1050,pull);sy=E.lerp(525,650,pull)+20*E.ramp(t,2,9)
    can.paste(ship,(int(sx-ship.width/2),int(sy-ship.height/2)),ship)
    cx=sx+size*.25;cy=sy+size*.12
    d=ImageDraw.Draw(can)
    # Dron ya en movimiento desde el cuadro cero; impacto a 0.20 s.
    if t<.2:
        x=E.lerp(260,cx,t/.2);y=E.lerp(910,cy,t/.2)
        for j in range(4):
            d.line((x-280-j*16,y+50+j*7,x-35,y+20),fill=(210,242,245),width=7-j)
        usv,_=E.icon('el_usv',240)
        can.paste(usv,(int(x-usv.width/2),int(y-usv.height/2)),usv)
    if t>=.2:
        fx=Image.new('RGBA',can.size);d=ImageDraw.Draw(fx)
        # Columna de agua con trayectorias balísticas y caída de gotas.
        for j in range(30):
            v=hit;vx=(j-14.5)*27;vy=-(330+(j%7)*63)
            x=cx+vx*v;y=cy+vy*v+230*v*v
            if y<1040 and v<2.9:
                d.line((cx+vx*max(0,v-.12),cy+vy*max(0,v-.12)+230*max(0,v-.12)**2,x,y),fill=(202,238,247,210),width=max(2,12-int(v*3)))
                d.ellipse((x-5,y-8,x+5,y+8),fill=(240,252,255,230))
        # Humo: cada lóbulo asciende, se ensancha, deriva y pierde opacidad.
        for j in range(21):
            age=hit-j*.105
            if age<0:continue
            r=23+age*24+(j%3)*7
            x=cx+age*35+math.sin(j*2.4+age)*age*19
            y=cy-45-age*105-j*5
            alpha=int(max(0,185-age*21))
            pts=[(x+math.cos(i*math.tau/18)*r*(1+.14*math.sin(i*3+j+age)),y+math.sin(i*math.tau/18)*r*.85) for i in range(18)]
            d.polygon(pts,fill=(58+j%3*9,62+j%3*9,65+j%3*9,alpha))
        # Boule de feu déformée à chaque image, plusieurs couches imbriquées.
        if hit<3.6:
            radius=(30+235*(1-math.exp(-hit*7)))*max(.08,1-hit/3.8)
            for scale,col in [(1,(239,69,22,245)),(.78,(255,145,25,255)),(.49,(255,220,93,255)),(.22,(255,251,210,255))]:
                pts=[]
                for i in range(64):
                    ang=i*math.tau/64
                    rr=radius*scale*(1+.085*math.sin(ang*5-hit*11)+.045*math.sin(ang*9+hit*16))
                    pts.append((cx+math.cos(ang)*rr,cy-45-hit*23+math.sin(ang)*rr*(1+hit*.16)))
                d.polygon(pts,fill=col)
        for j in range(45):
            age=hit;ang=j*2.399;speed=140+(j%9)*48
            x=cx+math.cos(ang)*speed*age;y=cy-40+math.sin(ang)*speed*age+170*age*age
            if age<1.8:
                d.line((x-math.cos(ang)*22,y-math.sin(ang)*22,x,y),fill=(255,210,80,int(255*(1-age/1.8))),width=3)
        # Ondas de choque sobre la superficie.
        for j in range(3):
            r=(hit*180+j*53)%650
            d.arc((cx-r,cy-r*.16,cx+r,cy+r*.16),0,360,fill=(205,235,240,int(155*(1-r/650))),width=4)
        can=Image.alpha_composite(can.convert('RGBA'),fx).convert('RGB')
        if hit<.16:can=Image.blend(can,Image.new('RGB',can.size,(255,244,215)),.7*(1-hit/.16))
        # Temblor decreciente sin bordes ni repetición de píxeles.
        amp=22*math.exp(-hit*1.8)
        dx=math.sin(hit*91)*amp;dy=math.cos(hit*73)*amp
        can=can.transform(can.size,Image.Transform.AFFINE,(.97,0,29+dx,0,.97,16+dy),Image.Resampling.BILINEAR)
    E.put_text(can,'ANIMATED RECONSTRUCTION',25,'WHITE',960,873,t,-1,pop=False,stroke=4)
    if t>4:E.put_text(can,'BENGHAZI, LIBYA',38,'WHITE',330,390,t,4,stroke=4)
    E.subtitle(can,t)
    return can

"""S10 Doss. S03 frame-by-frame PIL renderer, portrait safe layout.
python build.py --prep | --frame 0 .2 .8 1 | no arguments = complete render.
Approved guion, timeline and voice are read-only inputs.
"""
import json, math, os, subprocess, sys, re, wave, hashlib
from pathlib import Path
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageChops
from scipy import ndimage
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(HERE,'..','..','..'))
PREP=os.path.join(HERE,'_prep'); R3=os.path.join(HERE,'render3d'); CAP=os.path.join(HERE,'assets')
FF=r'C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
FONT=r'C:\Windows\Fonts\ariblk.ttf'; HFONT=SFONT=FONT
W,H,FPS=1080,1920,30; YEL=(255,214,40); WHITE=(255,255,255); BLUE=(65,165,255); RED=(255,75,55); GREEN=(65,225,170)
TL=json.load(open(os.path.join(HERE,'timeline.json'),encoding='utf8')); WORDS=TL['words']; TOTAL=TL['total']
SCRIPT=json.load(open(os.path.join(HERE,'guion.json'),encoding='utf8'))
SC={s['id']:(s['start'],s['start']+s['dur']) for s in TL['timeline']}
def wt(scene,word):return next(w['s'] for w in WORDS if w['scene']==scene and w['w'].lower().strip('.,?!')==word.lower())
D={}

def ease(x, kind="cubic"):
    x = min(1.0, max(0.0, x))
    if kind == "back":
        c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == "sine": return -(math.cos(math.pi * x) - 1) / 2
    if kind == "inout": return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    return 1 - (1 - x) ** 3
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind="inout"): return ease((t - t0) / max(1e-6, t1 - t0), kind)

def cutout(path, thr=245):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).copy()
    white = (a[..., :3] >= thr).all(-1)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    alpha = np.asarray(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    a[..., 3] = alpha
    out = Image.fromarray(a); return out.crop(out.getbbox())


def icon(name, size, flip=False):
    key = (name, int(size), flip)
    if key not in D["icons"]:
        im = Image.open(os.path.join(PREP, "cut_" + name + ".png"))
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = size / max(im.size); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        sh = im.getchannel("A").point(lambda v: int(v * 0.55)).filter(ImageFilter.GaussianBlur(max(2, size / 30)))
        D["icons"][key] = (im, sh)
        if len(D["icons"]) > 120: D["icons"].clear(); D["icons"][key] = (im, sh)
    return D["icons"][key]

def put_icon(can, name, size, xy, t, t0, t1=None, flip=False, bob=True):
    """Ícono con 'pop' de entrada (easeOutBack) y salida encogiendo."""
    if t < t0 or (t1 is not None and t >= t1 + 0.2): return
    k = ease((t - t0) / 0.28, "back")
    if t1 is not None and t > t1: k *= 1 - ease((t - t1) / 0.2)
    if k <= 0.03: return
    sz = size * k if k < 0.999 or k > 1.001 else size
    im, sh = icon(name, round(sz / 4) * 4 if abs(k - 1) > 1e-3 else size, flip)
    x, y = xy
    if bob: y += 5 * math.sin(2 * math.pi * 0.7 * (t - t0))
    x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    can.paste((0, 0, 0), (x0 + int(size / 24), y0 + int(size / 14)), sh)
    can.paste(im, (x0, y0), im)

def text_img(s, size, fill, stroke=10, font=None):
    font = font or FONT; key = (s, size, fill, stroke, font)
    if key not in D["texts"]:
        f = ImageFont.truetype(font, size); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8))
        ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        D["texts"][key] = im
    return D["texts"][key]

def put_text(can, s, size, fill, cx, cy, t, t0, stroke=10, pop=True, font=None):
    im = text_img(s, size, fill, stroke, font)
    if pop and t - t0 < 0.22:
        k = max(0.05, ease((t - t0) / 0.22, "back")); im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BILINEAR)
    can.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


class Neon:
    def __init__(self): self.items = []
    def line(self, pts, col, w=7, closed=False, k=1.0): self.items.append(("l", pts, col, w, closed, k))
    def dot(self, xy, col, r, k=1.0): self.items.append(("d", xy, col, r, k))
    def draw(self, can):
        if not self.items: return can
        gl = Image.new("RGB", (W // 2, H // 2)); gd = ImageDraw.Draw(gl)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = pts + [pts[0]] if closed else pts
                gd.line([(x / 2, y / 2) for x, y in p], fill=tuple(int(c * k) for c in col), width=max(3, int(w * 0.9)), joint="curve")
            else:
                _, (x, y), col, r, k = it; r2 = r * 1.4 / 2
                gd.ellipse((x / 2 - r2, y / 2 - r2, x / 2 + r2, y / 2 + r2), fill=tuple(int(c * k) for c in col))
        g1 = gl.filter(ImageFilter.GaussianBlur(10)); g2 = gl.filter(ImageFilter.GaussianBlur(3))
        glow = ImageChops.add(ImageChops.add(g1, g1), g2).resize((W, H), Image.BILINEAR)
        can = ImageChops.add(can, glow); d = ImageDraw.Draw(can)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = pts + [pts[0]] if closed else pts
                d.line(p, fill=tuple(int(lerp(c, 255, 0.15)) for c in col), width=w, joint="curve")
                d.line(p, fill=(255, 235, 225), width=2, joint="curve")
            else:
                _, (x, y), col, r, k = it
                d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=(255, 250, 245))
        return can

def partial(pts, frac):
    """Primeros `frac` de una polilínea (con punta interpolada)."""
    if frac >= 0.999: return pts, True
    n = frac * len(pts); i = int(n)
    if i < 1: return pts[:1], False
    out = pts[:i]; a = pts[i - 1]; b = pts[i % len(pts)]; f = n - i
    out = out + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
    return out, False

def arrow(neon, p0, p1, frac, col, w=10, bend=0.18):
    """Flecha curva neón dibujándose de p0 a p1."""
    if frac <= 0: return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2; dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c = (mx - dy * bend, my + dx * bend)
    n = 30; pts = []
    for i in range(int(n * frac) + 1):
        u = i / n; pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]))
    if len(pts) < 2: return
    neon.line(pts, col, w)
    (ax, ay), (bx, by) = pts[-2], pts[-1]; ang = math.atan2(by - ay, bx - ax); L = w * 3.2
    head = [(bx + math.cos(ang + a) * L, by + math.sin(ang + a) * L) for a in (2.6, math.pi, -2.6)]
    neon.line([head[0], (bx + math.cos(ang) * L * 0.6, by + math.sin(ang) * L * 0.6), head[2]], col, w)



# ---------------- S10 Doss: escenas ----------------
import mapa
ASSETS=('doss_medic','doss_rope','wounded','mockers','medal')
COUNTS={'hook':236}
OKI=(127.8,26.35)
def prep():
    os.makedirs(PREP,exist_ok=True)
    for n in ASSETS:
        im=Image.open(os.path.join(CAP,n+'.png')).convert('RGBA');arr=np.asarray(im)
        ink=np.min(arr[:,:,:3],axis=2)<235
        lab,num=ndimage.label(ink);sizes=np.bincount(lab.ravel());sizes[0]=0
        keep=[i for i in range(1,num+1) if sizes[i]>max(60,sizes.max()*.01)]
        fg=ndimage.binary_fill_holes(ndimage.binary_closing(np.isin(lab,keep),iterations=2))
        white=(arr[:,:,:3]>238).all(-1);wl,_=ndimage.label(white)
        border=set(np.unique(np.r_[wl[0],wl[-1],wl[:,0],wl[:,-1]]))-{0}
        fg&=~np.isin(wl,list(border))
        im.putalpha(Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45)));im=im.crop(im.getbbox())
        padded=Image.new('RGBA',(im.width+32,im.height+32));padded.paste(im,(16,16))
        b=padded.getchannel('A').filter(ImageFilter.MaxFilter(25));out=Image.new('RGBA',padded.size,'white');out.putalpha(b);out.alpha_composite(padded)
        out.save(os.path.join(PREP,'cut_'+n+'.png'))
    mapa.load()
    v=mapa.View(131,31,24);im,n=mapa.render(v,[(mapa.country('Japan'),RED,.22)])
    n.edge(mapa.mask(v,mapa.country('Japan')),RED,.7)
    arr=np.asarray(im).copy();dark=arr.sum(-1)<30;arr[dark]=(4,14,30);im=Image.fromarray(arr)
    n.draw(im).save(os.path.join(PREP,'map_pacific.png'))
    D['view']=v;init();print('PREP COMPLETE',flush=True)

def build_subs():
    groups=[]
    for scene in TL['timeline']:
        sid=scene['id'];ws=[w.copy() for w in WORDS if w['scene']==sid];n=len(ws);a,b=SC[sid];b=min(b,TOTAL)
        starts=[w['s'] for w in ws];starts[0]=a
        @lru_cache(None)
        def solve(i):
            if i==n:return 0,[]
            best=(1e9,[])
            for count in (1,2,3):
                j=i+count
                if j>n:continue
                tail=solve(j)
                if tail[0]>=1e8:continue
                end=starts[j] if j<n else b;dur=end-starts[i]
                penalty=max(0,.65-dur)**2*1000+(dur-1)**2+(.03 if count==2 else 0)+(.6 if count==1 else 0)
                if penalty+tail[0]<best[0]:best=(penalty+tail[0],[(starts[i],end,ws[i:j])]+tail[1])
            return best
        blocks=solve(0)[1];ss=[x[0] for x in blocks]+[b]
        for i in range(len(blocks)-1,-1,-1):ss[i]=min(ss[i],ss[i+1]-.65)
        ss[0]=max(a,ss[0])
        for i in range(1,len(blocks)):ss[i]=max(ss[i],ss[i-1]+.65)
        for i,(_,_,g) in enumerate(blocks):
            for w in g:w['txt']=w['w'].upper()
            groups.append((ss[i],ss[i+1],g))
    return groups

def init():
    if D:return
    D.update(icons={},texts={},bg={},r3={});D['subs']=build_subs()
    D['map']=Image.open(os.path.join(PREP,'map_pacific.png')).convert('RGB')
    mapa.load();D['view']=mapa.View(131,31,24)
    bg=Image.new('RGB',(W,H),(10,22,34));d=ImageDraw.Draw(bg)
    for x in range(0,W,90):d.line((x,0,x,H),fill=(17,33,46),width=2)
    for y in range(0,H,90):d.line((0,y,W,y),fill=(17,33,46),width=2)
    D['board']=bg
def label(can,s,xy,size=36,col=WHITE,anchor='mm',font=FONT):
    ImageDraw.Draw(can).text(xy,s,font=ImageFont.truetype(font,size),anchor=anchor,fill=col,stroke_width=3,stroke_fill=(5,10,17))
def chip(can,s,y=500,col=YEL,x=70,size=32):
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);d=ImageDraw.Draw(can)
    d.rounded_rectangle((x,y-31-size*.2,x+40+tw,y+31+size*.2),radius=15,fill=(8,16,24),outline=col,width=3);d.text((x+20,y),s,font=f,anchor='lm',fill=col)
def cchip(can,s,cx,y,col=YEL,size=34,t=None,t0=None):
    if t is not None and t<t0:return
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);x=cx-(tw+40)/2;chip(can,s,y,col,int(x),size)
def headline(can,t,sid):
    s=next(s['headline'] for s in SCRIPT['scenes'] if s['id']==sid);size=118
    while ImageFont.truetype(FONT,size).getlength(s)>830:size-=2
    put_text(can,s,size,YEL,495,250,t,SC[sid][0],stroke=10,pop=sid not in ('01','02'))
    label(can,'WARMAP STICK',(75,92),24,(180,200,214),'lm')
def subtitle(can,t):
    look=0 if t>=math.ceil(TOTAL*FPS)/FPS-4/FPS else t
    for s,e,g in D['subs']:
        if s<=look<e:break
    else:return
    hi=max([i for i,w in enumerate(g) if w['s']<=look+.018] or [0]);fs=78
    while ImageFont.truetype(FONT,fs).getlength(' '.join(w['txt'] for w in g))>810:fs-=2
    f=ImageFont.truetype(FONT,fs);sp=f.getlength(' ');widths=[f.getlength(w['txt']) for w in g];tw=sum(widths)+sp*(len(g)-1);x=495-tw/2;d=ImageDraw.Draw(can)
    d.rounded_rectangle((x-25,1434,x+tw+25,1555),radius=20,fill=(6,12,19))
    for i,w in enumerate(g):d.text((x,1493),w['txt'],font=f,anchor='lm',fill=YEL if i==hi else WHITE,stroke_width=7,stroke_fill=(0,0,0));x+=widths[i]+sp
def board(t):
    can=D['board'].copy();d=ImageDraw.Draw(can)
    for j in range(4):  # humo que pasa
        y=470+j*230;x=(1300-(t*(60+20*j)+j*330)%1700);d.rounded_rectangle((x,y,x+260+40*j,y+40),20,fill=(22,32,42))
    return can
def sceneid(t):return next((s['id'] for s in TL['timeline'] if s['start']<=t<s['start']+s['dur']),'11')
def r3(shot,i,preview=False):
    i=min(COUNTS[shot],max(1,i));p=os.path.join(R3,shot,f'f_{i:04d}.png')
    if not os.path.exists(p):
        if not preview:raise FileNotFoundError(p)
        files=list(Path(R3,shot).glob('f_*.png'))
        if not files:return Image.new('RGB',(W,H),(40,60,80))
        p=str(min(files,key=lambda q:abs(int(q.stem.split('_')[1])-i)))
    return Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)

def moving_icon(can,name,size,xy,t,t0,angle=0,start_full=False,flip=False,alpha=1.0):
    if t<t0:return
    k=1+.055*math.sin(math.pi*min(1,max(0,(t-t0)/.3))) if start_full else ease((t-t0)/.35,'back');im,_=icon(name,max(4,round(size*k/4)*4),flip)
    if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    if alpha<1:im=im.copy();im.putalpha(im.getchannel('A').point(lambda v:int(v*alpha)))
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def stamp_word(can,s,xy,size,col,t,at,width,hh=130):
    if t<at:return
    k=ease((t-at)/.17,'back');im=Image.new('RGBA',(width,hh));d=ImageDraw.Draw(im)
    d.rounded_rectangle((7,7,width-8,hh-8),10,outline=col,width=9)
    d.text((width/2,hh/2),s,font=ImageFont.truetype(FONT,size),anchor='mm',fill=col)
    im=im.rotate(-8,Image.Resampling.BICUBIC,expand=True);im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.Resampling.BICUBIC)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def boom2d(can,xy,t,t0,r=90):
    u=t-t0
    if u<0 or u>.6:return
    k=ease(u/.25,'back');d=ImageDraw.Draw(can);x,y=xy;fade=1-max(0,(u-.3)/.3)
    for j,(col,s) in enumerate(((RED,1.0),((255,150,40),.72),(YEL,.45))):
        rr=r*k*s;pts=[(x+math.cos(a*math.pi/8)*rr*(1 if a%2 else .62),y+math.sin(a*math.pi/8)*rr*(1 if a%2 else .62)) for a in range(16)]
        d.polygon(pts,fill=tuple(int(c*fade+20*(1-fade)) for c in col))
def tracer(can,p0,p1,t,t0,t1,col=YEL):
    if not t0<=t<=t1:return
    d=ImageDraw.Draw(can)
    for j in range(3):
        k=((t-t0)*3.2+j/3)%1;a=(lerp(p0[0],p1[0],k),lerp(p0[1],p1[1],k));b=(lerp(p0[0],p1[0],min(1,k+.08)),lerp(p0[1],p1[1],min(1,k+.08)))
        d.line((a,b),fill=col,width=8)

TOP=760;EDGE=600
def cliff(can):
    """Acantilado: meseta a la izquierda, borde en EDGE, pared que cae a la derecha."""
    d=ImageDraw.Draw(can)
    pts=[(0,TOP),(EDGE,TOP),(EDGE+40,TOP+130),(EDGE+10,TOP+300),(EDGE+60,TOP+480),(EDGE+30,1420),(0,1420)]
    d.polygon(pts,fill=(70,52,40));d.line(pts[:6],fill=(160,115,75),width=8)
    for j in range(6):y=TOP+70+j*105;d.line((60+j*40,y,EDGE-30,y+12),fill=(58,42,32),width=6)
    d.rectangle((EDGE+30,1420,W,1430),fill=(90,70,50))
def battle(can,t,t0,n=3,y=TOP-40):
    for j in range(n):
        tt=t0+j*.37+((t-t0)//1.1)*1.1
        boom2d(can,(120+(j*173)%(EDGE-120),y-40*(j%2)),t,tt,70)

def mapscene(t,sid):
    a,b=SC[sid];u=t-a;v=D['view']
    z=1+.08*ease(u/(b-a),'sine');base=D['map'];big=base.resize((int(W*z),int(H*z)),Image.Resampling.BILINEAR)
    can=big.crop((int((big.width-W)/2),int((big.height-H)/2),int((big.width+W)/2),int((big.height+H)/2)))
    P=lambda lon,lat:(W/2+(v.P(lon,lat)[0]-W/2)*z,H/2+(v.P(lon,lat)[1]-H/2)*z)
    label(can,'JAPAN',P(137.5,36.5),44,(255,160,150));label(can,'PACIFIC OCEAN',P(138,27.5),34,(159,215,255))
    x,y=P(*OKI);neon=Neon();arrow(neon,P(140,22.5),(x+30,y+20),ramp(t,a+.3,a+2.6,'inout'),BLUE,10,-.2);can=neon.draw(can);d=ImageDraw.Draw(can)
    if t>=wt('03','Okinawa'):
        r=60+8*math.sin(t*6);d.ellipse((x-r,y-r,x+r,y+r),outline=YEL,width=8)
        cchip(can,'OKINAWA',x,y+120,YEL,44)
    if t>=wt('03','cliff'):cchip(can,'MAEDA ESCARPMENT',495,1300,RED,40)
    cchip(can,'MAY 1945',495,560,WHITE,40,t,wt('03','May'))
    return can

def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid=='04':
        moving_icon(can,'doss_medic',620,(495,1000+4*math.sin(u*3)),t,a)
        cchip(can,'ARMY MEDIC',495,560,BLUE,42,t,wt('04','medic'))
        cchip(can,'MUST NOT KILL',495,660,WHITE,38,t,wt('04','kill'))
        stamp_word(can,'NO RIFLE',(760,1250),62,RED,t,wt('04','rifle'),400)
    elif sid=='05':
        moving_icon(can,'mockers',520,(300,1020+5*math.sin(u*4)),t,a)
        moving_icon(can,'doss_medic',460,(800,1030),t,a+.15,flip=True)
        stamp_word(can,'COWARD?',(760,640),66,RED,t,wt('05','coward'),400)
        for j in range(3):
            if t>=a+.4+j*.4:label(can,'HA',(260+j*90,640-j*40+6*math.sin(t*8+j)),52,YEL)
    elif sid in ('06','07'):
        cliff(can)
        if sid=='06':
            c=wt('06','counterattack');neon=Neon()
            for j in range(3):arrow(neon,(80,TOP-330+j*60),(420,TOP-60),ramp(t,c+j*.12,c+.9+j*.12),RED,10,.15)
            pb=wt('06','pull');can=neon.draw(can);d=ImageDraw.Draw(can)
            for j in range(8):
                k=ramp(t,pb+j*.06,pb+1.2+j*.06);x=180+j*50+k*(EDGE+250-180-j*50);y=TOP-25+k*(1380-TOP)
                d.ellipse((x-16,y-16,x+16,y+16),fill=BLUE,outline=WHITE,width=3)
            if t>=c:battle(can,t,c,4)
            cchip(can,'JAPANESE COUNTERATTACK',495,560,RED,36,t,c)
            cchip(can,'AMERICANS PULL BACK',495,1320,BLUE,36,t,pb)
        else:
            moving_icon(can,'doss_medic',300,(EDGE-80,TOP-150+3*math.sin(u*4)),t,a)
            stamp_word(can,'HE STAYS',(780,560),58,YEL,t,wt('07','stays'),340)
            dr=wt('07','drags')
            for j in range(3):
                k=ramp(t,dr+j*.5,dr+1.3+j*.5);x=lerp(90+j*90,EDGE-200-j*70,k)
                moving_icon(can,'wounded',230,(x,TOP-50),t,a+.2+j*.15)
            battle(can,t,a+.1,3,TOP-260);tracer(can,(0,TOP-300),(EDGE,TOP-120),t,wt('07','Under'),b,RED)
    elif sid=='08':
        cliff(can);rx,ry=EDGE-20,TOP-30
        moving_icon(can,'doss_rope',330,(EDGE-150,TOP-130),t,a,start_full=True)
        cyc=2.0;k=((t-a)%cyc)/cyc;y=lerp(ry+40,1360,ease(k,'inout'));x=rx+70+20*math.sin(t*3)
        d.line((rx,ry,x,y-60),fill=(225,190,120),width=7)
        moving_icon(can,'wounded',210,(x,y),t,a,angle=80,start_full=True)
        n=1+int((t-a)//cyc);cchip(can,f'MAN #{n}',850,1250,WHITE,36)
        l=wt('08','Lord')
        if t>=l:put_text(can,'"HELP ME GET',62,YEL,495,520,t,l,stroke=8);put_text(can,'ONE MORE"',62,YEL,495,600,t,l,stroke=8)
    elif sid=='09':
        s=wt('09','saved');n=int(75*ramp(t,s,s+1.6,'cubic')) if t>=s else 0
        for j in range(n):
            x=150+(j%7)*130+(j//7%2)*60;y=440+(j//7)*58;moving_icon(can,'wounded',165,(x,y),t,s+j*.02)
        put_text(can,str(n),230,YEL,495,1290,t,s,stroke=12,pop=False)
        cchip(can,'MEN SAVED (ABOUT)',495,1150,WHITE,36,t,s)
    elif sid=='10':
        m=wt('10','Medal')
        moving_icon(can,'doss_medic',430,(270,1080),t,a)
        if t>=m:
            k=ease((t-m)/.45,'back');moving_icon(can,'medal',int(420*min(1.08,k)) or 4,(730,960+6*math.sin(t*2)),t,m,start_full=True)
            for j in range(10):
                ang=j*math.pi/5+t*.6;r=260;d.line((730+math.cos(ang)*r,960+math.sin(ang)*r,730+math.cos(ang)*(r+55),960+math.sin(ang)*(r+55)),fill=YEL,width=8)
        cchip(can,'MEDAL OF HONOR',495,560,YEL,44,t,m)
        stamp_word(can,'NEVER CARRIED A GUN',(495,1300),46,RED,t,wt('10','never'),640)
    else:
        cliff(can);moving_icon(can,'doss_rope',360,(EDGE-160,TOP-140),t,a,start_full=True)
        if t>=wt('11','Would'):put_text(can,'?',300,YEL,850,1050,t,wt('11','Would'))
    return can

def reconstruction(t,sid,preview):
    can=r3('hook',int(t*FPS)+1,preview)
    if t>=wt('01','gun'):stamp_word(can,'NO GUN',(495,1260),76,RED,t,wt('01','gun'),380,150)
    if sid=='02' and t>=wt('02','One'):cchip(can,'ONE BY ONE',495,1120,YEL,46)
    return can

SHAKES=[(1/30,16,.3),(98/30,12,.26),(154/30,12,.26),(191/30,10,.24),(wt('06','counterattack'),10,.24),(wt('10','Medal'),8,.2)]
def post(can,t):
    dx=dy=0
    for at,amp,dur in SHAKES:
        dt=t-at
        if 0<=dt<dur:
            aa=amp*math.exp(-dt*13);dx+=aa*math.sin(dt*101+1);dy+=aa*math.cos(dt*83)
    if abs(dx)+abs(dy)>.3:
        big=can.resize((W+100,H+150),Image.Resampling.BILINEAR);x=round(50+dx);y=round(75+dy);can=big.crop((x,y,x+W,y+H))
    return can
def frame(t,preview=False):
    init();sid=sceneid(t);style=next(s['style'] for s in SCRIPT['scenes'] if s['id']==sid)
    can=reconstruction(t,sid,preview) if style=='3D' else (mapscene(t,sid) if style=='MAP' else charscene(t,sid))
    can=post(can,t)
    if style=='3D':label(can,'ANIMATED RECONSTRUCTION',(76,1377),25,(220,230,236),'lm')
    headline(can,t,sid);subtitle(can,t);return can

def seg(args):
    index,f0,f1,out=args
    p=subprocess.Popen([FF,'-y','-loglevel','error','-threads','2','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','medium','-crf','18','-threads','2','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for f in range(f0,f1):
        p.stdin.write(frame(f/FPS).tobytes())
        if (f-f0)%60==0:print(f'seg{index}: {f-f0}/{f1-f0}',flush=True)
    p.stdin.close()
    if p.wait():raise RuntimeError('ffmpeg segment failed')
    return out

def run(cmd):return subprocess.run(cmd,check=True,capture_output=True,text=True,encoding='utf8')
def loud_measure(path):
    r=run([FF,'-hide_banner','-i',str(path),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',r.stderr)[-1])

def render():
    # Fail immediately if any 3D frame or sticker is absent; no placeholder fallback.
    for shot,count in list(COUNTS.items()):
        missing=[i for i in range(1,count+1) if not Path(R3,shot,f'f_{i:04d}.png').exists()]
        if missing:raise RuntimeError(f'{shot}: missing {len(missing)} frames')
    subprocess.run([sys.executable,os.path.join(HERE,'sound.py')],check=True,cwd=HERE)
    tmp=Path(HERE,'_encode');tmp.mkdir(exist_ok=True)
    nf=math.ceil(TOTAL*FPS);nw=4;step=math.ceil(nf/nw)
    jobs=[(i,i*step,min(nf,(i+1)*step),str(tmp/f's{i:02d}.mp4')) for i in range(nw)]
    # Explicit worker processes avoid Windows named-pipe Pool restrictions.
    workers=[];logs=[]
    for i,f0,f1,path in jobs:
        log=open(tmp/f'segment_{i}.log','w',encoding='utf8');logs.append(log)
        workers.append(subprocess.Popen([sys.executable,'-u',__file__,'--segment',str(i),str(f0),str(f1),path],cwd=HERE,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
    codes=[p.wait() for p in workers]
    for log in logs:log.close()
    if any(codes):raise RuntimeError(f'Segment failures: {codes}; inspect _encode/segment_*.log')
    parts=[j[3] for j in jobs]
    lst=tmp/'list.txt';lst.write_text(''.join("file '"+p.replace('\\','/')+"'\n" for p in parts),encoding='utf8')
    video=tmp/'video.mp4';run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(video)])
    mix=tmp/'mix.wav';run([FF,'-y','-loglevel','error','-i',os.path.join(HERE,'voz.wav'),'-i',os.path.join(HERE,'sfx.wav'),'-filter_complex','[0:a]apad[v];[v][1:a]amix=inputs=2:normalize=0:duration=longest[a]','-map','[a]','-t',str(nf/FPS),'-c:a','pcm_s24le',str(mix)])
    m=loud_measure(mix);json.dump(m,open(tmp/'loudnorm_pass1.json','w'),indent=2)
    filt=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json"
    dest=Path(ROOT,'Render','Shorts');dest.mkdir(parents=True,exist_ok=True)
    out=dest/'S10_Doss.mp4';up=dest/'S10_upload.mp4'
    run([FF,'-y','-hide_banner','-i',str(video),'-i',str(mix),'-map','0:v','-map','1:a','-af',filt,'-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(nf/FPS),'-movflags','+faststart',str(out)])
    # Two-pass bounded upload: < 10,000,000 bytes with AAC 128k at full portrait resolution.
    bitrate=1300;passlog=str(tmp/'upload_pass')
    common=[FF,'-y','-loglevel','error','-i',str(out),'-c:v','libx264','-preset','slow','-b:v',f'{bitrate}k','-pix_fmt','yuv420p','-passlogfile',passlog]
    run(common+['-pass','1','-an','-f','null','NUL'])
    run(common+['-pass','2','-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart',str(up)])
    if up.stat().st_size>10_000_000:raise RuntimeError('Upload size exceeds 10 MB')
    report={'approved_total_s':TOTAL,'encoded_duration_s':nf/FPS,'frame_count':nf,'format':'1080x1920 30 fps','master':{'path':str(out),'bytes':out.stat().st_size,'loudness':loud_measure(out)},'upload':{'path':str(up),'bytes':up.stat().st_size,'loudness':loud_measure(up)}}
    json.dump(report,open(Path(HERE,'render_report.json'),'w'),indent=2)
    from master_audio import master
    master()

if __name__=='__main__':
    if '--segment' in sys.argv:seg((int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]))
    elif '--prep' in sys.argv:prep()
    elif '--frame' in sys.argv:
        for t in map(float,sys.argv[sys.argv.index('--frame')+1:]):frame(t,True).save(os.path.join(PREP,f'test_{t:05.2f}.jpg'),quality=92)
    else:render()

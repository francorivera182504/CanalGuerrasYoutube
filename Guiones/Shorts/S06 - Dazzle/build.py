"""S06 Dazzle. S03 frame-by-frame PIL renderer, portrait safe layout.
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


# ---------------- S06 Dazzle: escenas ----------------
import mapa
ASSETS=('captain_scope','captain_confused','captain_shock','artist','ship_grey','ship_dazzle','torpedo','painters_hull')
COUNTS={'scope':204,'aim':169,'turn':182,'miss':86}
SEA=(18,52,78)
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
    if not Path(mapa.PREP,'geo.json').exists():mapa.prep()
    mapa.load()
    v=mapa.View(-9,53.2,30);im,n=mapa.render(v,[(mapa.country('United Kingdom'),BLUE,.22)])
    n.edge(mapa.mask(v,mapa.country('United Kingdom')),BLUE,.7);n.draw(im).save(os.path.join(PREP,'map_atlantic.png'))
    init();print('PREP COMPLETE',flush=True)

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
    D['map_atlantic']=Image.open(os.path.join(PREP,'map_atlantic.png')).convert('RGB')
    bg=Image.new('RGB',(W,H),(10,22,34));d=ImageDraw.Draw(bg)
    for x in range(0,W,90):d.line((x,0,x,H),fill=(17,33,46),width=2)
    for y in range(0,H,90):d.line((0,y,W,y),fill=(17,33,46),width=2)
    D['board']=bg
    m=Image.new('L',(W,H),0);ImageDraw.Draw(m).ellipse((CX-R,CY-R,CX+R,CY+R),fill=255);D['scope']=m.filter(ImageFilter.GaussianBlur(10))
def label(can,s,xy,size=36,col=WHITE,anchor='mm',font=FONT):
    ImageDraw.Draw(can).text(xy,s,font=ImageFont.truetype(font,size),anchor=anchor,fill=col,stroke_width=3,stroke_fill=(5,10,17))
def chip(can,s,y=500,col=YEL,x=70,size=32):
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);d=ImageDraw.Draw(can)
    d.rounded_rectangle((x,y-31,x+40+tw,y+31),radius=15,fill=(8,16,24),outline=col,width=2);d.text((x+20,y),s,font=f,anchor='lm',fill=col)
def cchip(can,s,cx,y,col=YEL,size=34,t=None,t0=None):
    if t is not None and t<t0:return
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);x=cx-(tw+40)/2;chip(can,s,y,col,int(x),size)
def headline(can,t,sid):
    s=next(s['headline'] for s in SCRIPT['scenes'] if s['id']==sid);size=118
    while ImageFont.truetype(FONT,size).getlength(s)>830:size-=2
    put_text(can,s,size,YEL,495,250,t,SC[sid][0],stroke=10,pop=sid not in ('01','02','12'))
    label(can,'WARMAP STICK  /  YOU ARE THE SOLDIER',(75,92),24,(180,200,214),'lm')
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
    can=D['board'].copy();d=ImageDraw.Draw(can);y=570+(t*72)%760;d.line((55,y,930,y),fill=(23,55,69),width=3);return can
def sceneid(t):return next((s['id'] for s in TL['timeline'] if s['start']<=t<s['start']+s['dur']),'12')
def r3(shot,i,preview=False):
    i=min(COUNTS[shot],max(1,i));p=os.path.join(R3,shot,f'f_{i:04d}.png')
    if not os.path.exists(p):
        if not preview:raise FileNotFoundError(p)
        files=list(Path(R3,shot).glob('f_*.png'))+list(Path(R3,'test_'+shot).glob('still_*.png'))
        if not files:return Image.new('RGB',(W,H),(40,60,80))
        p=str(min(files,key=lambda q:abs(int(q.stem.split('_')[1])-i)))
    return Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)

CX,CY,R=495,905,455
def periscope(can,t):
    """Vista de periscopio: fuera del círculo oscuro, retícula con marcas (UI)."""
    dark=Image.new('RGB',(W,H),(4,8,12));can=Image.composite(can,dark,D['scope']);d=ImageDraw.Draw(can)
    d.ellipse((CX-R,CY-R,CX+R,CY+R),outline=(10,14,18),width=18)
    col=(20,24,28)
    d.line((CX-R,CY,CX+R,CY),fill=col,width=3);d.line((CX,CY-R,CX,CY+R),fill=col,width=3)
    for k in range(-8,9):
        if k==0:continue
        x=CX+k*50;h=18 if k%2==0 else 10;d.line((x,CY-h,x,CY+h),fill=col,width=3)
    return can

def reconstruction(t,sid,preview):
    a,b=SC[sid];u=t-a
    if sid in ('01','02'):can=periscope(r3('scope',int(t*FPS)+1,preview),t)
    elif sid=='12':
        # Vuelve hacia atrás al cuadro 1 del periscopio: el último fotograma = el primero (loop).
        end=math.ceil(TOTAL*FPS)/FPS;i=1+round((end-1/FPS-t)*FPS*(66/max(1,(end-a)*FPS)))
        can=periscope(r3('scope',max(1,i),preview),t)
        if wt('12','safer')<=t<wt('12','Would'):cchip(can,'CREW MORALE  ↑',495,1290,GREEN,40)
    elif sid=='06':can=r3('aim',int(u*FPS)+1,preview)
    elif sid=='08':
        can=r3('turn',int(u*FPS)+1,preview)
        if t>=wt('08','bow'):cchip(can,'BOW?  ←',300,1150,YEL,40,t,wt('08','bow'))
        if t>=wt('08','bow')+.35:cchip(can,'→  BOW?',690,1240,YEL,40)
        if t>=wt('08','turning'):put_text(can,'?',220,RED,800,700,t,wt('08','turning'))
    elif sid=='09':
        can=r3('miss',int(u*FPS)+1,preview)
        put_icon(can,'captain_shock',360,(230,1150),t,wt('09','wrong'),bob=False)
        cchip(can,'MISSED!',700,1250,RED,40,t,wt('09','misses'))
    if sid=='06':
        put_icon(can,'torpedo',230,(250,1170),t,a+.2,bob=False)
        cchip(can,'NOT HERE',300,1290,RED,34,t,wt('06','not'))
    return can

def moving_icon(can,name,size,xy,t,t0,angle=0,start_full=False):
    if t<t0:return
    k=1+.055*math.sin(math.pi*min(1,max(0,(t-t0)/.3))) if start_full else ease((t-t0)/.35,'back');im,_=icon(name,max(4,round(size*k/4)*4))
    if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def stamp_word(can,s,xy,size,col,t,at,width,hh=130):
    if t<at:return
    k=ease((t-at)/.17,'back');im=Image.new('RGBA',(width,hh));d=ImageDraw.Draw(im)
    d.rounded_rectangle((7,7,width-8,hh-8),10,outline=col,width=9)
    d.text((width/2,hh/2),s,font=ImageFont.truetype(FONT,size),anchor='mm',fill=col)
    im=im.rotate(-8,Image.Resampling.BICUBIC,expand=True);im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.Resampling.BICUBIC)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def sea_band(can,t,y0=1080):
    d=ImageDraw.Draw(can);d.rectangle((0,y0,W,1420),fill=SEA)
    for j in range(7):
        yy=y0+18+j*48;ph=t*1.6+j
        pts=[(x,yy+6*math.sin(x/70+ph)) for x in range(0,W+20,20)];d.line(pts,fill=(40,92,128),width=3)
def bulb(can,xy,t,t0):
    if t<t0:return
    k=ease((t-t0)/.3,'back');x,y=xy;r=46*k;d=ImageDraw.Draw(can)
    for j in range(8):
        a=j*math.pi/4;d.line((x+math.cos(a)*r*1.4,y+math.sin(a)*r*1.4,x+math.cos(a)*r*1.9,y+math.sin(a)*r*1.9),fill=YEL,width=7)
    d.ellipse((x-r,y-r,x+r,y+r),fill=YEL,outline=(0,0,0),width=5);d.rectangle((x-r*.4,y+r*.8,x+r*.4,y+r*1.3),fill=(150,150,160),outline=(0,0,0),width=4)
def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid=='04':
        sea_band(can,t)
        x=lerp(-200,520,ramp(t,a,a+3.2,'cubic'));moving_icon(can,'ship_grey',640,(x,1010+5*math.sin(t*2)),t,a,1.2*math.sin(t*1.5),start_full=True)
        if t>=wt('04',"can't"):cchip(can,'NOWHERE TO HIDE',495,420,RED,38)
        if t>=wt('04','artist'):
            moving_icon(can,'artist',560,(790,760+6*math.sin(u*3)),t,wt('04','artist'))
        bulb(can,(860,420),t,wt('04','idea'))
    elif sid=='05':
        sea_band(can,t)
        y=1010+5*math.sin(t*2);k=ramp(t,wt('05','Confuse'),wt('05','Confuse')+.7)
        g,_=icon('ship_grey',860);z,_=icon('ship_dazzle',860)
        z=z.resize(g.size,Image.LANCZOS);x0,y0=int(495-g.width/2),int(y-g.height/2)
        can.paste(g,(x0,y0),g)
        if k>0:
            cut=int(g.width*k);part=z.crop((0,0,cut,z.height));can.paste(part,(x0,y0),part)
            d.line((x0+cut,y0-20,x0+cut,y0+g.height+20),fill=YEL,width=8)
        hide=wt('05','hide');
        if t>=hide:
            cchip(can,'HIDE IT',300,650,WHITE,40)
            if t>=hide+.35:d.line((180,672,420,628),fill=RED,width=12)
        if t>=wt('05','Confuse'):cchip(can,'CONFUSE IT',700,760,YEL,40)
    elif sid=='07':
        moving_icon(can,'captain_scope',760,(360,1010+4*math.sin(u*3)),t,a,start_full=True)
        # cuenta regresiva: anillo que se vacía
        cx,cy,r=800,640,120;k=ramp(t,a+.2,b-.1,'sine')
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(40,70,90),width=18)
        if k<1:d.arc((cx-r,cy-r,cx+r,cy+r),-90,-90+360*(1-k),fill=RED,width=18)
        n=max(1,3-int(k*3));label(can,str(n),(cx,cy),110,WHITE)
        cchip(can,'SPEED?',780,880,YEL,40,t,wt('07','speed'))
        cchip(can,'HEADING?',780,980,YEL,40,t,wt('07','heading'))
    elif sid=='11':
        moving_icon(can,'captain_confused',720,(330,1040+4*math.sin(u*3)),t,a,start_full=True)
        # informe del comité (papel dibujado) con sello
        px,py=740,820;sh=ease(u/.4,'back');pw,ph=int(330*sh),int(420*sh)
        if pw>10:
            d.rectangle((px-pw/2,py-ph/2,px+pw/2,py+ph/2),fill=(236,230,210),outline=(0,0,0),width=6)
            if sh>.9:
                label(can,'REPORT',(px,py-160),40,(40,40,40));label(can,'1918',(px,py-112),34,(90,90,90))
                for j in range(6):d.line((px-120,py-60+j*36,px+120-(j%3)*40,py-60+j*36),fill=(150,145,130),width=8)
        stamp_word(can,'NO PROOF',(px,py+60),52,RED,t,wt('11','proof'),320)
        
    return can

def ship_grid_icon(can,xy,size,t0,t):
    if t<t0:return
    k=ease((t-t0)/.22,'back');im,_=icon('ship_dazzle',max(8,round(size*k/4)*4))
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def sub_icon(can,xy,s=1.0,col=RED):
    x,y=xy;d=ImageDraw.Draw(can)
    d.ellipse((x-60*s,y-14*s,x+60*s,y+14*s),fill=(30,34,40),outline=col,width=4)
    d.rectangle((x-12*s,y-34*s,x+12*s,y-10*s),fill=(30,34,40),outline=col,width=4);d.line((x+4*s,y-34*s,x+4*s,y-52*s),fill=col,width=4)
def mapscene(t,sid):
    a,b=SC[sid];u=t-a
    if sid=='03':
        z=1+.04*ease(u/(b-a),'sine');base=D['map_atlantic'];big=base.resize((int(W*z),int(H*z)),Image.Resampling.BILINEAR)
        can=big.crop((int((big.width-W)/2),int((big.height-H)/2),int((big.width+W)/2),int((big.height+H)/2)))
        label(can,'BRITAIN',(690,790),46,(159,215,255))
        label(can,'ATLANTIC',(250,1040),40,(120,170,210))
        # barcos que llegan a Gran Bretaña; los submarinos aparecen y algunos barcos se hunden
        lanes=[((60,1180),(560,880)),((60,1320),(600,1000)),((120,1400),(640,1120)),((40,960),(520,820))]
        for j,(p0,p1) in enumerate(lanes):
            st=a+.2+j*.25;k=ramp(t,st,st+3.2,'cubic');x=lerp(p0[0],p1[0],k);y=lerp(p0[1],p1[1],k)
            sink=wt('03','sinking')+j*.35 if j in (0,2,3) else 99
            if t>=sink:
                s=ramp(t,sink,sink+.9);x=lerp(p0[0],p1[0],ramp(sink,st,st+3.2,'cubic'));y=lerp(p0[1],p1[1],ramp(sink,st,st+3.2,'cubic'))+70*s
                if s>=1:continue
                im,_=icon('ship_grey',200);im=im.rotate(-35*s,Image.Resampling.BICUBIC,expand=True)
                al=im.getchannel('A').point(lambda v:int(v*(1-s)));im.putalpha(al);can.paste(im,(int(x-im.width/2),int(y-im.height/2)),im)
            else:moving_icon(can,'ship_grey',200,(x,y),t,st)
        for j,(sx,sy) in enumerate(((330,1110),(420,1290),(250,930))):
            if t>=wt('03','U-boats')+j*.2:sub_icon(can,(sx+8*math.sin(t*2+j),sy),.9)
        cchip(can,'SINKING FASTER THAN REPLACED',495,1360,RED,30,t,wt('03','replaced'))
    else:
        can=board(t);d=ImageDraw.Draw(can)
        put_icon(can,'painters_hull',520,(495,620),t,a-.2)
        # rejilla de barcos dazzle que se llena rápido
        for i in range(15):
            col=i%3;row=i//3;xy=(195+col*300,930+row*82)
            ship_grid_icon(can,(xy[0]+3*math.sin(t*2+i),xy[1]),255,a+.3+i*.12,t)
        cchip(can,'BRITAIN: ~3,000',300,1345,YEL,36,t,wt('10','thousands'))
        if t>=wt('10','America'):cchip(can,'U.S.: ~1,250',740,1345,BLUE,36)
    return can

SHAKES=[(wt('01','zebra'),14,.25),(wt('05','Confuse'),9,.22),(wt('09','misses'),12,.26),(wt('11','proof'),10,.24)]
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
    out=dest/'S06_Dazzle.mp4';up=dest/'S06_upload.mp4'
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

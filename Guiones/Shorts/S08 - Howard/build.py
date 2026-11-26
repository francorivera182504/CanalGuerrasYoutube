"""S08 Howard. S03 frame-by-frame PIL renderer, portrait safe layout.
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



# ---------------- S08 Howard: escenas ----------------
import mapa
ASSETS=('pilot_cockpit','pilot_shock','p51','fighter_de','b17','medal')
COUNTS={'hook':204,'dive':172}
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
    v=mapa.View(4.6,52.3,16);im,n=mapa.render(v,[(mapa.country('United Kingdom'),BLUE,.22),(mapa.country('Germany'),RED,.22)])
    n.edge(mapa.mask(v,mapa.country('United Kingdom')),BLUE,.7);n.edge(mapa.mask(v,mapa.country('Germany')),RED,.7)
    n.draw(im).save(os.path.join(PREP,'map_europe.png'))
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
    D['map']=Image.open(os.path.join(PREP,'map_europe.png')).convert('RGB')
    mapa.load();D['view']=mapa.View(4.6,52.3,16)
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
    for j in range(5):  # nubes que pasan: sensación de vuelo
        y=520+j*190;x=(1300-(t*(160+40*j)+j*330)%1700);d.rounded_rectangle((x,y,x+240+40*j,y+34),17,fill=(20,40,56))
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
    """Estallido 2D (solo en escenas de pizarra)."""
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

GERM_T=(11.3,52.0)  # Oschersleben aprox.
def mapscene(t,sid):
    a,b=SC[sid];u=t-a;v=D['view']
    z=1+.05*ease((t-SC['03'][0])/(SC['04'][1]-SC['03'][0]),'sine');base=D['map'];big=base.resize((int(W*z),int(H*z)),Image.Resampling.BILINEAR)
    can=big.crop((int((big.width-W)/2),int((big.height-H)/2),int((big.width+W)/2),int((big.height+H)/2)))
    P=lambda lon,lat:(W/2+(v.P(lon,lat)[0]-W/2)*z,H/2+(v.P(lon,lat)[1]-H/2)*z)
    label(can,'ENGLAND',P(-.6,52.9),40,(159,215,255));label(can,'GERMANY',P(10.4,50.6),44,(255,160,150))
    s0=P(.8,52.2);s1=P(*GERM_T);neon=Neon()
    if sid=='03':
        arrow(neon,s0,s1,ramp(t,a+.2,a+3.2,'inout'),YEL,9,.1);can=neon.draw(can)
        for j in range(5):
            k=ramp(t,a+.3+j*.12,a+3.6+j*.12,'inout');x=lerp(s0[0],s1[0],k)+(j%3-1)*55;y=lerp(s0[1],s1[1],k)+(j//3)*60-30
            moving_icon(can,'b17',150,(x,y+4*math.sin(t*3+j)),t,a+.2+j*.12)
        if t>=wt('03','Germany'):
            d=ImageDraw.Draw(can);x,y=s1;r=46+6*math.sin(t*6);d.ellipse((x-r,y-r,x+r,y+r),outline=RED,width=7)
        cchip(can,'DEEP INSIDE GERMANY',495,1300,RED,36,t,wt('03','deep'))
    else:
        arrow(neon,s0,s1,1,YEL,9,.1);can=neon.draw(can)
        for j in range(5):moving_icon(can,'b17',150,(s1[0]+(j%3-1)*55,s1[1]+(j//3)*60-30+4*math.sin(t*3+j)),t,a,start_full=True)
        cx,cy=P(8.6,52.4);lose=wt('04','loses')
        for j in range(4):
            off=((0,0),(-80,-60),(-80,60),(-160,0))[j]
            if j and t>=lose:
                k=ramp(t,lose,lose+1.2,'inout');ox=off[0]-260*k*(1 if j!=2 else .6);oy=off[1]+(-330 if j==1 else 330 if j==2 else -40)*k
                moving_icon(can,'p51',130,(cx+ox,cy+oy),t,a+.3,start_full=True,alpha=max(0,1-k))
            else:moving_icon(can,'p51',150 if j==0 else 130,(cx+off[0]+6*math.sin(t*2+j),cy+off[1]),t,a+.3+j*.1)
        if t>=wt('04','Howard'):
            d=ImageDraw.Draw(can);r=95;d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=YEL,width=6)
        cchip(can,'MAJ. JAMES HOWARD',495,1200,YEL,36,t,wt('04','Howard'))
        cchip(can,'P-51 MUSTANG',495,1310,WHITE,34,t,wt('04','P-51'))
        stamp_word(can,'ALONE',(cx+40,cy-190),58,RED,t,wt('04','group'),300)
    return can

def gun_row(can,xy,t,stops,one_at):
    """4 ametralladoras: verdes; se apagan en rojo con X; la última late."""
    d=ImageDraw.Draw(can);x0,y0=xy
    for j in range(4):
        x=x0+j*150;dead=j<3 and t>=stops[j];col=RED if dead else GREEN
        d.rounded_rectangle((x-55,y0-28,x+55,y0+28),12,fill=(12,24,34),outline=col,width=6);d.rectangle((x+55,y0-9,x+95,y0+9),fill=col)
        if dead:d.line((x-40,y0-40,x+40,y0+40),fill=RED,width=10);d.line((x-40,y0+40,x+40,y0-40),fill=RED,width=10)
        elif j==3 and t>=one_at:
            r=70+10*math.sin(t*10);d.ellipse((x-r,y0-r,x+r,y0+r),outline=YEL,width=6)
            if (t*8)%1<.5:d.ellipse((x+90,y0-18,x+126,y0+18),fill=YEL)
    label(can,'GUNS',(x0-120,y0),40,WHITE)

def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid=='05':
        moving_icon(can,'pilot_shock',470,(300,1130+4*math.sin(u*3)),t,a,start_full=True)
        for j in range(3):moving_icon(can,'b17',300,(700,560+j*170+6*math.sin(t*2+j)),t,a+.2+j*.1)
        n0=wt('05','More');cnt=0
        for j in range(30):
            ti=n0+j*.07
            if t<ti:continue
            cnt+=1;rnd=(j*37%11)/11;x=560+(j%6)*80+20*math.sin(t*2+j);y=420+(j//6)*170+70*rnd
            moving_icon(can,'fighter_de',95,(x,y),t,ti)
        if cnt:cchip(can,f'{cnt}+' if cnt==30 else str(cnt),300,600,RED,90)
        if t>=wt('05','attacking'):tracer(can,(640,500),(720,640),t,wt('05','attacking'),b,RED);tracer(can,(860,880),(700,900),t,wt('05','attacking')+.2,b,RED)
    elif sid=='06':
        moving_icon(can,'pilot_cockpit',640,(470,1050+4*math.sin(u*3)),t,a,start_full=True)
        cchip(can,'NO ESCORTS NEARBY',495,560,RED,40,t,wt('06','escorts'))
        tb=wt('06','turn')
        if t>=tb:
            k=ramp(t,tb,tb+.6);d.arc((640,600,900,860),200,200+250*k,fill=YEL,width=14)
            cchip(can,'TURN BACK?',770,930,YEL,40)
    elif sid=='09':
        moving_icon(can,'pilot_cockpit',560,(420,820+4*math.sin(u*3)),t,a,start_full=True)
        s=wt('09','stop');gun_row(can,(270,1260),t,(s,s+.25,s+.5),wt('09','one'))
        if t>=wt('09','keeps'):
            for j in range(3):
                x=900-((t-wt('09','keeps'))*500+j*260)%900;moving_icon(can,'fighter_de',130,(x,520+j*90),t,wt('09','keeps'))
            tracer(can,(700,840),(980,560),t,wt('09','keeps'),b,YEL)
    elif sid=='10':
        k3=wt('10','three')
        for j in range(3):
            moving_icon(can,'fighter_de',170,(250+j*250,560),t,k3+j*.18)
            boom2d(can,(250+j*250,560),t,k3+j*.18+.05,95)
            if t>=k3+j*.18+.3:d.line((190+j*250,500,310+j*250,620),fill=RED,width=12);d.line((190+j*250,620,310+j*250,500),fill=RED,width=12)
        cchip(can,'AT LEAST 3 KILLS',495,700,YEL,40,t,k3)
        m=wt('10','Medal')
        if t>=m:
            k=ease((t-m)/.45,'back');moving_icon(can,'medal',int(460*min(1.08,k)) or 4,(495,1050+6*math.sin(t*2)),t,m,start_full=True)
            for j in range(10):
                ang=j*math.pi/5+t*.6;r=280;d.line((495+math.cos(ang)*r,1050+math.sin(ang)*r,495+math.cos(ang)*(r+60),1050+math.sin(ang)*(r+60)),fill=YEL,width=8)
    else:  # 11: uno contra treinta
        moving_icon(can,'p51',300,(230,1000+8*math.sin(t*2)),t,a,start_full=True)
        cchip(can,'1 PILOT',230,800,BLUE,40,t,wt('11','pilot'))
        cchip(can,'1 GUN',230,1200,YEL,40,t,wt('11','gun'))
        th=wt('11','Thirty')
        for j in range(30):
            if t>=th+j*.03:moving_icon(can,'fighter_de',80,(560+(j%5)*85+10*math.sin(t*2+j),620+(j//5)*110),t,th+j*.03)
        cchip(can,'30 ENEMIES',770,1330,RED,40,t,th)
        if t>=wt('11','Would'):put_text(can,'?',260,YEL,495,1060,t,wt('11','Would'))
    return can

def reconstruction(t,sid,preview):
    a,b=SC[sid];u=t-a
    if sid in ('01','02'):
        can=r3('hook',int(t*FPS)+1,preview)
        if t>=wt('01','Alone'):stamp_word(can,'ALONE',(495,1250),70,RED,t,wt('01','Alone'),360,150)
    else:
        can=r3('dive',int((t-SC['07'][0])*FPS)+1,preview)
        if sid=='08':
            cx,cy,r=790,1220,95;k=ramp(t,a,b,'sine');dd=ImageDraw.Draw(can)
            dd.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(8,16,24),outline=(40,70,90),width=14);dd.arc((cx-r,cy-r,cx+r,cy+r),-90,-90+360*k,fill=YEL,width=14)
            label(can,str(int(k*30)),(cx,cy-10),70,WHITE);label(can,'MIN',(cx,cy+48),28,WHITE)
    return can

SHAKES=[(25/30,16,.3),(91/30,12,.26),(SC['07'][0]+99/30,12,.26),(SC['07'][0]+149/30,10,.24),(wt('09','stop'),8,.2),(wt('10','Medal'),8,.2)]
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
    out=dest/'S08_Howard.mp4';up=dest/'S08_upload.mp4'
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

"""S09 Mincemeat. S03 frame-by-frame PIL renderer, portrait safe layout.
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



# ---------------- S09 Mincemeat: escenas ----------------
import mapa
ASSETS=('intel_officer','major_martin','german_agent')
COUNTS={'hook':203,'release':87}
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
    v=mapa.View(8,43,34);im,n=mapa.render(v,[(mapa.country('Italy'),BLUE,.18),(mapa.country('Greece'),RED,.2),(mapa.country('Germany'),(150,150,150),.15)])
    n.edge(mapa.mask(v,mapa.country('Italy')),BLUE,.6);n.edge(mapa.mask(v,mapa.country('Greece')),RED,.6)
    im=n.draw(im);a_=np.asarray(im).copy();a_[a_.sum(-1)<14]=(4,14,30);Image.fromarray(a_).save(os.path.join(PREP,'map_europe.png'))
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
    mapa.load();D['view']=mapa.View(8,43,34)
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

SITES={'Sicily':(14.2,37.5),'Sardinia':(9.0,40.0),'Greece':(22.0,39.3),'Huelva':(-6.95,37.2),'Berlin':(13.4,52.5),'Tunisia':(10.0,35.5)}
def mapbase(t):
    v=D['view'];z=1+.04*math.sin(t*.25);base=D['map'];big=base.resize((int(W*z),int(H*z)),Image.Resampling.BILINEAR)
    can=big.crop((int((big.width-W)/2),int((big.height-H)/2),int((big.width+W)/2),int((big.height+H)/2)))
    P=lambda lon,lat:(W/2+(v.P(lon,lat)[0]-W/2)*z,H/2+(v.P(lon,lat)[1]-H/2)*z)
    return can,P
def pulse(can,xy,t,col,r0=40):
    d=ImageDraw.Draw(can);x,y=xy;r=r0+8*math.sin(t*6);d.ellipse((x-r,y-r,x+r,y+r),outline=col,width=7);d.ellipse((x-9,y-9,x+9,y+9),fill=col)
def troops(can,p0,p1,t,t0,n=5,col=(150,150,150)):
    d=ImageDraw.Draw(can)
    for j in range(n):
        k=ramp(t,t0+j*.12,t0+1.6+j*.12,'inout');x=lerp(p0[0],p1[0],k)+(j%3-1)*26;y=lerp(p0[1],p1[1],k)+(j//3)*26
        if t>=t0+j*.12:d.rectangle((x-13,y-9,x+13,y+9),fill=col,outline=(0,0,0),width=3)
def mapscene(t,sid):
    a,b=SC[sid];u=t-a;can,P=mapbase(t);neon=Neon()
    for k in ('Sicily','Sardinia','Greece'):label(can,k.upper(),(P(*SITES[k])[0]-(70 if k=='Greece' else 0),P(*SITES[k])[1]+58),34,WHITE)
    if sid=='03':
        arrow(neon,P(*SITES['Tunisia']),P(*SITES['Sicily']),ramp(t,wt('03','invade'),wt('03','invade')+1),BLUE,10,.25);can=neon.draw(can)
        if t>=wt('03','Sicily'):pulse(can,P(*SITES['Sicily']),t,YEL)
        cchip(can,'OBVIOUS TARGET',495,1300,YEL,40,t,wt('03','obvious'))
    elif sid=='08':
        h=P(*SITES['Huelva']);label(can,'HUELVA',(h[0]+20,h[1]+50),32,(255,200,120));pulse(can,h,t,(255,200,120),30)
        arrow(neon,h,P(*SITES['Berlin']),ramp(t,wt('08','papers'),wt('08','Germans')+.4),YEL,8,-.2)
        for k in ('Greece','Sardinia'):
            if t>=wt('08',k):arrow(neon,P(*SITES['Berlin']),P(*SITES[k]),ramp(t,wt('08',k),wt('08',k)+.6),RED,9,.15)
        can=neon.draw(can)
        moving_icon(can,'german_agent',330,(780,560),t,wt('08','Germans'))
        cchip(can,'GREECE?',P(*SITES['Greece'])[0]-40,P(*SITES['Greece'])[1]-80,RED,38,t,wt('08','Greece'))
        cchip(can,'SARDINIA?',P(*SITES['Sardinia'])[0],P(*SITES['Sardinia'])[1]-80,RED,38,t,wt('08','Sardinia'))
    elif sid=='09':
        for k in ('Greece','Sardinia'):arrow(neon,P(*SITES['Berlin']),P(*SITES[k]),1,RED,9,.15)
        can=neon.draw(can)
        troops(can,P(*SITES['Berlin']),P(*SITES['Greece']),t,wt('09','reinforcements'),6)
        troops(can,P(*SITES['Berlin']),P(*SITES['Sardinia']),t,wt('09','reinforcements')+.3,5)
        moving_icon(can,'dictator_smug',360,(820,1150),t,a+.1)
        stamp_word(can,'WRONG',(495,1330),62,RED,t,wt('09','wrong'),300)
    else:  # 10
        arrow(neon,P(*SITES['Tunisia']),P(*SITES['Sicily']),ramp(t,a+.1,wt('10','land')),BLUE,14,.25);can=neon.draw(can)
        for k in ('Greece','Sardinia'):d=ImageDraw.Draw(can);x,y=P(*SITES[k]);d.line((x-30,y-30,x+30,y+30),fill=RED,width=9);d.line((x-30,y+30,x+30,y-30),fill=RED,width=9)
        boom2d(can,P(*SITES['Sicily']),t,wt('10','land'),120)
        if t>=wt('10','land')+.4:pulse(can,P(*SITES['Sicily']),t,BLUE,50)
        cchip(can,'JULY 1943',495,560,BLUE,44,t,wt('10','July'))
        moving_icon(can,'dictator_shock',360,(820,1170),t,wt('10','Sicily'))
    return can

def letter(can,xy,t,t0):
    if t<t0:return
    k=ease((t-t0)/.3,'back');x,y=xy;w,h=200*k,130*k;d=ImageDraw.Draw(can)
    d.rectangle((x-w/2,y-h/2,x+w/2,y+h/2),fill=(240,232,210),outline=(0,0,0),width=5);d.line((x-w/2,y-h/2,x,y+8*k,x+w/2,y-h/2),fill=(0,0,0),width=5)
    r=16*k;d.ellipse((x-r*1.6,y+h/4-r,x,y+h/4+r*.4),fill=RED);d.ellipse((x,y+h/4-r,x+r*1.6,y+h/4+r*.4),fill=RED);d.polygon([(x-r*1.55,y+h/4),(x+r*1.55,y+h/4),(x,y+h/4+r*1.9)],fill=RED)
def tickets(can,xy,t,t0):
    if t<t0:return
    k=ease((t-t0)/.3,'back');x,y=xy;d=ImageDraw.Draw(can)
    for j in range(2):
        ox=j*40;oy=j*30;w,h=220*k,90*k
        d.rounded_rectangle((x-w/2+ox,y-h/2+oy,x+w/2+ox,y+h/2+oy),10,fill=(250,200,70),outline=(0,0,0),width=5)
        if k>.8:d.text((x+ox,y+oy),'ADMIT ONE',font=ImageFont.truetype(FONT,26),anchor='mm',fill=(60,30,10))
def idcard(can,xy,t,t0):
    if t<t0:return
    k=ease((t-t0)/.35,'back');x,y=xy;w,h=560*k,330*k;d=ImageDraw.Draw(can)
    d.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),18,fill=(225,215,185),outline=(0,0,0),width=6)
    if k>.9:
        d.rectangle((x-w/2+30,y-h/2+40,x-w/2+200,y+h/2-40),fill=(200,190,160),outline=(0,0,0),width=4)
        for j in range(4):d.line((x-30,y-80+j*55,x+w/2-40-(j%2)*60,y-80+j*55),fill=(120,110,90),width=10)
def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid=='04':
        moving_icon(can,'intel_officer',700,(330,1030+4*math.sin(u*3)),t,a,start_full=True)
        f=wt('04','fake');idcard(can,(740,700),t,wt('04','hand'))
        stamp_word(can,'TOP SECRET',(740,700),46,RED,t,wt('04','Germans'),400)
        stamp_word(can,'FAKE',(760,960),70,YEL,t,f,280,150)
    elif sid=='05':
        m=wt('05','Major')
        if t<m:
            idcard(can,(495,820),t,a+.2);label(can,'?',(330,820),120,(90,80,60))
        else:
            moving_icon(can,'major_martin',820,(495,920+4*math.sin(u*3)),t,m)
            cchip(can,'MAJ. WILLIAM MARTIN',495,1350,YEL,42,t,m)
        cchip(can,'NEW IDENTITY',495,520,BLUE,38,t,wt('05','new'))
    elif sid=='06':
        moving_icon(can,'major_martin',520,(230,1080+4*math.sin(u*3)),t,a,start_full=True)
        letter(can,(700,560),t,wt('06','Love'));tickets(can,(700,800),t,wt('06','Theatre'))
        moving_icon(can,'briefcase',300,(720,1080+5*math.sin(t*2)),t,wt('06','briefcase'))
        stamp_word(can,'FAKE',(740,1090),66,RED,t,wt('06','fake'),260,140)
    else:  # 11
        e=wt('11','existed');al=1-ramp(t,e,e+.8)
        moving_icon(can,'major_martin',820,(495,920+4*math.sin(u*3)),t,a,start_full=True,alpha=max(.12,al))
        stamp_word(can,'NEVER EXISTED',(495,820),58,RED,t,e+.3,520,140)
        if t>=wt('11','Would'):put_text(can,'?',220,YEL,820,560,t,wt('11','Would'))
    return can

def reconstruction(t,sid,preview):
    if sid in ('01','02'):
        can=r3('hook',int(t*FPS)+1,preview)
        cchip(can,'OPERATION MINCEMEAT',495,1300,YEL,40,t,wt('01','Hitler'))
    else:
        can=r3('release',int((t-SC['07'][0])*FPS)+1,preview)
        cchip(can,'HUELVA, SPAIN · 1943',495,1300,WHITE,38,t,wt('07','Spain'))
    return can

SHAKES=[(38/30,14,.3),(wt('04','fake'),8,.2),(wt('06','fake'),8,.2),(wt('09','wrong'),8,.2),(wt('10','land'),14,.3),(wt('11','existed')+.3,9,.22)]
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
    out=dest/'S09_Mincemeat.mp4';up=dest/'S09_upload.mp4'
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

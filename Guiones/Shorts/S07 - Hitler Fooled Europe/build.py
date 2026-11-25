"""S07 How Hitler FOOLED Europe. PIL frame renderer (based on S06).
python build.py --prep | --frame 0 .2 .8 1 | no arguments = complete render."""
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


# ---------------- S07 How Hitler FOOLED Europe: escenas ----------------
import mapa
from mapa import View
ASSETS=('dictator_promise','dictator_smug','dictator_shock','dictator_handshake','chamberlain','stalin','disguised_men','french_tank','german_tank','briefcase')
COUNTS={}
GOLD=(255,190,60); GREY=(160,170,185); NIGHT=(7,11,26)
YEARS={'thirty-six':'1936','thirty-eight':'1938','thirty-nine':'1939','forty':'1940','forty-one':'1941'}
def wtn(scene,word,n=1):return [w['s'] for w in WORDS if w['scene']==scene and w['w'].lower().strip('.,?!')==word.lower()][n-1]
RHINE=[(6.1,51.9),(6.76,51.43),(6.96,50.94),(7.6,50.35),(8.27,50.0),(8.45,49.5),(8.2,48.97),(7.9,48.6),(7.55,48.0),(7.6,47.6)]
VIEWS={'rhine':View(6.6,49.6,11),'central':View(13,49.5,20),'czech':View(15.3,49.6,9.5),'poland':View(19.5,52,15),
       'lowc':View(4.2,50.1,8.5),'france':View(2.6,47.3,13),'east':View(28.5,54,22),'europe':View(19,53,38)}
PLACES={'Prague':(14.42,50.08),'Warsaw':(21.01,52.23),'Paris':(2.35,48.86),'Moscow':(37.62,55.75),'Leningrad':(30.32,59.94),'Kyiv':(30.52,50.45),'Sedan':(4.94,49.70),'Abbeville':(1.83,50.10)}
def P(v,lonlat):return VIEWS[v].P(*lonlat)
def merge(*names):
    out=[]
    for n in names:out+=mapa.country(n)
    return out
def prussia():return [r for r in mapa.country('Russia') if max(p[0] for p in r)<23]
USSR=('Russia','Belarus','Ukraine','Estonia','Latvia','Lithuania','Moldova')

def cut_asset(n):
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

def base_for(v):
    mapa.load();view=VIEWS[v];n=mapa.Neon()
    G=merge('Germany');F=mapa.country('France')
    fills={'rhine':[(G,RED,.22),(F,BLUE,.20)],'central':[(G,RED,.22),(F,BLUE,.14)],'czech':[(G,RED,.22)],
           'poland':[(merge('Germany','Austria','Czechia')+prussia(),RED,.22)],'lowc':[(G,RED,.22),(F,BLUE,.20),(merge('Belgium','Netherlands','Luxembourg'),YEL,.12)],
           'france':[(G,RED,.22),(F,BLUE,.20)],'east':[(merge('Germany','Austria','Czechia','Poland')+prussia(),RED,.24),(merge(*USSR),GOLD,.16)],
           'europe':[]}[v]
    im,n=mapa.render(view,fills,n)
    edges={'rhine':[('Germany',RED),('France',BLUE)],'central':[('Germany',RED),('Austria',WHITE),('Czechia',WHITE)],'czech':[('Germany',RED),('Czechia',YEL)],
           'poland':[('Germany',RED),('Poland',WHITE)],'lowc':[('Germany',RED),('France',BLUE),('Belgium',YEL)],'france':[('France',BLUE),('Germany',RED)],
           'east':[('Germany',RED),('Poland',RED),('Russia',GOLD),('Ukraine',GOLD),('Belarus',GOLD)],'europe':[('Germany',RED)]}[v]
    for name,col in edges:n.edge(mapa.mask(view,mapa.country(name)),col,.7)
    im=n.draw(im);im.save(os.path.join(PREP,f'map_{v}.png'))

def prep():
    os.makedirs(PREP,exist_ok=True)
    for n in ASSETS:
        if os.path.exists(os.path.join(CAP,n+'.png')):cut_asset(n)
        else:print('MISSING asset',n,flush=True)
    for v in VIEWS:base_for(v)
    init();print('PREP COMPLETE',flush=True)

def band(m,px):
    a=np.asarray(m)>127;d=ndimage.distance_transform_edt(a);return Image.fromarray(((a&(d<px))*255).astype('uint8')).filter(ImageFilter.GaussianBlur(1))
def init():
    if D:return
    D.update(icons={},texts={},r3={});D['subs']=build_subs();mapa.load()
    D['map']={v:Image.open(os.path.join(PREP,f'map_{v}.png')).convert('RGB') for v in VIEWS}
    vr=VIEWS['rhine'];west=RHINE+[(4.5,47.6),(4.5,51.9)]
    D['m_rhineland']=ImageChops.multiply(mapa.mask(vr,mapa.country('Germany')),mapa.mask(vr,[west]))
    D['m_austria_c']=mapa.mask(VIEWS['central'],mapa.country('Austria'))
    D['m_czech_c']=mapa.mask(VIEWS['central'],mapa.country('Czechia'))
    cz=mapa.mask(VIEWS['czech'],mapa.country('Czechia'));D['m_czech']=cz;D['m_sudeten']=band(cz,62)
    D['m_france_f']=mapa.mask(VIEWS['france'],mapa.country('France'))
    D['m_occupied']=mapa.mask(VIEWS['europe'],merge('Germany','Austria','Czechia','Poland','France','Belgium','Netherlands','Luxembourg','Denmark','Norway','Greece','Republic of Serbia','Croatia','Bosnia and Herzegovina','Lithuania','Latvia','Estonia','Belarus','Ukraine')+prussia())
    bg=Image.new('RGB',(W,H),(10,22,34));d=ImageDraw.Draw(bg)
    for x in range(0,W,90):d.line((x,0,x,H),fill=(17,33,46),width=2)
    for y in range(0,H,90):d.line((0,y,W,y),fill=(17,33,46),width=2)
    D['board']=bg
    night=Image.new('RGB',(W,H));d=ImageDraw.Draw(night)
    for y in range(H):k=y/H;d.line((0,y,W,y),fill=(int(lerp(4,18,k)),int(lerp(7,22,k)),int(lerp(20,44,k))))
    rng=np.random.default_rng(3)
    for _ in range(140):
        x,y=rng.integers(0,W),rng.integers(0,1250);r=rng.choice([1,1,2,3]);d.ellipse((x-r,y-r,x+r,y+r),fill=(200,210,235))
    d.rectangle((0,1330,W,H),fill=(10,14,20))
    D['night']=night

def icon(name,size,flip=False):
    key=(name,int(size),flip)
    if key not in D['icons']:
        p=os.path.join(PREP,'cut_'+name+'.png')
        if os.path.exists(p):im=Image.open(p)
        else:
            im=Image.new('RGBA',(400,400 if 'tank' not in name and name!='briefcase' else 220));dd=ImageDraw.Draw(im)
            dd.rounded_rectangle((4,4,im.width-4,im.height-4),30,fill=(200,200,210,255),outline=(0,0,0,255),width=6);dd.text((im.width/2,im.height/2),name,fill=(0,0,0,255),anchor='mm',font=ImageFont.truetype(FONT,26))
        if flip:im=im.transpose(Image.FLIP_LEFT_RIGHT)
        s=size/max(im.size);im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
        sh=im.getchannel('A').point(lambda v:int(v*.55)).filter(ImageFilter.GaussianBlur(max(2,size/30)))
        D['icons'][key]=(im,sh)
        if len(D['icons'])>160:D['icons'].clear();D['icons'][key]=(im,sh)
    return D['icons'][key]

def build_subs():
    groups=[];words=[]
    for i,w in enumerate(WORDS):
        w=w.copy();low=w['w'].lower().strip('.,?!')
        if low in YEARS and words and words[-1]['w'].lower()=='nineteen' and words[-1]['scene']==w['scene']:
            words[-1]['w']=YEARS[low];continue
        if low=='nineteen' and i+1<len(WORDS) and WORDS[i+1]['w'].lower().strip('.,?!') in YEARS:w['w']='nineteen'
        words.append(w)
    for scene in TL['timeline']:
        sid=scene['id'];ws=[w for w in words if w['scene']==sid];n=len(ws);a,b=SC[sid];b=min(b,TOTAL)
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
            for w in g:w['txt']=w['w'].upper().strip('.,')
            groups.append((ss[i],ss[i+1],g))
    return groups

def label(can,s,xy,size=36,col=WHITE,anchor='mm',font=FONT):
    ImageDraw.Draw(can).text(xy,s,font=ImageFont.truetype(font,size),anchor=anchor,fill=col,stroke_width=4,stroke_fill=(5,10,17))
def chip(can,s,y=500,col=YEL,x=70,size=32):
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);d=ImageDraw.Draw(can)
    d.rounded_rectangle((x,y-31-(size-32)//2,x+40+tw,y+31+(size-32)//2),radius=15,fill=(8,16,24),outline=col,width=3);d.text((x+20,y),s,font=f,anchor='lm',fill=col)
def cchip(can,s,cx,y,col=YEL,size=34,t=None,t0=None):
    if t is not None and t<t0:return
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);x=cx-(tw+40)/2
    if t is not None and t-t0<.2:
        k=max(.1,ease((t-t0)/.2,'back'));tmp=Image.new('RGBA',(int(tw+60),int(size*2.6)));chip(tmp,s,tmp.height//2,col,10,size)
        tmp=tmp.resize((max(1,int(tmp.width*k)),max(1,int(tmp.height*k))));can.paste(tmp,(int(cx-tmp.width/2),int(y-tmp.height/2)),tmp);return
    chip(can,s,y,col,int(x),size)
def headline(can,t,sid):
    s=next(s['headline'] for s in SCRIPT['scenes'] if s['id']==sid);size=118
    while ImageFont.truetype(FONT,size).getlength(s)>830:size-=2
    put_text(can,s,size,YEL,495,250,t,SC[sid][0],stroke=10,pop=sid not in ('01','02'))
    label(can,'WARMAP STICK  /  HOW HE LIED',(75,92),24,(180,200,214),'lm')
def subtitle(can,t):
    for s,e,g in D['subs']:
        if s<=t<e:break
    else:return
    hi=max([i for i,w in enumerate(g) if w['s']<=t+.018] or [0]);fs=78
    while ImageFont.truetype(FONT,fs).getlength(' '.join(w['txt'] for w in g))>810:fs-=2
    f=ImageFont.truetype(FONT,fs);sp=f.getlength(' ');widths=[f.getlength(w['txt']) for w in g];tw=sum(widths)+sp*(len(g)-1);x=495-tw/2;d=ImageDraw.Draw(can)
    d.rounded_rectangle((x-25,1434,x+tw+25,1555),radius=20,fill=(6,12,19))
    for i,w in enumerate(g):d.text((x,1493),w['txt'],font=f,anchor='lm',fill=YEL if i==hi else WHITE,stroke_width=7,stroke_fill=(0,0,0));x+=widths[i]+sp
def board(t):
    can=D['board'].copy();d=ImageDraw.Draw(can);y=570+(t*72)%760;d.line((55,y,930,y),fill=(23,55,69),width=3);return can
def sceneid(t):return next((s['id'] for s in TL['timeline'] if s['start']<=t<s['start']+s['dur']),'14')
def moving_icon(can,name,size,xy,t,t0,angle=0,start_full=False,flip=False,shadow=True):
    if t<t0:return
    k=1+.04*math.sin(math.pi*min(1,max(0,(t-t0)/.3))) if start_full else ease((t-t0)/.35,'back');im,sh=icon(name,max(4,round(size*k/4)*4),flip)
    if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True);sh=None
    x0,y0=int(xy[0]-im.width/2),int(xy[1]-im.height/2)
    if shadow and sh is not None:can.paste((0,0,0),(x0+int(size/24),y0+int(size/14)),sh)
    can.paste(im,(x0,y0),im)
def stamp_word(can,s,xy,size,col,t,at,width=None,hh=130,rot=-8):
    if t<at:return
    width=width or int(ImageFont.truetype(FONT,size).getlength(s)+70)
    k=ease((t-at)/.17,'back');im=Image.new('RGBA',(width,hh));d=ImageDraw.Draw(im)
    d.rounded_rectangle((7,7,width-8,hh-8),10,outline=col,width=9,fill=(8,10,16,170))
    d.text((width/2,hh/2),s,font=ImageFont.truetype(FONT,size),anchor='mm',fill=col)
    im=im.rotate(rot,Image.Resampling.BICUBIC,expand=True);im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.Resampling.BICUBIC)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def tint(can,m,col,a):
    if a<=0.01:return can
    return Image.composite(Image.new('RGB',(W,H),col),can,m.point(lambda v:int(v*min(1,a))))
def city(neon,can,v,name,col=WHITE,t=None,t0=0,dx=0,dy=-46,size=34):
    if t is not None and t<t0:return
    x,y=P(v,PLACES[name]);neon.dot((x,y),col,16);D.setdefault('_labels',[]).append((name.upper(),(x+dx,y+dy),size,col))
def flush_labels(can):
    for s,xy,size,col in D.pop('_labels',[]):label(can,s,xy,size,col)
def path_pt(pts,k):
    """Punto a fracción k de una polilínea."""
    L=[math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1)];tot=sum(L);s=k*tot
    for i,l in enumerate(L):
        if s<=l or i==len(L)-1:
            f=min(1,s/max(l,1e-6));a,b=pts[i],pts[i+1];return (lerp(a[0],b[0],f),lerp(a[1],b[1],f)),math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        s-=l
def tanks_along(can,name,p0,p1,t,t0,t1,n=2,size=120,gap=.16):
    for j in range(n):
        k=ramp(t,t0+j*gap,t1+j*gap,'inout')
        if t<t0+j*gap:continue
        x,y=lerp(p0[0],p1[0],k),lerp(p0[1],p1[1],k);flip=p1[0]<p0[0]
        moving_icon(can,name,size,(x+(j%2)*18,y+j*22),t,t0+j*gap,start_full=True,flip=flip)

def m_rhine(t,sid):
    a,b=SC[sid];can=D['map']['rhine'].copy();neon=Neon();v='rhine'
    neon.line([P(v,p) for p in RHINE],(80,170,255),5)
    k=ramp(t,.15,1.4,'cubic')
    can=tint(can,D['m_rhineland'],RED,.15+.5*k+(.25*math.sin(t*9) if 3.6<t<5.4 else 0))
    for p0,p1 in [((9.4,51.2),(6.7,50.7)),((9.6,50.1),(6.9,49.9)),((9.2,49.0),(7.0,49.3))]:
        arrow(neon,P(v,p0),P(v,p1),ramp(t,-.4,1.0,'cubic'),RED,11,.12)
    can=neon.draw(can)
    label(can,'RHINELAND',P(v,(6.3,50.25)),40,(255,170,160))
    label(can,'GERMANY',P(v,(10.3,51.6)),44,(255,150,140));label(can,'FRANCE',P(v,(2.4,46.6)),52,(160,205,255))
    big=1.0+(.18*ramp(t,wt('02','bigger'),wt('02','bigger')+.3,'back') if sid=='02' else 0)
    for j,(lo,la) in enumerate([(3.0,49.2),(4.4,48.9),(5.6,48.45),(2.6,48.1),(3.9,47.85),(5.2,47.5)]):
        x,y=P(v,(lo,la));moving_icon(can,'french_tank',int(200*big),(x,y),t,-1,start_full=True)
    if sid=='01':
        cchip(can,'MARCH 1936',495,430,WHITE,34,t,.25)
        cchip(can,'ORDERS: RETREAT IF FRANCE FIGHTS',495,1330,RED,32,t,wt('01','orders'))
    else:
        cchip(can,'BIGGER ARMY',300,1330,BLUE,40,t,wt('02','bigger'))
        stamp_word(can,'NO RESPONSE',(700,1180),54,GREY,t,wt('02','move'))
    return can
def m_central(t,sid):
    can=D['map']['central'].copy();neon=Neon();v='central';a1,a2=wtn('02','again',1),wtn('02','again',2)
    if t>=a1:can=tint(can,D['m_austria_c'],RED,.55+.35*math.exp(-(t-a1)*4))
    if t>=a2:can=tint(can,D['m_czech_c'],YEL,.18+.3*abs(math.sin((t-a2)*7)))
    can=neon.draw(can)
    label(can,'GERMANY',P(v,(10,52.3)),44,(255,150,140))
    if t>=a1:cchip(can,'AUSTRIA  1938',*P(v,(14.3,46.6)),RED,34,t,a1)
    if t>=a2:label(can,'?',P(v,(15.4,49.9)),120,YEL)
    return can
def m_czech(t,sid):
    can=D['map']['czech'].copy();neon=Neon();v='czech'
    if sid=='03':
        s=wt('03','slice');can=tint(can,D['m_sudeten'],RED,.6*ramp(t,s,s+.6)+(.2*math.sin(t*8) if t>s+.6 else 0))
        can=neon.draw(can)
        label(can,'CZECHOSLOVAKIA',P(v,(15.6,49.75)),36,(255,235,150))
        if t>=s:label(can,'SUDETENLAND',P(v,(13.2,50.55)),34,(255,160,150))
        cchip(can,'SEPT 1938',495,430,WHITE,34,t,SC['03'][0]+.2)
        moving_icon(can,'dictator_promise',560,(300,1110+5*math.sin(t*3)),t,wt('03','swears'))
        cchip(can,'"MY LAST TERRITORIAL CLAIM"',495,1340,YEL,32,t,wt('03','last'))
    else:
        t0=wt('05','tanks');can=tint(can,D['m_sudeten'],RED,.6);can=tint(can,D['m_czech'],RED,.55*ramp(t,t0,wt('05','Prague')+.3))
        city(neon,can,v,'Prague',YEL)
        can=neon.draw(can);flush_labels(can)
        pr=P(v,PLACES['Prague'])
        for p0 in [(11.6,50.6),(14.9,51.4),(13.6,48.2)]:
            tanks_along(can,'german_tank',P(v,p0),(pr[0]+(P(v,p0)[0]-pr[0])*.4,pr[1]+(P(v,p0)[1]-pr[1])*.4),t,t0-.2,wt('05','Prague')+.2,1,115)
        cchip(can,'MARCH 1939',495,430,WHITE,34,t,wt('05','later'))
        stamp_word(can,'PROMISE BROKEN',(495,1290),56,RED,t,wt('05','Prague'))
    return can
def tower(can,t):
    d=ImageDraw.Draw(can);bx,top,base=700,430,1340;col=(70,58,44);hi=(120,100,74)
    for k in range(0,10):
        y0=lerp(top,base,k/10);y1=lerp(top,base,(k+1)/10);w0=lerp(16,150,k/10);w1=lerp(16,150,(k+1)/10)
        d.line((bx-w0,y0,bx-w1,y1),fill=hi,width=8);d.line((bx+w0,y0,bx+w1,y1),fill=hi,width=8)
        d.line((bx-w0,y0,bx+w1,y1),fill=col,width=5);d.line((bx+w0,y0,bx-w1,y1),fill=col,width=5);d.line((bx-w1,y1,bx+w1,y1),fill=col,width=5)
    d.rectangle((bx-260,1190,bx-60,1340),fill=(40,44,52),outline=(0,0,0),width=6)
    for i in range(3):d.rectangle((bx-240+i*62,1225,bx-200+i*62,1270),fill=(255,214,120) if (i+int(t*2))%4 else (90,80,60))
    on=(t*1.6)%1<.5;r=16
    if on:
        g=Image.new('RGB',(W,H));ImageDraw.Draw(g).ellipse((bx-60,top-60,bx+60,top+60),fill=(160,20,15));can=ImageChops.add(can,g.filter(ImageFilter.GaussianBlur(25)));d=ImageDraw.Draw(can)
    d.ellipse((bx-r,top-r-6,bx+r,top+r-6),fill=(255,60,40) if on else (90,20,20),outline=(0,0,0),width=4)
    return can
def c_gleiwitz(t,sid):
    a,b=SC[sid];can=tower(D['night'].copy(),t)
    cchip(can,'GLEIWITZ, GERMANY  ·  31 AUG 1939',495,430,WHITE,30,t,a+.15)
    x=lerp(-160,330,ramp(t,a,wt('06','fake'),'cubic'));moving_icon(can,'disguised_men',540,(x,1150+8*abs(math.sin(t*6))),t,a,start_full=True)
    f=wt('06','fake');stamp_word(can,'FAKE',(300,790),80,RED,t,f)
    at=wt('06','radio')
    if t>=at:
        neon=Neon()
        for j in range(3):
            ph=((t-at)*1.3+j/3)%1;r=60+ph*330;k=1-ph
            neon.line([(700+r*math.cos(math.radians(an)),430+r*math.sin(math.radians(an))) for an in range(-150,-29,6)],tuple(int(c*k) for c in YEL),6)
        can=neon.draw(can)
        cchip(can,'"POLISH ATTACK!"',700,640,YEL,40,t,at)
    return can
def m_poland(t,sid):
    can=D['map']['poland'].copy();neon=Neon();v='poland';t0=wt('07','invades')-.3;wa=P(v,PLACES['Warsaw'])
    for p0,p1 in [((14.2,52.6),(20.2,52.3)),((21.2,54.7),(21.0,52.7)),((19.2,49.0),(20.6,51.4)),((15.8,51.0),(19.6,51.8))]:
        arrow(neon,P(v,p0),P(v,p1),ramp(t,t0,t0+1.3,'cubic'),RED,12,.1)
    city(neon,can,v,'Warsaw',WHITE)
    can=neon.draw(can);flush_labels(can)
    label(can,'POLAND',P(v,(19.4,50.6)),48,WHITE);label(can,'GERMANY',P(v,(11.0,51.0)),40,(255,150,140))
    cchip(can,'1 SEPT 1939',495,430,WHITE,34,t,wt('07','morning'))
    stamp_word(can,'"SELF-DEFENCE"',(495,1290),58,RED,t,wt('07','self-defence'))
    return can
def c_why(t,sid):
    a,b=SC[sid];can=board(t);moving_icon(can,'dictator_smug',700,(495,1000+5*math.sin(t*3)),t,a,start_full=True)
    for w,xy,s in (('why',(830,640),190),('believe',(170,760),150)):
        if t>=wt('08',w):put_text(can,'?',s,YEL,xy[0],xy[1]+8*math.sin(t*4),t,wt('08',w))
    return can
def graves(can,t,t0):
    d=ImageDraw.Draw(can)
    for i in range(24):
        row=i//8;col=i%8;at=t0+i*.035
        if t<at:continue
        k=ease((t-at)/.25,'back');x=110+col*110+(row%2)*55;y=1060+row*95;h=70*k;w=12*k
        d.rectangle((x-w/2,y-h,x+w/2,y),fill=(205,210,215),outline=(0,0,0),width=3);d.rectangle((x-h*.33,y-h*.72,x+h*.33,y-h*.72+w),fill=(205,210,215),outline=(0,0,0),width=3)
    d.rectangle((0,1350,W,1420),fill=(20,40,30))
def c_nomore(t,sid):
    a,b=SC[sid];can=board(t);graves(can,t,wt('09','World'))
    cchip(can,'WW1: MILLIONS DEAD',495,430,WHITE,36,t,wt('09','One'))
    moving_icon(can,'chamberlain',470,(250,740),t,wt('09','Britain'))
    cchip(can,'NEVER AGAIN',250,1000,BLUE,36,t,wt('09','feared'))
    moving_icon(can,'dictator_smug',500,(780,760),t,wt('09','used'))
    return can
def m_lowc(t,sid):
    can=D['map']['lowc'].copy();neon=Neon();v='lowc';d=ImageDraw.Draw(can)
    for i in range(46):
        ang=i*2.39996;rr=math.sqrt(i/46);lo=5.55+math.cos(ang)*rr*.85;la=50.0+math.sin(ang)*rr*.42;x,y=P(v,(lo,la));s=13
        d.polygon([(x,y-s*1.6),(x-s,y+s*.6),(x+s,y+s*.6)],fill=(40,150,80),outline=(10,40,20))
    ru=wt('10','rush')-.2
    for p0,p1 in [((2.6,50.25),(4.4,50.85)),((2.2,50.75),(3.8,51.15)),((3.6,49.9),(4.9,50.55))]:arrow(neon,P(v,p0),P(v,p1),ramp(t,ru,ru+1.0,'cubic'),BLUE,11,.12)
    bt=wt('10','But');bh=wt('10','behind')
    arrow(neon,P(v,(7.0,50.25)),P(v,PLACES['Sedan']),ramp(t,bt,bt+1.6,'cubic'),RED,13,-.1)
    arrow(neon,P(v,PLACES['Sedan']),P(v,(1.75,50.15)),ramp(t,bh-.15,bh+.75,'cubic'),RED,13,.18)
    can=neon.draw(can)
    label(can,'BELGIUM',P(v,(4.4,51.25)),40,(255,235,150));label(can,'FRANCE',P(v,(2.4,49.1)),44,(160,205,255));label(can,'GERMANY',P(v,(7.6,51.1)),40,(255,150,140))
    if t>=wt('10','Ardennes'):cchip(can,'ARDENNES FOREST',*P(v,(6.2,49.35)),(90,230,130),30,t,wt('10','Ardennes'))
    tanks_along(can,'german_tank',P(v,(7.0,50.25)),P(v,PLACES['Sedan']),t,bt+.1,bt+1.7,2,110)
    cchip(can,'MAY 1940',495,430,WHITE,34,t,wt('10','forty'))
    if t>=wt('10','them'):stamp_word(can,'TRAPPED',(700,1290),60,RED,t,wt('10','them'))
    return can
def m_france(t,sid):
    a,b=SC[sid];can=D['map']['france'].copy();neon=Neon();v='france'
    can=tint(can,D['m_france_f'],(120,30,30),.7*ramp(t,a,wt('11','falls')+.2))
    city(neon,can,v,'Paris',YEL);can=neon.draw(can);flush_labels(can)
    stamp_word(can,'FRANCE FALLS',(495,1150),66,RED,t,wt('11','falls'))
    cchip(can,'JUNE 1940',495,430,WHITE,34,t,wt('11','weeks'))
    return can
def c_pact(t,sid):
    a,b=SC[sid];th=wt('12','Then')
    if t<th:
        can=board(t);meet=wt('12','deal')
        k=ramp(t,a,meet,'cubic');shake=4*math.sin(t*30) if t>meet else 0
        moving_icon(can,'dictator_handshake',620,(lerp(150,330,k),1000+shake),t,a,start_full=True)
        moving_icon(can,'stalin',620,(lerp(940,690,k),1000-shake),t,wt('12','with')-.1)
        cchip(can,'AUG 1939: PEACE DEAL',495,430,WHITE,34,t,wt('12','signed'))
        cchip(can,'HIDDEN PLAN',250,1330,RED,34,t,meet+.35)
        return can
    can=D['map']['east'].copy();neon=Neon();v='east';t0=wt('12','forty-one')-.2
    for p0,c in [((21.5,55.0),'Leningrad'),((23.5,53.0),'Moscow'),((23.6,50.6),'Kyiv')]:
        arrow(neon,P(v,p0),P(v,PLACES[c]),ramp(t,t0,t0+2.2,'cubic'),RED,14,.08);city(neon,can,v,c,WHITE)
    can=neon.draw(can);flush_labels(can);label(can,'SOVIET UNION',P(v,(35,52.5)),44,(255,210,130))
    for p0,c in [((21.5,55.0),'Leningrad'),((23.5,53.0),'Moscow'),((23.6,50.6),'Kyiv')]:
        a0=P(v,p0);a1=P(v,PLACES[c]);tanks_along(can,'german_tank',a0,(lerp(a0[0],a1[0],.75),lerp(a0[1],a1[1],.75)),t,t0+.2,t0+2.4,1,110)
    cchip(can,'JUNE 1941',495,430,WHITE,34,t,t0+.2)
    cchip(can,'~3 MILLION GERMAN SOLDIERS',495,1330,RED,32,t,wt('12','three'))
    return can
def m_cost(t,sid):
    a,b=SC[sid];can=D['map']['europe'].copy();neon=Neon();v='europe'
    mi=wt('13','millions');can=tint(can,D['m_occupied'],(150,20,20),.25+.45*ramp(t,mi,mi+.8))
    pts=[('1936',(7.0,50.0)),('1938',(14.4,50.1)),('1939',(21.0,52.2)),('1940',(2.35,48.86)),('1941',(37.6,55.75))]
    for j,(yr,ll) in enumerate(pts):
        at=a+.15+j*.32
        if t>=at:x,y=P(v,ll);neon.dot((x,y),YEL,18);D.setdefault('_labels',[]).append((yr,(x-(45 if yr=='1941' else 0),y-44),36,YEL))
    can=neon.draw(can);flush_labels(can)
    cchip(can,'EVERY LIE = MORE TIME',495,430,YEL,34,t,wt('13','time'))
    cchip(can,'TENS OF MILLIONS DEAD',495,1330,RED,38,t,mi)
    return can
def c_payback(t,sid):
    a,b=SC[sid];can=board(t);fo=wt('14','fooled')
    if t<fo:moving_icon(can,'dictator_smug',680,(495,1000+5*math.sin(t*3)),t,a,start_full=True)
    else:moving_icon(can,'dictator_shock',680,(400,1020+5*math.sin(t*3)),t,fo,start_full=True)
    moving_icon(can,'briefcase',380,(790,700+6*math.sin(t*2.5)),t,wt('14','dead'))
    cchip(can,'1943: OPERATION MINCEMEAT',495,430,WHITE,34,t,wt('14','letters'))
    cchip(can,'NEXT: THE DEAD MAN\'S BRIEFCASE',495,1340,YEL,30,t,wt('14','Follow'))
    return can

def scene_frame(t,sid):
    if sid=='01':return m_rhine(t,sid)
    if sid=='02':return m_rhine(t,sid) if t<wt('02','So') else m_central(t,sid)
    if sid in ('03','05'):return m_czech(t,sid)
    if sid=='04':
        a,b=SC[sid];can=board(t);moving_icon(can,'chamberlain',720,(470,980+6*math.sin(t*3)),t,a,start_full=True)
        cchip(can,'MUNICH, SEPT 1938',495,430,WHITE,34,t,a+.15)
        if t>=wt('04','Peace'):put_text(can,'"PEACE FOR OUR TIME"',62,WHITE,495,1335,t,wt('04','Peace'),stroke=8)
        moving_icon(can,'dictator_promise',540,(860,1060),t,wt('04','time'))
        return can
    return {'06':c_gleiwitz,'07':m_poland,'08':c_why,'09':c_nomore,'10':m_lowc,'11':m_france,'12':c_pact,'13':m_cost,'14':c_payback}[sid](t,sid)

SHAKES=[(wt('01','run'),14,.28),(wt('05','Prague'),10,.24),(wt('06','fake'),10,.24),(wt('07','self-defence'),11,.25),(wt('10','behind'),12,.26),(wt('11','falls'),12,.26),(wt('12','invade'),12,.26),(wt('14','fooled'),12,.26)]
def post(can,t):
    dx=dy=0
    for at,amp,dur in SHAKES:
        dt=t-at
        if 0<=dt<dur:aa=amp*math.exp(-dt*13);dx+=aa*math.sin(dt*101+1);dy+=aa*math.cos(dt*83)
    if abs(dx)+abs(dy)>.3:
        big=can.resize((W+100,H+150),Image.Resampling.BILINEAR);x=round(50+dx);y=round(75+dy);can=big.crop((x,y,x+W,y+H))
    return can
def frame(t,preview=False):
    init();sid=sceneid(t);can=scene_frame(t,sid);can=post(can,t)
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
    out=dest/'S07_HitlerFooled.mp4';up=dest/'S07_upload.mp4'
    run([FF,'-y','-hide_banner','-i',str(video),'-i',str(mix),'-map','0:v','-map','1:a','-af',filt,'-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(nf/FPS),'-movflags','+faststart',str(out)])
    # Two-pass bounded upload: < 10,000,000 bytes with AAC 128k at full portrait resolution.
    bitrate=820;passlog=str(tmp/'upload_pass')
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

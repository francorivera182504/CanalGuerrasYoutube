"""S04 Saint-Nazaire. S03 frame-by-frame PIL renderer, portrait safe layout.
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


# Custom scene logic. Utilities above are copied from S03 Alesia.
import mapa

def prep():
    os.makedirs(PREP,exist_ok=True)
    for n in ('commando','sailor','inspectors','charges','general','ship','dock','tirpitz'):
        im=Image.open(os.path.join(CAP,n+'.png')).convert('RGBA');arr=np.asarray(im)
        # Fill the closed ink silhouette; discard disconnected faint generated shadows.
        ink=np.min(arr[:,:,:3],axis=2)<185
        lab,num=ndimage.label(ink);sizes=np.bincount(lab.ravel());sizes[0]=0
        keep=[i for i in range(1,num+1) if sizes[i]>max(100,sizes.max()*.025)]
        fg=ndimage.binary_fill_holes(ndimage.binary_closing(np.isin(lab,keep),iterations=1))
        im.putalpha(Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45)));im=im.crop(im.getbbox())
        # A real white die-cut border, with no remaining square white background.
        a=im.getchannel('A'); padded=Image.new('RGBA',(im.width+32,im.height+32)); padded.paste(im,(16,16))
        border=padded.getchannel('A').filter(ImageFilter.MaxFilter(25))
        out=Image.new('RGBA',padded.size,'white');out.putalpha(border);out.alpha_composite(padded)
        out.save(os.path.join(PREP,'cut_'+n+'.png'))
    mapa.load()
    for name,v in [('channel',mapa.View(-3.6,49.3,12.0)),('europe',mapa.View(2.6,55.6,30)),('france',mapa.View(-1.8,47.5,9.8))]:
        fs=[(mapa.country('United Kingdom'),BLUE,.22),(mapa.country('France'),RED,.16),(mapa.country('Norway'),BLUE,.22)]
        im,n=mapa.render(v,fs)
        for country,col in [('United Kingdom',BLUE),('France',RED),('Norway',BLUE)]:n.edge(mapa.mask(v,mapa.country(country)),col,.55)
        n.draw(im).save(os.path.join(PREP,'map_'+name+'.png'))
    print('PREP COMPLETE',flush=True)

def build_subs():
    # Dynamic programming chooses 2-3 word blocks. Every displayed block >= .65 s.
    groups=[]
    for scene in TL['timeline']:
        sid=scene['id']; ws=[w.copy() for w in WORDS if w['scene']==sid]; n=len(ws)
        a,b=SC[sid]
        # Permit early appearance of the first block while preserving word highlight timing.
        starts=[w['s'] for w in ws];starts[0]=a
        @lru_cache(None)
        def solve(i):
            if i==n:return 0,[]
            best=(1e9,[])
            for count in (2,3):
                j=i+count
                if j>n:continue
                tail=solve(j)
                if tail[0]>=1e8:continue
                end=starts[j] if j<n else (TOTAL if sid=='11' else b)
                dur=end-starts[i]
                penalty=max(0,.65-dur)**2*1000 + (dur-1.0)**2 + (.03 if count==2 else 0)
                if penalty+tail[0]<best[0]:best=(penalty+tail[0],[(starts[i],end,ws[i:j])]+tail[1])
            return best
        blocks=solve(0)[1]
        # The few fast phrase boundaries are scheduled at .65s minimum, backward then forward.
        ss=[x[0] for x in blocks]+[TOTAL if sid=='11' else b]
        for i in range(len(blocks)-1,-1,-1):ss[i]=min(ss[i],ss[i+1]-.65)
        ss[0]=max(a,ss[0])
        for i in range(1,len(blocks)):ss[i]=max(ss[i],ss[i-1]+.65)
        for i,(_,_,g) in enumerate(blocks):
            for w in g:w['txt']=w['w'].upper()
            groups.append((ss[i],ss[i+1],g))
    return groups

def init():
    if D:return
    D.update(icons={},texts={},bg={},r3={})
    D['subs']=build_subs()
    for name in ('channel','europe','france'):D['map_'+name]=Image.open(os.path.join(PREP,'map_'+name+'.png')).convert('RGB')
    # Dark whiteboard panels with a moving technical grid, not a static photo.
    bg=Image.new('RGB',(W,H),(10,22,34)); d=ImageDraw.Draw(bg)
    for x in range(0,W,90):d.line((x,0,x,H),fill=(17,33,46),width=2)
    for y in range(0,H,90):d.line((0,y,W,y),fill=(17,33,46),width=2)
    D['board']=bg

def label(can,s,xy,size=36,col=WHITE,anchor='mm'):
    f=ImageFont.truetype(FONT,size); d=ImageDraw.Draw(can)
    d.text(xy,s,font=f,anchor=anchor,fill=col,stroke_width=3,stroke_fill=(5,10,17))

def fitlabel(can,s,xy,width=850,size=68,col=YEL):
    while ImageFont.truetype(FONT,size).getlength(s)>width:size-=2
    label(can,s,xy,size,col)

def chip(can,s,y=500,col=YEL):
    f=ImageFont.truetype(FONT,36); tw=f.getlength(s); d=ImageDraw.Draw(can)
    d.rounded_rectangle((70,y-33,110+tw,y+33),radius=16,fill=(8,16,24),outline=col,width=2)
    d.text((90,y),s,font=f,anchor='lm',fill=col)

def headline(can,t,sid):
    s=next(s['headline'] for s in SCRIPT['scenes'] if s['id']==sid)
    # Large original headline stays at the top; long ones use two lines.
    lines=[s]
    if ImageFont.truetype(FONT,112).getlength(s)>860:
        words=s.split(); choices=[(' '.join(words[:i]),' '.join(words[i:])) for i in range(1,len(words))]
        lines=min(choices,key=lambda z:max(len(z[0]),len(z[1])))
    for i,line in enumerate(lines):
        size=112
        while ImageFont.truetype(FONT,size).getlength(line)>850:size-=2
        put_text(can,line,size,YEL if i==0 else WHITE,495,240+125*i,t,SC[sid][0],stroke=10,pop=False)
    label(can,'WARMAP STICK  /  S04',(75,92),24,(180,200,214),'lm')

def subtitle(can,t):
    for s,e,g in D['subs']:
        if s<=t<e:break
    else:return
    hi=max([i for i,w in enumerate(g) if w['s']<=t+.018] or [0])
    fs=78
    while ImageFont.truetype(FONT,fs).getlength(' '.join(w['txt'] for w in g))>840:fs-=2
    f=ImageFont.truetype(FONT,fs); sp=f.getlength(' '); widths=[f.getlength(w['txt']) for w in g]; tw=sum(widths)+sp*(len(g)-1)
    d=ImageDraw.Draw(can); x=495-tw/2
    # The lower UI exclusion zone starts at y=1640. Subtitle box ends at 1555.
    d.rounded_rectangle((x-25,1434,x+tw+25,1555),radius=20,fill=(6,12,19))
    for i,w in enumerate(g):
        d.text((x,1493),w['txt'],font=f,anchor='lm',fill=YEL if i==hi else WHITE,stroke_width=7,stroke_fill=(0,0,0)); x+=widths[i]+sp

def board(t):
    can=D['board'].copy(); d=ImageDraw.Draw(can)
    # Travelling light streaks and a small sonar scan keep every CHAR frame moving.
    y=570+(t*72)%760;d.line((55,y,930,y),fill=(23,55,69),width=3)
    return can

def sceneid(t):
    return next((s['id'] for s in TL['timeline'] if s['start']<=t<s['start']+s['dur']),'11')

def r3(shot,i,preview=False):
    counts={'hook':113,'ram':115,'blast':64,'night':1};i=min(counts[shot],max(1,i))
    p=os.path.join(R3,shot,f'f_{i:04d}.png')
    if not os.path.exists(p):
        if not preview:raise FileNotFoundError(p)
        files=list(Path(R3,shot).glob('still_*.png'))
        p=str(min(files,key=lambda q:abs(int(q.stem.split('_')[1])-i)))
    return Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)

def reconstruction(t,sid,preview):
    a,b=SC[sid];u=t-a
    if sid=='01':can=r3('hook',int(u*FPS)+1,preview)
    elif sid=='02':
        frac=u/(b-a);i=round(113-(112*ease(frac,'sine')))
        can=r3('hook',i,preview)
        # Same camera trajectory reverses; a rendered night plate crossfades at the end.
        k=ramp(frac,.66,1,'sine')
        night=ImageEnhance.Brightness(ImageEnhance.Color(can).enhance(.60)).enhance(.29)
        night=Image.blend(night,Image.new('RGB',(W,H),(4,12,26)),.14)
        can=Image.blend(can,night,k)
        chip(can,'<< REWIND',500,BLUE)
    elif sid=='06':
        can=r3('ram',int(u*FPS)+1,preview);chip(can,'≈01:34',500)
    else:can=r3('blast',int(u*FPS)+1,preview)
    # Small reconstruction disclosure is drawn after shake, so it cannot be clipped.
    return can

FAL=(-5.068,50.153); NAZ=(-2.203,47.277); NOR=(10.4,63.5)
def point(n,xy,col,t):n.dot(xy,col,20+5*math.sin(t*6))
def mapscene(t,sid):
    a,b=SC[sid];u=t-a; name='channel' if sid=='03' else ('france' if sid=='09' else 'europe')
    v={'channel':mapa.View(-3.6,49.3,12),'europe':mapa.View(2.6,55.6,30),'france':mapa.View(-1.8,47.5,9.8)}[name]
    can=D['map_'+name].copy();n=Neon();naz=v.P(*NAZ);nor=v.P(*NOR)
    if sid=='03':
        start=v.P(*FAL);k=min(1,max(0,(t-a)/(b-a)))
        # Route goes west of Ushant and south of Brittany, entirely over water.
        way=[FAL,(-5.65,48.65),(-5.60,47.75),(-4.7,46.9),(-3.05,46.8),NAZ]
        geo=[v.P(*p) for p in way];route=[]
        for j in range(len(geo)-1):
            p0=geo[max(0,j-1)];p1=geo[j];p2=geo[j+1];p3=geo[min(len(geo)-1,j+2)]
            for step in range(20):
                q=step/20
                route.append(tuple(.5*((2*p1[z])+(-p0[z]+p2[z])*q+(2*p0[z]-5*p1[z]+4*p2[z]-p3[z])*q*q+(-p0[z]+3*p1[z]-3*p2[z]+p3[z])*q*q*q) for z in (0,1)))
        route.append(naz);pts,_=partial(route,k);n.line(pts,YEL,9)
        if len(pts)>1:
            ax,ay=pts[-2];bx,by=pts[-1];ang=math.atan2(by-ay,bx-ax)
            n.line([(bx+math.cos(ang+2.6)*27,by+math.sin(ang+2.6)*27),(bx,by),(bx+math.cos(ang-2.6)*27,by+math.sin(ang-2.6)*27)],YEL,9)
        point(n,naz,RED,t);point(n,start,BLUE,t);can=n.draw(can)
        label(can,'BRITAIN',(390,590),48,(150,210,255));label(can,'FALMOUTH',(start[0]+25,start[1]-65),31)
        label(can,'OCCUPIED FRANCE',(700,1080),32,(255,170,150));label(can,'SAINT-NAZAIRE',(naz[0],1360),38,YEL)
        # Flotilla sails along the quadratic route; three ships trail the lead vessel.
        for j in range(3):
            f=max(0,k-j*.10);pos=f*(len(route)-1);idx=min(len(route)-2,int(pos));mix=pos-idx
            xy=(lerp(route[idx][0],route[idx+1][0],mix),lerp(route[idx][1],route[idx+1][1],mix)-35)
            put_icon(can,'ship',125 if j else 155,xy,t,a+.05+j*.12,bob=False)
    elif sid=='04':
        point(n,naz,YEL,t);point(n,nor,BLUE,t)
        for j in range(18):
            f=(j+(t*.4)%1)/18;g=min(1,f+.025)
            n.line([(lerp(nor[0],naz[0],f),lerp(nor[1],naz[1],f)),(lerp(nor[0],naz[0],g),lerp(nor[1],naz[1],g))],YEL,4)
        can=n.draw(can);put_icon(can,'tirpitz',330,(nor[0]-115,nor[1]+100),t,a-.2)
        label(can,'NORWAY',(nor[0]-100,nor[1]+10),37,(150,210,255));label(can,'TIRPITZ',(nor[0]-100,nor[1]+180),41)
        d=ImageDraw.Draw(can);d.rounded_rectangle((90,800,905,1110),24,fill=(7,18,29),outline=(48,84,106),width=2)
        put_icon(can,'dock',250,(265,950),t,a-.2)
        label(can,'NORMANDIE',(640,890),40,YEL);label(can,'DOCK',(640,955),47,YEL)
        label(can,'SAINT-NAZAIRE, FRANCE',(640,1030),23,(175,210,230))
        # Proportional comparison: 251m ship fits the 350m dry dock.
        d=ImageDraw.Draw(can);d.rounded_rectangle((90,1135,905,1415),24,fill=(7,18,29),outline=(48,84,106),width=2)
        # The dock outline encloses a correctly scaled side silhouette (251/350).
        d.rectangle((215,1155,775,1365),outline=(65,165,255),width=5)
        put_icon(can,'tirpitz',402,(495,1260),t,a-.2,bob=False)
        label(can,'251 m  /  350 m DOCK',(495,1388),29,(175,210,230))
        # Link remains visible above the cards, rather than hidden under them.
        link=Neon();p0=(nor[0]-115,nor[1]+215);p1=(355,900)
        for j in range(10):
            f=(j+(u*.9)%1)/10;g=min(1,f+.05)
            link.line([(lerp(p0[0],p1[0],f),lerp(p0[1],p1[1],f)),(lerp(p0[0],p1[0],g),lerp(p0[1],p1[1],g))],YEL,5)
        can=link.draw(can)
    elif sid=='09':
        point(n,naz,RED,t);can=n.draw(can);put_icon(can,'dock',460,(495,830),t,a-.2)
        fitlabel(can,'OUT OF ACTION',(495,1090),800,76,RED)
        d=ImageDraw.Draw(can);d.line((180,1240,820,1240),fill=(65,85,105),width=8)
        end=lerp(180,820,ramp(t,a+.2,b-.35));d.line((180,1240,end,1240),fill=YEL,width=10)
        for x,year in ((180,'1942'),(820,'1945')):
            d.line((x,1218,x,1262),fill=YEL,width=6);label(can,year,(x,1300),42)
        label(can,'REST OF THE WAR',(495,1170),34)
    else:
        point(n,nor,BLUE,t);can=n.draw(can)
        put_icon(can,'tirpitz',475,(nor[0]-115+14*math.sin(u*2),nor[1]+100+5*math.sin(u*3)),t,a-.2)
        label(can,'NORWEGIAN WATERS',(495,970),43,(150,210,255));label(can,'TIRPITZ',(495,1060),58)
        label(can,'ATLANTIC',(290,1270),44,(125,165,190))
        chip(can,'REPAIR OPTION LOST',530,RED)
        # No barrier is drawn; the ship stays near Norway while water glints move.
        d=ImageDraw.Draw(can)
        for j in range(7):
            x=170+(j*107+t*27)%600;y=1130+j%3*48;d.line((x,y,x+25,y),fill=(48,92,125),width=3)
    return can

def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid=='05':
        chip(can,'≈600 RAIDERS',500)
        k=ramp(t,a,a+.55)
        put_icon(can,'commando',425,(lerp(70,290,k),840),t,a-.2)
        put_icon(can,'sailor',425,(lerp(920,710,k),840),t,a-.2)
        cargo=wt('05','Campbeltown');hidden=wt('05','hidden')
        if t<cargo:
            put_icon(can,'ship',700,(495+20*math.sin(u),1190),t,a-.1)
        else:
            put_icon(can,'ship',710,(495,1150),t,cargo-.2)
            put_icon(can,'charges',290,(495,1130+10*math.sin(t*5)),t,hidden-.1)
            label(can,'HMS CAMPBELTOWN',(495,1350),35,(155,205,240))
            # Dashed x-ray callout, clock hand and timer pulse; educational, no wiring detail.
            if t>=hidden:
                n=Neon();n.line([(650,1160),(805,1070),(805,1000)],YEL,5);can=n.draw(can)
                label(can,'DELAYED FUSES',(495,600),43,YEL)
    elif sid=='07':
        chip(can,'≈10:35',500)
        put_icon(can,'ship',780,(495+7*math.sin(u*2),1190),t,a-.2)
        put_icon(can,'inspectors',680,(lerp(80,490,ramp(t,a,a+.65)),875),t,a-.2)
        label(can,'INSPECTING THE WRECK',(495,1375),34,(155,205,240))
        # Moving inspection beam is restricted to this 2D CHAR scene.
        beam=Image.new('RGBA',(W,H));bd=ImageDraw.Draw(beam);x=580+70*math.sin(u*2)
        bd.polygon([(500,1030),(x-90,1260),(x+130,1260)],fill=(255,225,150,22));can=Image.alpha_composite(can.convert('RGBA'),beam).convert('RGB')
    else:
        put_icon(can,'general',690,(lerp(70,335,ramp(t,a,a+.45)),985),t,a-.2)
        put_icon(can,'dock',300,(745,800+7*math.sin(u*3)),t,a-.15)
        put_icon(can,'ship',335,(745,1175+7*math.sin(u*3+2)),t,a-.1)
        put_text(can,'?',165,YEL,680,1000,t,a+.6,stroke=9)
        fitlabel(can,'SHIPS  +  LIVES',(495,1335),820,54,WHITE)
    return can

SHAKES=[(wt('01','exploded'),27),(wt('01','rammed'),9),(wt('06','rammed'),24),(wt('08','exploded'),30)]
FLASHES=[(wt('01','exploded'),.18,.64),(wt('08','exploded'),.18,.6)]
def post(can,t):
    dx=dy=0
    for at,amp in SHAKES:
        dt=t-at
        if 0<=dt<.55:
            aa=amp*math.exp(-dt*7);dx+=aa*math.sin(dt*101+1);dy+=aa*math.cos(dt*83)
    # Overscan before shift prevents black borders, even at maximum shake.
    if abs(dx)+abs(dy)>.3:
        big=can.resize((W+100,H+150),Image.Resampling.BILINEAR);x=round(50+dx);y=round(75+dy);can=big.crop((x,y,x+W,y+H))
    for at,dur,alpha in FLASHES:
        if 0<=t-at<dur:can=Image.blend(can,Image.new('RGB',(W,H),'white'),alpha*(1-(t-at)/dur))
    return can

def frame(t,preview=False):
    init();sid=sceneid(t);style=next(s['style'] for s in SCRIPT['scenes'] if s['id']==sid)
    if style=='3D':can=reconstruction(t,sid,preview)
    elif style=='MAP':can=mapscene(t,sid)
    else:can=charscene(t,sid)
    can=post(can,t)
    # Fixed text layer remains fully safe during impacts.
    if style=='3D':label(can,'ANIMATED RECONSTRUCTION',(76,1377),25,(220,230,236),'lm')
    headline(can,t,sid);subtitle(can,t)
    return can

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
    for shot,count in [('hook',113),('ram',115),('blast',64),('night',1)]:
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
    out=dest/'S04_Saint_Nazaire.mp4';up=dest/'S04_upload.mp4'
    run([FF,'-y','-hide_banner','-i',str(video),'-i',str(mix),'-map','0:v','-map','1:a','-af',filt,'-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(nf/FPS),'-movflags','+faststart',str(out)])
    # Two-pass bounded upload: < 10,000,000 bytes with AAC 128k at full portrait resolution.
    bitrate=1550;passlog=str(tmp/'upload_pass')
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

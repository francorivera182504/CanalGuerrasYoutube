"""S05 Tanks. S03 frame-by-frame PIL renderer, portrait safe layout.
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


# Scene section assembled into build.py, preserving S04 PIL utilities and encoder.
import mapa
ASSETS=('guard','guard_panic','guard_ok','engineer','painter','water','tarp','blueprint','stamp','factory','tank_icon')
COUNTS={'hook':165,'cross':122,'stall':71,'crew':103}
def prep():
    os.makedirs(PREP,exist_ok=True)
    for n in ASSETS:
        im=Image.open(os.path.join(CAP,n+'.png')).convert('RGBA');arr=np.asarray(im)
        ink=np.min(arr[:,:,:3],axis=2)<185
        lab,num=ndimage.label(ink);sizes=np.bincount(lab.ravel());sizes[0]=0
        keep=[i for i in range(1,num+1) if sizes[i]>max(100,sizes.max()*.015)]
        fg=ndimage.binary_fill_holes(ndimage.binary_closing(np.isin(lab,keep),iterations=1))
        # Exterior flood removes background; preserve face whites and holes in legs.
        white=(arr[:,:,:3]>240).all(-1);wl,_=ndimage.label(white)
        border=set(np.unique(np.r_[wl[0],wl[-1],wl[:,0],wl[:,-1]]))-{0}
        bg=np.isin(wl,list(border)); fg &= ~bg
        im.putalpha(Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45)));im=im.crop(im.getbbox())
        padded=Image.new('RGBA',(im.width+32,im.height+32));padded.paste(im,(16,16))
        border=padded.getchannel('A').filter(ImageFilter.MaxFilter(25));out=Image.new('RGBA',padded.size,'white');out.putalpha(border);out.alpha_composite(padded)
        out.save(os.path.join(PREP,'cut_'+n+'.png'))
    # Separate the generated brush/hand so the painting action can follow each letter.
    painter=Image.open(Path(PREP,'cut_painter.png')).convert('RGBA')
    brush=painter.crop((660,110,992,530));brush.save(Path(PREP,'cut_brush_hand.png'))
    body=painter.copy();ImageDraw.Draw(body).rectangle((660,110,992,530),fill=(0,0,0,0));body.save(Path(PREP,'cut_painter_body.png'))
    if not Path(mapa.PREP,'geo.json').exists():mapa.prep()
    mapa.load()
    for name,v,country,col in [('britain',mapa.View(-2.6,54,11),'United Kingdom',BLUE),('somme',mapa.View(2.0,50.05,6.5),'France',BLUE)]:
        im,n=mapa.render(v,[(mapa.country(country),col,.19)])
        n.edge(mapa.mask(v,mapa.country(country)),col,.65);n.draw(im).save(os.path.join(PREP,'map_'+name+'.png'))
    init();json.dump([{'start':s,'end':e,'text':' '.join(w['txt'] for w in g)} for s,e,g in D['subs']],open(Path(PREP,'subtitle_blocks.json'),'w'),indent=2)
    print('PREP COMPLETE',flush=True)

def build_subs():
    groups=[]
    for scene in TL['timeline']:
        sid=scene['id'];ws=[w.copy() for w in WORDS if w['scene']==sid];n=len(ws);a,b=SC[sid];b=min(b,TOTAL)
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
                end=starts[j] if j<n else b;dur=end-starts[i]
                penalty=max(0,.65-dur)**2*1000+(dur-1)**2+(.03 if count==2 else 0)
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
    for n in ('britain','somme'):D['map_'+n]=Image.open(os.path.join(PREP,'map_'+n+'.png')).convert('RGB')
    bg=Image.new('RGB',(W,H),(10,22,34));d=ImageDraw.Draw(bg)
    for x in range(0,W,90):d.line((x,0,x,H),fill=(17,33,46),width=2)
    for y in range(0,H,90):d.line((0,y,W,y),fill=(17,33,46),width=2)
    D['board']=bg
def label(can,s,xy,size=36,col=WHITE,anchor='mm',font=FONT):
    ImageDraw.Draw(can).text(xy,s,font=ImageFont.truetype(font,size),anchor=anchor,fill=col,stroke_width=3,stroke_fill=(5,10,17))
def fitlabel(can,s,xy,width=850,size=68,col=YEL):
    while ImageFont.truetype(FONT,size).getlength(s)>width:size-=2
    label(can,s,xy,size,col)
def chip(can,s,y=500,col=YEL,x=70,size=32):
    f=ImageFont.truetype(FONT,size);tw=f.getlength(s);d=ImageDraw.Draw(can)
    d.rounded_rectangle((x,y-31,x+40+tw,y+31),radius=15,fill=(8,16,24),outline=col,width=2);d.text((x+20,y),s,font=f,anchor='lm',fill=col)
def headline(can,t,sid):
    s=next(s['headline'] for s in SCRIPT['scenes'] if s['id']==sid);lines=[s]
    if ImageFont.truetype(FONT,112).getlength(s)>850:
        words=s.split();choices=[(' '.join(words[:i]),' '.join(words[i:])) for i in range(1,len(words))];lines=min(choices,key=lambda z:max(len(z[0]),len(z[1])))
    for i,line in enumerate(lines):
        size=112
        while ImageFont.truetype(FONT,size).getlength(line)>830:size-=2
        put_text(can,line,size,YEL if i==0 else WHITE,495,240+125*i,t,SC[sid][0],stroke=10,pop=False)
    label(can,'WARMAP STICK  /  S05',(75,92),24,(180,200,214),'lm')
def subtitle(can,t):
    # Let the final 0.13s return exactly to the opening subtitle for the loop seam.
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
        files=list(Path(R3,shot).glob('still_*.png'))
        if not files:raise FileNotFoundError('No stills for '+shot)
        p=str(min(files,key=lambda q:abs(int(q.stem.split('_')[1])-i)))
    return Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def loop_index(t):
    # Reverse the SAME shot, then last four frames use frame 1 for an exact visual seam.
    a,b=SC['12'];end=math.ceil(TOTAL*FPS)/FPS-4/FPS
    q=min(1,max(0,(t-a)/(end-a)));return max(1,round(165-164*ease(q,'sine')))
def reconstruction(t,sid,preview):
    u=t-SC[sid][0]
    if sid in ('01','02'):can=r3('hook',int(t*FPS)+1,preview)
    elif sid=='04':can=r3('cross',int(u*FPS)+1,preview)
    elif sid=='09':can=r3('stall',int(u*FPS)+1,preview)
    elif sid=='11':can=r3('crew',int(u*FPS)+1,preview)
    else:can=r3('hook',loop_index(t),preview)
    # Only permitted UI overlay on these reconstructions.
    if sid=='02':put_icon(can,'water',110,(850,420),t,SC[sid][0],bob=False)
    return can
def moving_icon(can,name,size,xy,t,t0,angle=0):
    if t<t0:return
    k=ease((t-t0)/.35,'back');im,_=icon(name,max(4,round(size*k/4)*4))
    im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def stamp_word(can,s,xy,size,col,t,at,width):
    if t<at:return
    k=ease((t-at)/.17,'back');hh=100 if s=='TOO OBVIOUS' else 140;im=Image.new('RGBA',(width,hh));d=ImageDraw.Draw(im)
    d.rounded_rectangle((7,7,width-8,hh-8),10,outline=col,width=9)
    d.text((width/2,hh/2),s,font=ImageFont.truetype(FONT,size),anchor='mm',fill=col)
    im=im.rotate(-8,Image.Resampling.BICUBIC,expand=True);im=im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.Resampling.BICUBIC)
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def charscene(t,sid):
    a,b=SC[sid];u=t-a;can=board(t);d=ImageDraw.Draw(can)
    if sid in ('05','06'):
        entry=ease(u/.45);cx=lerp(-350,375,entry) if sid=='05' else 375
        moving_icon(can,'engineer',930,(cx,940+4*math.sin(t*3)),t,a-.1,math.sin(t*2)*.7)
        # Match the blank blue sheet actually held by the generated engineer.
        sheet_y=988 if sid=='05' else lerp(988,935,ramp(t,wt('06','innocent'),wt('06','cover')));show='LANDSHIP'
        fitlabel(can,show,(cx,sheet_y),520,72,(15,38,58))
        at=wt('05','too') if sid=='05' else wt('06','tank')
        guard='guard_panic' if sid=='05' and t>=wt('05','landship') else ('guard_ok' if sid=='06' and t>=at else 'guard')
        gx=lerp(1150,800,ease((u-.15)/.45)) if sid=='05' else 800
        moving_icon(can,guard,510,(gx,1080-10*abs(math.sin(u*4))),t,a+.05,(-2+4*math.sin(u*8)) if guard=='guard_panic' else 0)
        if sid=='05':
            # A real stamp prop drops and withdraws; the ink remains on the paper.
            if at-.32<t<at+.26:
                kk=ease((t-(at-.32))/.32) if t<at else ease((t-at)/.26)
                sy=lerp(500,940,kk) if t<at else lerp(940,650,kk)
                sx=cx+400*(1-kk) if t<at else cx+400*kk
                moving_icon(can,'stamp',180,(sx,sy),t,at-.36)
            stamp_word(can,'TOO OBVIOUS',(cx,1050),46,RED,t,at,500)
        else:
            k=ramp(t,wt('06','innocent'),wt('06','cover'))
            ImageDraw.Draw(can).line((cx-250,sheet_y+25,cx-250+500*k,sheet_y-26),fill=RED,width=13)
            if at-.3<t<at+.28:
                kk=ease((t-at+.3)/.3) if t<at else ease((t-at)/.28)
                sy=lerp(540,950,kk) if t<at else lerp(950,650,kk)
                sx=cx+360*(1-kk) if t<at else cx+360*kk
                moving_icon(can,'stamp',180,(sx,sy),t,at-.34)
            stamp_word(can,'TANK',(cx,1040),86,GREEN,t,at,340)
    elif sid=='07':
        d.line((495,640,495,1260),fill=(46,76,94),width=4)
        moving_icon(can,'water',340,(275,955),t,a+.03,1.2*math.sin(u*2))
        moving_icon(can,'tarp',390,(715,990),t,a+.15,math.sin(u*2))
        label(can,'WATER CONTAINER',(275,1190),27,(155,203,228));label(can,'SECRET WEAPON',(715,1190),27,(155,203,228))
        put_text(can,'✓',88,GREEN,275,700,t,a+.35,font=r'C:\Windows\Fonts\seguisym.ttf')
        k=ramp(t,wt('07','supposed'),wt('07','sound'))
        if k>0:chip(can,'COVER NAME',1320,YEL,x=int(lerp(-430,305,k)),size=37)
    else:
        # Tarp and worker are separate movable stickers. The brush arm swings.
        moving_icon(can,'tarp',800,(505,990),t,a-.1)
        start=wt('08','marked');end=wt('08','Petrograd')+.35;k=ramp(t,start,end)
        word='ПЕТРОГРАД';n=min(len(word),int(k*(len(word)+.5)))
        # Paint plate is on the blank broad side of the tarp.
        if n:label(can,word[:n],(330,920),56,(248,238,191),'lm',font=r'C:\Windows\Fonts\arialbd.ttf')
        # The generated hand and brush follow the newest letter; the worker steps along.
        f=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',56)
        tipx=330+f.getlength(word[:n])-12 if n else 330
        tipy=908+7*math.sin(max(0,t-start)*19)+120*ramp(t,end,end+.28)
        if t<start:tipy=985
        entry=-450*(1-ease(u/.4));px=max(190,tipx-180)+entry;tipx+=entry
        moving_icon(can,'painter_body',440,(px,1200),t,a-.5)
        d=ImageDraw.Draw(can);hand=(tipx-50,tipy+95);elbow=(px+58,1128)
        d.line([elbow,hand],fill=WHITE,width=21)
        d.line([elbow,hand],fill=(0,0,0),width=14)
        d.line([elbow,hand],fill=WHITE,width=7)
        im,_=icon('brush_hand',180);can.paste(im,(int(tipx-89),int(tipy-25)),im)
        if t>=wt('08','With'):chip(can,'WITH CARE TO PETROGRAD',1320,YEL,x=140,size=29)
    return can
def tank_grid_icon(can,xy,size,t0,t,grey=False):
    if t<t0:return
    k=ease((t-t0)/.20,'back');im,_=icon('tank_icon',max(4,round(size*k/4)*4))
    if grey:
        g=ImageEnhance.Color(im).enhance(0);g=ImageEnhance.Brightness(g).enhance(.62);g.putalpha(im.getchannel('A'));im=g
    can.paste(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)),im)
def mapscene(t,sid):
    a,b=SC[sid];u=t-a
    if sid=='03':
        z=1+.035*ease(u/(b-a),'sine');base=D['map_britain'];big=base.resize((int(W*z),int(H*z)),Image.Resampling.BILINEAR);can=big.crop((int((big.width-W)/2),int((big.height-H)/2),int((big.width+W)/2),int((big.height+H)/2)))
        chip(can,'LATE 1915',485,BLUE);label(can,'BRITAIN',(410,695),52,(159,215,255))
        n=Neon();arrow(n,(400,790),(615,1000),ramp(u,.25,1.2),YEL,7);can=n.draw(can)
        put_icon(can,'factory',440,(610,1090),t,a+.12)
        gx=lerp(-240,270,ease((u-.12)/.65));moving_icon(can,'guard',505,(gx,1080-10*abs(math.sin(u*5))),t,a+.06)
        chip(can,'SECRET PROJECT',1340,YEL,x=270,size=32)
    else:
        z=1+.04*u/(b-a);base=D['map_somme'];bw,bh=int(W*z),int(H*z);big=base.resize((bw,bh),Image.Resampling.BILINEAR);can=big.crop(((bw-W)//2,(bh-H)//2,(bw-W)//2+W,(bh-H)//2+H));v=mapa.View(2,50.05,6.5);fp=v.P(2.822,50.049);fl=(W/2+(fp[0]-W/2)*z,H/2+(fp[1]-H/2)*z);n=Neon();n.dot(fl,YEL,17+3*math.sin(t*7));arrow(n,(220,815),(fl[0]-30,fl[1]-30),ramp(u,.1,1.25),YEL,5,bend=-.15);can=n.draw(can)
        label(can,'NORTHERN FRANCE',(495,485),31,(160,213,246));chip(can,'15 SEP 1916',580,BLUE,x=315,size=30)
        
        if t<wt('10','Forty-nine'):label(can,'FLERS',(fl[0],fl[1]-58),48,YEL)
        label(can,'THE SOMME',(210,795),32,(145,200,245))
        # All 49 are readable in a 7x7 grid; first 32 move and the other 17 grey out.
        d=ImageDraw.Draw(can);d.rounded_rectangle((80,1025,920,1370),22,fill=(6,17,27),outline=(41,75,98),width=2)
        assign=wt('10','Forty-nine');move=wt('10','Only');reach=wt('10','start')
        progress=ramp(t,move,reach);line_y=1048
        for x in range(110,905,37):d.line((x,line_y,x+19,line_y),fill=YEL,width=4)
        label(can,'START LINE',(490,1018),24,YEL)
        for i in range(49):
            col=i%7;row=i//7;origin=(155+col*112,1085+row*40)
            # Destination keeps every icon separate, immediately above the start line.
            dest=(155+(i%8)*98,840+(i//8)*43)
            xy=(lerp(origin[0],dest[0],progress),lerp(origin[1],dest[1],progress)) if i<32 else origin
            tank_grid_icon(can,xy,82,a+.4+i*.065,t,grey=i>=32 and t>=move)
        if t>=assign:
            label(can,'49 → 32' if t>=move else '49 ASSIGNED',(495,700),74,YEL,font=r'C:\Windows\Fonts\arialbd.ttf')
        if t>=move:label(can,'17 HELD BACK · BREAKDOWNS',(495,1388),25,(159,176,190))
        # Quote at the end, above the grid, safely clear of the narration subtitles.
        if t>=37.55:
            d=ImageDraw.Draw(can);d.rounded_rectangle((85,745,915,824),12,fill=(7,17,25),outline=(90,130,153),width=2)
            label(can,'“A tank is walking up the High Street of Flers…”',(500,768),25,WHITE)
            label(can,'— RFC aircraft report',(500,801),22,(164,198,219))
    return can
SHAKES=[(1.15,25,.24),(wt('05','too'),12,.26),(wt('06','tank'),13,.26),(SC['09'][0]+.55,6,.22),(SC['11'][0]+3.05,8,.20)]
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
    out=dest/'S05_Tanks.mp4';up=dest/'S05_upload.mp4'
    run([FF,'-y','-hide_banner','-i',str(video),'-i',str(mix),'-map','0:v','-map','1:a','-af',filt,'-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(nf/FPS),'-movflags','+faststart',str(out)])
    # Two-pass bounded upload: < 10,000,000 bytes with AAC 128k at full portrait resolution.
    bitrate=1440;passlog=str(tmp/'upload_pass')
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

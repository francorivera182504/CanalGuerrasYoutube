"""S14 Libya: action-first bespoke choreography, Natural Earth atlas, S13 encoding/mastering pipeline."""
import json,math,os,re,subprocess,sys
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance,ImageChops
from scipy import ndimage
HERE=str(Path(__file__).resolve().parent); P=Path(HERE);ROOT=str(P.parents[2]);PREP=str(P/'_prep');CAP=P/'assets'
FF=r'C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
W,H,FPS=1080,1920,30
TL=json.loads((P/'timeline.json').read_text(encoding='utf8')); TOTAL=TL['total'];WORDS=TL['words']
SC={s['id']:(s['start'],s['start']+s['dur']) for s in TL['timeline']}
WHITE=(250,248,239);GOLD=(255,208,104);RED=(236,94,72)
def run(cmd):return subprocess.run(cmd,check=True,capture_output=True,text=True,encoding='utf8')
def loud_measure(path):
 r=run([FF,'-hide_banner','-i',str(path),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
 return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}',r.stderr)[-1])
def ramp(t,a,b):return min(1,max(0,(t-a)/max(.001,b-a)))
def ease(x):return x*x*(3-2*x)
def wt(s,w):return next(x['s'] for x in WORDS if x['scene']==s and x['w'].lower().strip('.,?!:')==w.lower())
@lru_cache(120)
def font(size):return ImageFont.truetype(r'C:\Windows\Fonts\seguibl.ttf',int(size))
@lru_cache(300)
def textlay(text,size,col):
 f=font(size)
 while f.getlength(text)>890:size-=2;f=font(size)
 bb=f.getbbox(text);im=Image.new('RGBA',(int(f.getlength(text))+24,size+36))
 ImageDraw.Draw(im).text((12,8),text,font=f,fill=col,stroke_width=4,stroke_fill=(10,20,29))
 return im
def txt(c,s,y,size=70,col=WHITE,x=540):
 im=textlay(s,size,col);c.alpha_composite(im,(int(x-im.width/2),int(y)))
@lru_cache(24)
def asset(name):return Image.open(P/'_prep'/f'{name}.png').convert('RGBA')
def sticker(c,name,x,y,h,angle=0):
 im=asset(name);z=h/im.height;im=im.resize((int(im.width*z),max(1,int(h))),Image.Resampling.BILINEAR)
 if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 c.alpha_composite(im,(int(x-im.width/2),int(y-im.height)))
def bg(name,t=0,z=1):
 im=asset(name);scale=max(W/im.width,H/im.height)*z
 im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.BILINEAR)
 x=int((im.width-W)/2+math.sin(t*.5)*min(12,(im.width-W)/2)); y=int((im.height-H)/2)
 return im.crop((x,y,x+W,y+H))
def prep():
 Path(PREP).mkdir(exist_ok=True)
 for n in ['corvette','cargo','usv','sailor','operator','official']:
  im=Image.open(CAP/f'{n}.png').convert('RGB');a=np.asarray(im);white=(a.min(2)>235);labels,num=ndimage.label(white)
  border=np.unique(np.r_[labels[0],labels[-1],labels[:,0],labels[:,-1]]);border=border[border>0]
  mask=~np.isin(labels,border);mask=ndimage.binary_fill_holes(mask)
  # Preserve a narrow white sticker rim, remove only white connected to the exterior.
  mask=ndimage.binary_dilation(mask,iterations=4);out=im.convert('RGBA');out.putalpha(Image.fromarray(np.uint8(mask)*255))
  out.crop(out.getbbox()).save(P/'_prep'/f'{n}.png')
 for n in ['bg_port','bg_sea']:Image.open(CAP/f'{n}.png').convert('RGBA').save(P/'_prep'/f'{n}.png')
 Image.MAX_IMAGE_PIXELS=None
 big=Image.open(Path(ROOT)/'Recursos/naturalearth/NE1_HR_LC_SR_W_DR/NE1_HR_LC_SR_W_DR.tif');s=big.width/360
 box=(int(165*s),int(25*s),int(240*s),int(95*s))
 m=big.crop(box).convert('RGB').resize((2400,2800),Image.Resampling.LANCZOS)
 m=ImageEnhance.Color(m).enhance(.48);m=ImageEnhance.Brightness(m).enhance(.63);m.save(P/'_prep/map.png')
 print('PREP COMPLETE',flush=True)
def atlas(t,center=(22,33),span=48):
 m=asset('map');lon,lat=center;latspan=span*(H/W)*.78
 box=((lon-span/2+15)/75*m.width,(65-lat-latspan/2)/70*m.height,(lon+span/2+15)/75*m.width,(65-lat+latspan/2)/70*m.height)
 c=m.transform((W,H),Image.Transform.EXTENT,box,Image.Resampling.BILINEAR)
 def xy(lon1,lat1):return ((lon1-lon)/span*W+W/2,(lat-lat1)/latspan*H+H/2)
 for label,lo,la in [('UKRAINE',31,49),('BLACK SEA',34,43),('LIBYA',17,27),('SYRIA',39,36),('AFRICA',18,18)]:
  x,y=xy(lo,la)
  if label!='SYRIA' and 100<x<950 and 170<y<1350:txt(c,label,y,40,(225,222,205),x)
 bx,by=xy(20.05,32.12);d=ImageDraw.Draw(c)
 d.ellipse((bx-12,by-12,bx+12,by+12),fill=RED,outline=WHITE,width=3)
 txt(c,'BENGHAZI',by+15,43,GOLD,bx)
 return c,xy
def route(c,pts,k=1,col=GOLD,dashed=True):
 d=ImageDraw.Draw(c);n=max(2,int(len(pts)*k));pts=pts[:n]
 for i in range(len(pts)-1):
  if not dashed or i%4<2:d.line((pts[i],pts[i+1]),fill=col,width=7)
 if len(pts)>2:
  x,y=pts[-1];a=math.atan2(y-pts[-2][1],x-pts[-2][0]);d.polygon([(x,y),(x-25*math.cos(a-.5),y-25*math.sin(a-.5)),(x-25*math.cos(a+.5),y-25*math.sin(a+.5))],fill=col)
def path(a,b):return [(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u-100*math.sin(math.pi*u)) for u in np.linspace(0,1,60)]
def blast(c,x,y,t,scale=1):
 # One continuous event, with age measured from collision; no looping sprite.
 a=t-.25
 if a<0:return
 s=scale
 # Local light spill is composited onto the already drawn hull AND sea.
 glow=Image.new('RGB',(270,480));gd=ImageDraw.Draw(glow)
 energy=math.exp(-a*8)*.95+math.exp(-a*1.8)*.24
 for radius in range(110,0,-8):
  v=energy*(1-radius/120)**1.6
  gd.ellipse((x/4-radius*s,y/4-radius*s*.8,x/4+radius*s,y/4+radius*s*.8),fill=(int(255*v),int(164*v),int(65*v)))
 # Rippled orange reflection stretches downward from the collision.
 for i in range(20):
  yy=(y+115*s)/4+i*3;ww=(32-i)*s*(.7+.25*math.sin(i*2.3+t*19))
  gd.line((x/4-ww,yy,x/4+ww,yy),fill=(int(110*energy),int(65*energy),int(18*energy)),width=2)
 lit=ImageChops.screen(c.convert('RGB'),glow.filter(ImageFilter.GaussianBlur(5)).resize((W,H),Image.Resampling.BILINEAR))
 c.paste(lit,(0,0))
 fx=Image.new('RGBA',(W,H));d=ImageDraw.Draw(fx)
 # Buoyant smoke lobes expand, drift, and cool as the flame dies.
 for i in range(22):
  birth=i*.055;age=a-birth
  if age<0:continue
  xx=x+s*(math.sin(i*2.4)*42+age*(20+12*math.sin(i)))
  yy=y-s*(75+age*(155+23*math.cos(i)))
  r=s*(24+age*55)*(1+.13*math.sin(t*4+i))
  alpha=int(min(190,age*850)*min(1,max(0,(3.5-age)/.8)))
  shade=int(44+18*math.sin(i*1.8)+age*6)
  d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(shade,shade+3,shade+7,alpha))
 c.alpha_composite(fx.filter(ImageFilter.GaussianBlur(9)))
 # Irregular, overlapping flame cells: rapid expansion then upward roll-off.
 fx=Image.new('RGBA',(W,H));d=ImageDraw.Draw(fx)
 envelope=(1-math.exp(-a*17))*math.exp(-a*.95)
 for i in range(19):
  angle=i*2.399+t*(.8+.07*i)
  radius=s*envelope*(70+25*math.sin(i*3.1+t*15))
  xx=x+math.cos(angle)*radius*.95
  yy=y-s*(a*85+25)-abs(math.sin(angle))*radius*1.25
  r=s*envelope*(55+20*math.sin(t*20+i*1.7))
  for q,col in [(1,(185,47,13,235)),(.78,(255,101+int(25*math.sin(i+t*9)),16,245)),(.48,(255,202,65,250)),(.23,(255,246,183,255))]:
   rr=r*q;d.ellipse((xx-rr,yy-rr*1.1,xx+rr,yy+rr*.9),fill=col)
 c.alpha_composite(fx.filter(ImageFilter.GaussianBlur(3)))
 # Ballistic spray forms a tall column, breaks up, then falls to the sea.
 fx=Image.new('RGBA',(W,H));d=ImageDraw.Draw(fx)
 for i in range(68):
  age=a-(i%7)*.012
  if age<0:continue
  vx=math.sin(i*2.399)*(100+120*(i%5)/4)
  vy=-(240+(i*71)%440)
  xx=x+s*vx*age;yy=y+s*(95+vy*age+310*age*age)
  if yy>y+115*s:continue
  rr=s*max(1.3,6-age*2)*(1+(i%3)*.3)
  d.ellipse((xx-rr,yy-rr*2.6,xx+rr,yy+rr*2.6),fill=(195,226,235,210))
 # Sparks and dark hull fragments share gravity and drag, without respawning.
 for i in range(37):
  vx=math.sin(i*2.399)*(140+(i*43)%280);vy=-(100+(i*67)%380)
  drag=(1-math.exp(-a*.8))/.8
  xx=x+s*vx*drag;yy=y+s*(vy*drag+230*a*a)
  if yy>y+120*s:continue
  col=(255,211,104,255) if i%3 else (32,34,37,255)
  rr=(2 if i%3 else 6)*s
  d.line((xx,yy,xx-vx*.025*s,yy-(vy+460*a)*.025*s),fill=col,width=max(2,int(rr)))
 # Expanding contact rings connect the event to the water surface.
 for i in range(3):
  age=a-i*.14
  if age<0:continue
  r=s*(20+age*210);alpha=int(155*math.exp(-age*1.7))
  d.arc((x-r,y+115*s-r*.14,x+r,y+115*s+r*.14),0,360,fill=(186,224,232,alpha),width=3)
 c.alpha_composite(fx)
def reconstruction(c):txt(c,'ANIMATED RECONSTRUCTION',1280,34,(209,218,223))
def waterline(c,y,t):
 d=ImageDraw.Draw(c)
 for i in range(9):
  x=i*150-90+math.sin(t*1.5+i)*20;d.arc((x,y+i%2*18,x+160,y+40+i%2*18),0,180,fill=(116,160,180),width=5)
def impact(t,mode=0):
 c=bg('bg_port',t,1.04)
 age=max(0,t-.25)
 # All three impact angles keep the vessel above 40% of vertical frame height.
 sx,sy,sh=[(475,1220,840),(545,1200,820),(480,1250,880)][mode]
 roll=-min(7,age*3)+math.sin(age*8)*2*math.exp(-age*1.5)
 sticker(c,'corvette',sx,sy+min(24,age*12),sh,roll)
 x=sx+270;y=sy-110+min(25,age*12)
 waterline(c,sy+15,t)
 if t<.25:
  # Drone travels from the lower left toward the hull from the first frame.
  k=t/.25;dx=380+(x-380)*k;dy=1370+(y+25-1370)*k
  d=ImageDraw.Draw(c)
  for j in range(7):
   length=90+j*15;off=j*4
   d.line((dx-110-length,dy+100+off,dx-55,dy+45+off),fill=(122+j*12,174+j*8,192+j*7),width=3)
  sticker(c,'usv',dx-92,dy+200,205,0)
 blast(c,x,y,t,1.05 if mode==2 else 1)
 if mode==1:
  # Small edge reaction; its silhouette stays below and left of the impact.
  ImageDraw.Draw(c).polygon([(0,1340),(170,1360),(200,H),(0,H)],fill=(60,70,76))
  sticker(c,'sailor',75-15*math.sin((t-.9)*5),1435,335,-12-6*math.sin(t*8))
 # Shake the photographed scene, leaving editorial text readable.
 amp=18*math.exp(-age*4) if t>=.25 else 0
 dx=int(amp*math.sin(age*89));dy=int(amp*.65*math.cos(age*73))
 if dx or dy:
  c=c.resize((W+40,H+40),Image.Resampling.BILINEAR).crop((20+dx,20+dy,W+20+dx,H+20+dy))
 reconstruction(c);return c
def wreck(t):
 c=bg('bg_port',t);sticker(c,'corvette',540,1530,700,158)
 # Water occludes the bottom of the capsized hull, which remains visible.
 d=ImageDraw.Draw(c);d.rectangle((0,1100,W,H),fill=(25,51,69));waterline(c,1090,t)
 reconstruction(c);return c
# Whole phrase captions, fixed white text with an outline, never karaoke or a box.
SUBS=[]
for s in TL['timeline']:
 ws=[w for w in WORDS if w['scene']==s['id']]
 for i in range(0,len(ws),5):
  part=ws[i:i+5];end=ws[i+5]['s'] if i+5<len(ws) else min(TOTAL,s['start']+s['dur'])
  SUBS.append((part[0]['s']-.04,end,' '.join(w['w'] for w in part)))
def frame(t,*_):
 sid=next((s['id'] for s in TL['timeline'] if s['start']<=t<s['start']+s['dur']),'10');u=t-SC[sid][0]
 if t<.9:c=impact(t);txt(c,'RUSSIA HIT IN LIBYA',260,87,GOLD)
 elif t<1.8:c=impact(t,1);txt(c,'RUSSIA HIT IN LIBYA',260,87,GOLD)
 elif t<2.7:c=impact(t,2);txt(c,'WHY HERE?',190,110,GOLD)
 elif t<3.6:
  c=bg('bg_sea',t);ImageDraw.Draw(c).polygon([(0,1240),(650,1220),(720,H),(0,H)],fill=(60,70,76));sticker(c,'operator',410,1270,850);sticker(c,'usv',860-u*10,1180,330);reconstruction(c);txt(c,'WHY HERE?',190,110,GOLD)
 elif t<4.5:c=wreck(t);txt(c,'MERKURY',270,100,GOLD)
 elif t<5.8:
  k=ease(ramp(t,4.5,5.8));c,xy=atlas(t,(20.05,32.12),4+44*k);txt(c,'LIBYA',260,100,GOLD)
 elif sid=='03':
  c,xy=atlas(t);txt(c,'22 NOVEMBER 2026',260,68,GOLD)
  x,y=xy(20.05,32.12);r=30+25*(t%1);ImageDraw.Draw(c).ellipse((x-r,y-r,x+r,y+r),outline=RED,width=5)
 elif sid=='04':
  if u<2.3:
   c=bg('bg_sea',t);txt(c,'KYIV: SEVEN NAVAL DRONES',260,66,GOLD)
   for i in range(7):
    x=200+(i%3)*310+u*35;y=820+(i//3)*170-u*30;sticker(c,'usv',x,y,185)
   reconstruction(c);txt(c,'Launched from a mothership',420,44)
  elif u<4.2:
   c=wreck(t);txt(c,'MERKURY',270,100,GOLD)
  else:
   c=bg('bg_sea',t);sticker(c,'cargo',520+u*9,1200,440);waterline(c,1200,t);txt(c,'ANGARA',270,100,GOLD);txt(c,'KYIV SAYS IT WAS HIT',430,48);reconstruction(c)
 elif sid=='05':
  c,xy=atlas(t,(24,32),39)
  a,b=xy(35.88,34.89),xy(20.05,32.12);route(c,path(a,b),ramp(u,.3,2))
  txt(c,'TARTUS',a[1]-65,42,GOLD,a[0]);txt(c,'KYIV: MILITARY SUPPLY LINKS',250,58,GOLD)
  txt(c,'SCHEMATIC SUPPLY LINKS',1260,35)
  # The animated route stays unobstructed.
 elif sid=='06':
  c,xy=atlas(t,(20,25),42);a,b=xy(20.05,32.12),xy(18,20)
  route(c,path(a,b),ramp(u,.2,2.6));txt(c,'A GATEWAY INTO AFRICA',260,72,GOLD);txt(c,'SCHEMATIC SUPPLY LINKS',1270,35)
 elif sid=='07':
  c,xy=atlas(t,(29,34),34);x,y=xy(35.88,34.89)
  txt(c,'TARTUS',y-75,44,GOLD,x);ImageDraw.Draw(c).ellipse((x-13,y-13,x+13,y+13),fill=GOLD)
  sticker(c,'cargo',450+u*20,1140,140);txt(c,'SYRIA STILL MATTERS',260,74,GOLD);txt(c,'RUSSIAN RESUPPLY CONTINUED',450,44)
 elif sid=='08':
  c=bg('bg_port',t)
  # Officials stand on a solid quay; no depiction of casualties.
  ImageDraw.Draw(c).polygon([(0,1220),(1080,1160),(1080,H),(0,H)],fill=(70,75,77))
  sticker(c,'official',410,1300,690);txt(c,'TWO LIBYAN OFFICERS',260,72,GOLD);txt(c,'DIED LATER, SAYS THE LNA',420,49)
  if u>2.8:
   txt(c,'BENGHAZI',1120,42)
 elif sid=='09':
  c,xy=atlas(t,(18,35),43)
  a,b,cc=xy(12,36),xy(17,34),xy(10,38)
  route(c,path(a,b),ramp(u,0,1),col=(170,186,195))
  if u>1:route(c,path(b,cc),ramp(u,1,2.9),col=RED)
  txt(c,'CONVOY TURNED BACK',260,74,GOLD);txt(c,'ACCORDING TO REUTERS',430,43);txt(c,'SCHEMATIC · NEAR SICILY',1260,34)
 else:
  c,xy=atlas(t,(23,34),48);txt(c,'WEAKEN RUSSIA?',280,88,GOLD);txt(c,'OR SPREAD THE WAR?',440,78)
  x,y=xy(20.05,32.12);r=30+15*math.sin(u*4);ImageDraw.Draw(c).ellipse((x-r,y-r,x+r,y+r),outline=RED,width=5)
 for a,b,s in SUBS:
  if a<=t<b:txt(c,s,1460,65);break
 return c.convert('RGB')
def checks():
 for t in range(6):frame(t).save(P/'_prep'/f'chk_{t:02}.jpg',quality=94)
 times=[6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,39.5]
 sheet=Image.new('RGB',(6*216,3*408),(15,20,26));d=ImageDraw.Draw(sheet)
 for i,t in enumerate(times):
  im=frame(t).resize((216,384));x=i%6*216;y=i//6*408;sheet.paste(im,(x,y+24));d.text((x+8,y+5),f'{t:.1f}s',fill='white')
 sheet.save(P/'_prep/sheet.jpg',quality=93)
 print('CHECKS COMPLETE',flush=True)


def seg(args):
    index, f0, f1, out = args
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-threads', '2', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-threads', '2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).convert('RGB').tobytes())
        if (f - f0) % 60 == 0: print(f'seg{index}: {f - f0}/{f1 - f0}', flush=True)
    p.stdin.close()
    if p.wait(): raise RuntimeError('ffmpeg segment failed')
def run(cmd): return subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf8')
def loud_measure(path):
    r = run([FF, '-hide_banner', '-i', str(path), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'])
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}', r.stderr)[-1])
def render():
    subprocess.run([sys.executable, os.path.join(HERE, 'sound.py')], check=True, cwd=HERE)
    tmp = Path(HERE, '_encode'); tmp.mkdir(exist_ok=True)
    nf = math.ceil(TOTAL * FPS); nw = 4; step = math.ceil(nf / nw)
    jobs = [(i, i * step, min(nf, (i + 1) * step), str(tmp / f's{i:02d}.mp4')) for i in range(nw)]
    workers = []; logs = []
    for i, f0, f1, path in jobs:
        log = open(tmp / f'segment_{i}.log', 'w', encoding='utf8'); logs.append(log)
        workers.append(subprocess.Popen([sys.executable, '-u', __file__, '--segment', str(i), str(f0), str(f1), path], cwd=HERE, stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)))
    codes = [p.wait() for p in workers]
    for log in logs: log.close()
    if any(codes): raise RuntimeError(f'Segment failures: {codes}')
    lst = tmp / 'list.txt'; lst.write_text(''.join("file '" + j[3].replace('\\', '/') + "'\n" for j in jobs), encoding='utf8')
    video = tmp / 'video.mp4'; run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(video)])
    mix = tmp / 'mix.wav'; run([FF, '-y', '-loglevel', 'error', '-i', os.path.join(HERE, 'voz.wav'), '-i', os.path.join(HERE, 'sfx.wav'), '-filter_complex', '[0:a]apad[v];[v][1:a]amix=inputs=2:normalize=0:duration=longest[a]', '-map', '[a]', '-t', str(nf / FPS), '-c:a', 'pcm_s24le', str(mix)])
    dest = Path(ROOT, 'Render', 'Shorts'); dest.mkdir(parents=True, exist_ok=True); out = dest / 'S14_Libya.mp4'; up = dest / 'S14_upload.mp4'
    run([FF, '-y', '-loglevel', 'error', '-i', str(video), '-i', str(mix), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(nf / FPS), str(out)])
    passlog = str(tmp / 'upload_pass'); common = [FF, '-y', '-loglevel', 'error', '-i', str(out), '-c:v', 'libx264', '-preset', 'slow', '-b:v', '1350k', '-pix_fmt', 'yuv420p', '-passlogfile', passlog]
    run(common + ['-pass', '1', '-an', '-f', 'null', 'NUL']); run(common + ['-pass', '2', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-movflags', '+faststart', str(up)])
    json.dump({'approved_total_s': TOTAL, 'frame_count': nf, 'master': {'path': str(out)}, 'upload': {'path': str(up)}}, open(Path(HERE, 'render_report.json'), 'w'), indent=2)
    from master_audio import master
    master()


if __name__ == '__main__':
 if '--prep' in sys.argv:prep()
 elif '--checks' in sys.argv:checks()
 elif '--segment' in sys.argv:seg((int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]))
 else:render()

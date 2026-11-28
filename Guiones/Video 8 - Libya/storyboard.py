"""Story V8 sobre el motor V7: cartografía real, navegación, descarga y acciones."""
import math,os
from PIL import Image,ImageDraw
import engine as E
from engine import View,lerp,ease

BENG=(20.05,32.12);TRIP=(13.19,32.89);TART=(35.89,34.9)
VIEWS={'libya':View(18,28.5,27),'coast':View(19,32,13),'med':View(23,35,49),'syria':View(36,34.8,12),'africa':View(18,17,76),'sahel':View(9,18,42),'crimea':View(34.4,44.5,12),'sudan':View(31.5,16,16),'europe':View(19,39,38),'sicily':View(12.5,36.5,14)}
PLACES={'BENGHAZI':BENG,'TRIPOLI':TRIP,'TARTUS':TART,'HMEIMIM':(35.95,35.4),'TOBRUK':(23.96,32.08),'SIRTE':(16.59,31.21),'JUFRA':(16.1,29.1),'AL-KHADIM':(21.15,32),'MALI':(-4,17),'GUINEA':(-10.8,10.6),'KHARTOUM':(32.56,15.5),'CRIMEA':(34,45),'LIBYA':(18,27),'SYRIA':(38,35),'ITALY':(12.5,42),'UKRAINE':(31,47),'MEDITERRANEAN':(20,36),'SAHARA':(13,23)}
PLANS={};CACHE={}

def plan(sid):
    s=E.G[sid];txt=s['text'].lower();ch=s['chapter'].split('.')[0];i=int(sid)
    p=dict(view='libya',kind='logistics',labels=['LIBYA','BENGHAZI'],asset='angara',note='CONCEPTUAL LOGISTICS')
    if ch=='I':
        p.update(view='coast',kind='harbour',labels=['BENGHAZI'],asset='corvette',note='ANIMATED RECONSTRUCTION')
        if any(w in txt for w in ['angara','cargo','holds','precise cargo']):p.update(asset='angara',kind='harbour')
        if any(w in txt for w in ['seven','mother ship','boats','route','attackers','unmanned']):p.update(kind='usv',view='med',asset='usv',note='SBU ACCOUNT / LOCATION UNCLEAR',labels=['BENGHAZI'])
        if any(w in txt for w in ['officers','families','wounds','human cost']):p.update(kind='official',asset='libyan',note='ACCORDING TO THE LNA')
        if any(w in txt for w in ['network','inland','africa','follow the network','larger']):p.update(kind='logistics',view='africa',labels=['LIBYA','SAHARA'],asset='aircraft',note='CONCEPTUAL LOGISTICS')
        if any(w in txt for w in ['sunk it','capsized','overturned','hull visible']):p.update(kind='wreck',asset='corvette',note='ANIMATED RECONSTRUCTION')
        if 'what was this war' in txt:p.update(kind='map',view='med',labels=['UKRAINE','BENGHAZI'],asset='corvette',note='')
    elif ch=='II':
        p.update(kind='politics',labels=['TRIPOLI','BENGHAZI'],asset='haftar',note='')
        if any(w in txt for w in ['wagner','africa corps','control over','transition']):p.update(kind='politics',asset='putin',note='RUSSIAN MILITARY PRESENCE')
        if any(w in txt for w in ['may twenty','aircraft','imagery','africa command']):p.update(kind='flight',asset='aircraft',note='US AFRICOM / MAY 2020')
        if any(w in txt for w in ['twenty-five','tobruk','nodes','geography']):p.update(kind='nodes',labels=['TOBRUK','AL-KHADIM','SIRTE','JUFRA'],note='NETWORK DESCRIBED / MARCH 2025')
        if any(w in txt for w in ['inland','truck','equipment','coast provides','journey','delivery','escort','syria']):p.update(kind='logistics',view='libya',labels=['BENGHAZI','JUFRA','SAHARA'],asset='aid_truck',note='CONCEPTUAL LOGISTICS')
    elif ch=='III':
        p.update(view='syria',kind='map',labels=['TARTUS','HMEIMIM','SYRIA'],asset='contract',note='')
        if any(w in txt for w in ['ships','convoy','harbour','coastal facilities']):p.update(kind='tartus',asset='angara',note='ANIMATED RECONSTRUCTION')
        if any(w in txt for w in ['aircraft','runway','airspace']):p.update(kind='flight',asset='aircraft',note='CONCEPTUAL LOGISTICS')
        if any(w in txt for w in ['libya','several','alternatives','redirected','flexibility','network','mediterranean','north africa','ports, roads','flag over','unloaded','coastal end','benghazi','inland base','lasting']):p.update(kind='logistics',view='med',labels=['BENGHAZI','TARTUS'],asset='convoy',note='CONCEPTUAL LINKS / NOT A VOYAGE TRACK')
    elif ch=='IV':
        p.update(kind='harbour',view='med',asset='angara',labels=['BENGHAZI'],note='ANIMATED RECONSTRUCTION')
        if any(w in txt for w in ['oil','energy','revenue','shadow fleet','sanctions','restrictions','maritime trade','port access']):p.update(kind='compare',asset='oil',note='ENERGY TRADE / MILITARY TRANSPORT')
        if any(w in txt for w in ['africa','baltic','guinea','mali','different route']):p.update(kind='logistics',view='africa',labels=['GUINEA','MALI','LIBYA'],asset='angara',note='AP INVESTIGATION / JUNE 2025')
        if 'mali' in txt:p.update(view='sahel',labels=['GUINEA','MALI','SAHARA'])
        if any(w in txt for w in ['convoy','flotilla','sicily','course','caution','destination']):p.update(kind='convoy',view='sicily',labels=['ITALY'],asset='convoy',note='REUTERS / 27 NOV 2026')
    elif ch=='V':
        p.update(kind='usv',view='med',asset='usv',labels=['BENGHAZI'],note='CONCEPTUAL RECONSTRUCTION')
        if any(w in txt for w in ['black sea','crimea','magura','kunikov']):p.update(view='crimea',labels=['CRIMEA'],note='UKRAINIAN MILITARY / FEBRUARY 2024')
        if any(w in txt for w in ['sudan','khartoum','bellingcat','riflemen','locations could','identities']):p.update(kind='map',view='sudan',labels=['KHARTOUM'],asset='operator',note='REPORTED INVOLVEMENT / 2023')
        if any(w in txt for w in ['arctic','gas carrier','april','they said the forces','sinking','claims about']):p.update(kind='gas',asset='gas',note='LIBYAN OFFICIALS / AP, APRIL 2026')
        if any(w in txt for w in ['eastern libya','base in the west','different stages','fit together','uncertainty matters']):p.update(kind='politics',view='libya',asset='libyan',labels=['TRIPOLI','BENGHAZI'],note='LAUNCH ARRANGEMENTS UNCLEAR')
        if any(w in txt for w in ['kyiv','distance also','personnel committed','organisers','coordinated','diplomatic','governments']):p.update(kind='politics',view='med',asset='zelensky',labels=['UKRAINE','BENGHAZI'],note='')
    else:
        p.update(kind='politics',view='europe',asset='zelensky',labels=['ITALY','BENGHAZI'],note='')
        if any(w in txt for w in ['tripoli','libyan','casualties','restraint','united nations','retaliation']):p.update(view='libya',asset='libyan',labels=['TRIPOLI','BENGHAZI'])
        if any(w in txt for w in ['russia','moscow','escorts','surveillance','network','ship movements','delayed convoy','continued deliveries','russian corvette']):p.update(kind='convoy',view='med',asset='convoy',labels=['BENGHAZI','TARTUS'],note='POSSIBLE RESPONSES' if 'would' in txt or 'could' in txt else '')
        if 'corvette overturned' in txt:p.update(kind='wreck',asset='corvette',note='ANIMATED RECONSTRUCTION')
    p['variant']=i%4
    return p

def txt(can,s,xy,size=30,col='WHITE'):
    E.put_text(can,s,size,col,*xy,0,-99,stroke=4,pop=False)

def paste(can,name,size,xy,t,a,flip=False):
    path=os.path.join(E.PREP,'cut_el_'+name+'.png')
    if not os.path.exists(path): raise FileNotFoundError(path)
    if name in ('zelensky','libyan','haftar','putin','operator'):
        # Inclinar el torso y mover el brazo hacia el interlocutor.
        u=t-a;im,_=E.icon('el_'+name,size,flip)
        angle=round(2.8*math.sin(u*2.3)*2)/2
        key=('gesture',name,size,flip,angle)
        if key not in CACHE:
            posed=im.copy()
            if name=='zelensky' and not flip:
                # Animar el brazo existente; no añadir extremidades al recorte.
                box=(0,int(im.height*.31),int(im.width*.45),int(im.height*.49))
                arm=im.crop(box);posed.paste((0,0,0,0),box)
                arm=arm.rotate(angle*3,Image.Resampling.BICUBIC,expand=False,center=(arm.width-2,arm.height*.6))
                posed.alpha_composite(arm,(box[0],box[1]))
            CACHE[key]=posed.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        im=CACHE[key];x,y=xy
        can.paste(im,(int(x-im.width/2),int(y-im.height/2)),im)
    else:E.put_icon(can,'el_'+name,size,xy,t,a-.25,flip=flip,bob=False)

def dashed(d,a,b,k,col=(225,190,90),width=5):
    dx=b[0]-a[0];dy=b[1]-a[1];n=max(1,int(math.hypot(dx,dy)/22))
    for j in range(n):
        u=j/n;v=min((j+.55)/n,k)
        if u>k:break
        d.line((lerp(a[0],b[0],u),lerp(a[1],b[1],u),lerp(a[0],b[0],v),lerp(a[1],b[1],v)),fill=col,width=width)

def map_labels(can,v,p,u):
    d=ImageDraw.Draw(can)
    for j,name in enumerate(p['labels']):
        x,y=v.P(*PLACES[name])
        if 70<x<1850 and 60<y<860:
            r=7+2*math.sin(u*3+j);d.ellipse((x-r,y-r,x+r,y+r),fill=(245,190,75),outline=(20,30,35),width=2)
            # Puertos próximos: escalonar los rótulos para que no se junten.
            lx,ly=x,y+36
            if name=='AL-KHADIM':lx-=40;ly+=27
            if name=='TOBRUK':lx+=40;ly-=12
            if name=='SYRIA' and p['asset']=='contract':lx-=155;ly+=55
            txt(can,name,(lx,ly),34)

def action(can,v,t,sid):
    p=PLANS[sid];a,b=E.SC[sid];u=t-a;dur=b-a
    # Cut a long spoken sentence into two complete visual compositions, never split its audio.
    phase=int(u/7.5);q=(u%7.5)/min(7.5,dur-phase*7.5);q=min(1,max(0,q));k=ease(q,'inout');kind=p['kind'];variant=(p['variant']+phase)%4
    if kind in ['harbour','tartus','wreck','official']:
        bg='tartus' if kind=='tartus' else 'benghazi'
        if bg not in CACHE:CACHE[bg]=Image.open(os.path.join(E.HERE,'assets',bg+'.png')).convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS)
        can.paste(CACHE[bg],(0,0))
        # Water ripples move independently of the fixed background.
        d=ImageDraw.Draw(can)
        for j in range(11):
            x=(j*231+u*32)%2100-90;y=800+(j%3)*47
            d.arc((x,y,x+100,y+12),0,170,fill=(105,158,181),width=2)
        if kind=='official':
            paste(can,'libyan',430,(lerp(-180,420,min(1,u/.8)),485),t,a)
            paste(can,'corvette',760,(1330,740),t,a)
        elif kind=='wreck':
            im,_=E.icon('el_corvette',1050);im=im.rotate(180,resample=Image.Resampling.BICUBIC,expand=True)
            water=can.crop((0,820,1920,1080))
            can.paste(im,(int(900-im.width/2),int(905-im.height/2)),im)
            can.paste(water,(0,820))
        else:
            size=1050 if variant%2==0 else 850
            x=lerp(450,1150,k) if p['asset']=='angara' else lerp(870,1020,k)
            paste(can,p['asset'],size,(x,730),t,a)
            if p['asset']=='angara':
                d=ImageDraw.Draw(can);cx=lerp(x,1450,k);cy=620-220*math.sin(q*math.pi)
                d.line((cx,320,cx,cy-45),fill=(45,40,32),width=5);paste(can,'crate',105,(cx,cy),t,a)
                paste(can,'libyan',260,(1660,580),t,a)
            else:paste(can,'sailor',250,(1470,600),t,a)
        txt(can,'TARTUS' if bg=='tartus' else 'BENGHAZI',(1200,430) if kind=='official' else (330,430),35)
        if p['note']:txt(can,p['note'],(1050,873),24)
        return
    map_labels(can,v,p,u)
    if kind=='politics':
        anchor=(21,28) if p['view']=='libya' else (24,35)
        x,y=v.P(*anchor);x=max(400,min(1500,x));y=max(400,min(720,y))
        paste(can,p['asset'],390,(x-130*(1-min(1,u/.9)),y),t,a)
        # A moving statement and a leader line make the character's relation to the map explicit.
        focus=TRIP if p['asset']=='libyan' else BENG
        point=v.P(*focus);d=ImageDraw.Draw(can)
        progress=(u%6)/2
        dashed(d,(x,y+195),point,min(1,progress),col=(180,155,95),width=4)
        # El marcador recorre la conexión, sin representar una ruta naval.
        travel=(u%6)/6
        px=lerp(x,point[0],travel);py=lerp(y+195,point[1],travel)
        d.ellipse((px-6,py-6,px+6,py+6),fill=(245,197,88))
        if p['asset']=='haftar':
            point=v.P(*PLACES[['BENGHAZI','TOBRUK','JUFRA'][int(u/1.5)%3]])
            r=10+8*(u%1.5)/1.5;d.ellipse((point[0]-r,point[1]-r,point[0]+r,point[1]+r),outline=(215,125,55),width=4)
        else:
            paste(can,'contract',105,(lerp(x+100,min(1730,x+380),k),y-35-65*math.sin(q*math.pi)),t,a+.25)
        if variant%2==0:
            other='libyan' if p['asset']!='libyan' else 'zelensky'
            paste(can,other,290,(x+440,y+50),t,a+.4)
            d=ImageDraw.Draw(can);dashed(d,(x+170,y-20),(x+310,y-20),min(1,u/1.6),col=(190,200,207))
    elif kind=='nodes':
        d=ImageDraw.Draw(can);pts=[v.P(*PLACES[n]) for n in p['labels']]
        for i in range(len(pts)-1):dashed(d,pts[i],pts[i+1],min(1,u/2),width=3)
        paste(can,'aircraft',350,(lerp(400,1460,k),650-100*math.sin(q*math.pi)),t,a)
    elif kind=='compare':
        paste(can,'oil',760,(lerp(260,500,min(1,u/1.2)),540),t,a)
        paste(can,'angara',740,(lerp(1660,1420,min(1,u/1.2)),700),t,a+.25)
        txt(can,'ENERGY',(480,800),31,col='GOLD');txt(can,'DRY CARGO',(1420,800),31,col='BLUE')
    elif kind=='usv':
        # No geographic attack route: separate diagram from the located map marker.
        paste(can,'operator',310,(320,670),t,a)
        target='landing' if p['view']=='crimea' else 'corvette'
        paste(can,target,650 if not phase else 490,(1390,470),t,a)
        num=7 if 'seven' in E.G[sid]['text'].lower() else 1
        for j in range(num):
            x=lerp(580+j*30,1160+j*25,k);y=690+(j%3)*52
            paste(can,'usv',(180 if num==1 else 125)*(1.4 if phase else 1),(x,y),t,a+j*.08)
            d=ImageDraw.Draw(can);d.line((x-90,y+24,x-140,y+25),fill=(172,210,217),width=3)
    elif kind=='flight':
        paste(can,'aircraft',680,(lerp(360,1510,k),570-140*math.sin(q*math.pi)),t,a)
        d=ImageDraw.Draw(can);d.line((950,800,1650,800),fill=(225,225,210),width=9)
    elif kind=='convoy':
        x=lerp(580,1300,k)
        flip='turned around' in E.G[sid]['text'].lower() or 'changed course' in E.G[sid]['text'].lower()
        paste(can,'convoy',1050,(x,610),t,a,flip=flip)
    elif kind=='gas':
        paste(can,'gas',1000 if not phase else 1180,(lerp(720,1150,k),610),t,a)
        txt(can,'ARCTIC METAGAZ / GAS CARRIER',(960,780),30)
    elif kind=='logistics':
        if p['view']=='sahel' or 'AP INVESTIGATION' in p['source_note']:
            sea0,sea1,port,dest=(-18,11),(-15,10),(-13.7,9.5),(-8,13)
        else:
            sea0,sea1,port,dest=(23,33),(20,32.8),BENG,(16.1,29.1)
        if p['view']=='africa' and 'AP INVESTIGATION' not in p['source_note']:dest=(17,20)
        if p['view']=='med':sea0,sea1,port,dest=(34.5,34.5),(23,33),BENG,(18,29.3)
        start=v.P(*port);end=v.P(*dest);s0=v.P(*sea0);s1=v.P(*sea1)
        d=ImageDraw.Draw(can);dashed(d,start,end,min(1,u/1.6),width=4)
        paste(can,'angara',400,(lerp(s0[0],s1[0],k),lerp(s0[1],s1[1],k)),t,a)
        asset='aircraft' if p['asset']=='aircraft' else 'aid_truck'
        paste(can,asset,250,(lerp(start[0],end[0],k),lerp(start[1],end[1],k)),t,a+.2)
        paste(can,'crate',90,end,t,a+.5)
    else:
        if p['asset']=='contract':
            x,y=1420,640;d=ImageDraw.Draw(can)
            for port in [TART,(35.95,35.4)]:dashed(d,(x-150,y),v.P(*port),min(1,u/1.5),col=(200,165,80),width=3)
            paste(can,'contract',420,(x,y),t,a)
            txt(can,'BASE ACCESS',(x,y-235),31)
            d.line((x-130,y+225,x-130+260*k,y+225),fill=(200,165,80),width=7)
        else:paste(can,p['asset'],450,(lerp(550,1100,k),650),t,a)
    if p['note']:txt(can,p['note'],(960,875),23)

for sid in E.ORDER:
    p=plan(sid);PLANS[sid]=p
    p['source_note']=p['note']
    # Sin rótulos editoriales; reconstrucción solamente en escenas del ataque.
    p['note']='ANIMATED RECONSTRUCTION' if p['kind']=='wreck' else ''
    E.STORY[sid]={'view':VIEWS[p['view']],'custom2':[action],'fx':[]}
    if p['kind'] in ['usv','flight','convoy','logistics']:E.STORY[sid]['fx']=[(0,'whoosh',.08)]
    if E.G[sid]['text'].startswith("Start with Libya's"):
        E.STORY[sid].update(view=VIEWS['med'],view2=VIEWS['libya'],move=.1,movedur=2.5)
    if E.G[sid]['text'].startswith('For years, Tartus'):
        E.STORY[sid].update(view=VIEWS['med'],view2=VIEWS['syria'],move=.1,movedur=3)
    if 'it traced equipment unloaded in Guinea' in E.G[sid]['text']:
        E.STORY[sid].update(view=VIEWS['africa'],view2=VIEWS['sahel'],move=.1,movedur=3)

# Acercamientos de seis segundos a los lugares que se nombran en la frase.
base_render_scene=E.render_scene

def moving_scene(sid,t):
    can=base_render_scene(sid,t)
    p=PLANS[sid]
    if p['kind'] in ('harbour','tartus','wreck','official'):return can
    a,b=E.SC[sid];u=t-a;v=E.scene_view(E.STORY[sid],sid,t)
    candidates=[]
    spoken=E.G[sid]['text'].lower()
    for name in p['labels']:
        x,y=v.P(*PLACES[name])
        if 160<x<1760 and 120<y<800:
            candidates.append((name.lower() in spoken,x,y))
    candidates.sort(reverse=True)
    _,cx,cy=candidates[0] if candidates else (False,960,540)
    # Ida y vuelta suave: cambio de encuadre continuo, sin saltos a los seis segundos.
    z=1+.11*(.5-.5*math.cos(u*math.tau/6))
    inv=1/z
    return can.transform(can.size,Image.Transform.AFFINE,(inv,0,cx*(1-inv),0,inv,cy*(1-inv)),Image.Resampling.BILINEAR)

E.render_scene=moving_scene
original_frame=E.frame
def frame(t):
    if t<10.1:
        from hook2d import render
        return render(t)
    return original_frame(t)
E.frame=frame
E.SFX.extend([{'t':0,'type':'boom','vol':.25},{'t':0,'type':'fire','d':5,'vol':.05}])

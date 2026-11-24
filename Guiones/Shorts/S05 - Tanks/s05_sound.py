# S05 sound section appended to S04 synthesis helpers, all sounds created locally.
import math
from pathlib import Path
P=Path(__file__).parent
TL=json.load(open(P/'timeline.json',encoding='utf8'));TOTAL=math.ceil(TL['total']*30)/30
SC={s['id']:(s['start'],s['start']+s['dur']) for s in TL['timeline']}
def wt(sid,word):return next(w['s'] for w in TL['words'] if w['scene']==sid and w['w'].lower()==word.lower())
def crunch(d=.7):
 n=int(d*SR);tt=np.arange(n)/SR
 x=lp(rng.standard_normal(n),.45)*np.exp(-tt*8)
 return x+sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*(6+i*3)) for i,f in enumerate((141,237,379,612,901)))*.23
def engine(d=2):
 n=int(d*SR);tt=np.arange(n)/SR
 x=(np.sin(2*np.pi*38*tt)+.48*np.sin(2*np.pi*76.6*tt)+.27*np.sin(2*np.pi*114.7*tt)+lp(rng.standard_normal(n),.026))
 return x*(.65+.35*np.sin(2*np.pi*6.5*tt)**4)*np.minimum(1,tt*40+.8)*np.minimum(1,(d-tt)*35)
def clank(d=.16):
 n=int(d*SR);tt=np.arange(n)/SR
 return (sum(np.sin(2*np.pi*f*tt) for f in (190,325,590,937))*.3+lp(rng.standard_normal(n),.18))*np.exp(-tt*27)
def wire(d=.5):
 n=int(d*SR);tt=np.arange(n)/SR
 return (np.sin(2*np.pi*(790*tt-350*tt*tt))+.45*np.sin(2*np.pi*(1150*tt-430*tt*tt)))*np.exp(-tt*11)+rng.standard_normal(n)*np.exp(-tt*65)*.35
def brush(d=.22):
 n=int(d*SR);tt=np.arange(n)/SR
 return (lp(rng.standard_normal(n),.35)-lp(rng.standard_normal(n),.03))*np.sin(np.pi*tt/d)**2
def cough(d=.75):
 n=int(d*SR);tt=np.arange(n)/SR
 env=sum(np.exp(-((tt-v)/.055)**2) for v in (.05,.19,.36,.58))
 return (lp(rng.standard_normal(n),.09)+.55*np.sin(2*np.pi*44*tt))*env
EVENTS=[]
def ev(t,kind,vol=.1,d=None):EVENTS.append(dict(t=round(float(t),3),type=kind,vol=vol,**({'d':d} if d else {})))
for sid,shot in [('01','hook'),('04','cross'),('09','stall'),('11','crew'),('12','loop')]:
 a,b=SC[sid];b=min(b,TOTAL);ev(a,'engine',.075 if sid!='11' else .045,b-a)
 if sid!='11':
  for at in np.arange(a,b,.29):
   if sid=='09' and a+.72<at<a+1.36:continue
   ev(at,'clank',.045)
ev(1.15,'crunch',.40);ev(1.15,'boom',.22,.65);ev(1.15,'wire',.22);ev(1.18,'brush',.09,.45)
for at in (1.23,1.31,1.39):ev(at,'clank',.075)
for s in TL['timeline'][2:]:ev(s['start']-.12,'whoosh',.075,.36)
ev(SC['02'][0],'pop',.10)
for at in (5.53,5.70,6.00,6.40):ev(at,'pop',.065)
ev(6.2,'clank',.075)
ev(wt('04','smash'),'crunch',.18);ev(wt('04','smash'),'wire',.12);ev(wt('04','cross'),'creak',.08,.8);ev(11.0,'brush',.095,.8)
ev(SC['05'][0],'whoosh',.10,.6);ev(wt('05','landship'),'pop',.10)
ev(wt('05','too'),'clank',.18);ev(wt('05','too'),'boom',.13,.28)
ev(wt('06','innocent'),'brush',.10,.45);ev(wt('06','tank'),'clank',.17);ev(wt('06','tank'),'pop',.17)
ev(SC['07'][0]+.03,'pop',.11);ev(SC['07'][0]+.15,'pop',.11)
ev(wt('07','supposed'),'whoosh',.09,.48)
for at in np.arange(SC['07'][0]+.23,SC['07'][1],.46):ev(at,'pop',.023,.08)
ev(SC['08'][0],'whoosh',.09,.45)
for at in np.linspace(wt('08','marked'),wt('08','Petrograd')+.35,9):ev(at,'brush',.075,.18)
ev(wt('08','With'),'pop',.075)
ev(SC['09'][0]+.55,'cough',.20,.72);ev(SC['09'][0]+1.36,'engine',.12,.7)
ev(wt('10','Flers'),'pop',.12);ev(wt('10','Forty-nine'),'pop',.14)
for i in range(49):ev(SC['10'][0]+i*.014,'pop',.026,.10)
ev(wt('10','Only'),'whoosh',.12,1.1)
for at in np.arange(wt('10','Only'),wt('10','start'),.22):ev(at,'clank',.025)
ev(wt('10','start'),'clank',.08);ev(36.9,'pop',.06)
ev(SC['11'][0]+2.4,'creak',.10,.65);ev(SC['11'][0]+3.05,'clank',.20)
def main():
 n=int(TOTAL*SR);bed=norm(music(TOTAL,96),.045)[:n]
 gen={'boom':boom,'click':click,'pop':pop,'creak':creak,'whoosh':whoosh,'crunch':crunch,'engine':engine,'clank':clank,'wire':wire,'brush':brush,'cough':cough}
 for e in EVENTS:
  fn=gen[e['type']];x=fn(e['d']) if 'd' in e else fn();x=norm(x,e['vol']);a=int(e['t']*SR);b=min(n,a+len(x))
  if b>a:bed[a:b]+=x[:b-a]
 # Crossfade only the nonverbal bed to its opening engine at the loop seam.
 nn=int(.12*SR);k=np.linspace(0,1,nn);bed[-nn:]=bed[-nn:]*(1-k)+bed[:nn]*k
 peak=np.abs(bed).max()
 if peak>.93:bed*=.93/peak
 with wave.open(str(P/'sfx.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((bed*32767).astype(np.int16).tobytes())
 json.dump({'bpm':96,'music_vol':.045,'events':EVENTS},open(P/'sfx.json','w'),indent=2)
 print('SFX',TOTAL,'s',len(EVENTS),'events',flush=True)
if __name__=='__main__':main()

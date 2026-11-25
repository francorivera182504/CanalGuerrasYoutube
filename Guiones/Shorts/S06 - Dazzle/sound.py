"""Genera la cama de sonido de un Short (efectos + pulso de tensión) sin licencias.
Uso: python short_sfx.py carpeta_del_short   (lee timeline.json y sfx.json, escribe sfx.wav)
sfx.json: {"whoosh_cuts": true, "events": [{"t": 7.5, "type": "click"}, {"t": 23, "type": "boom"},
           {"t": 23, "type": "planes", "d": 4}, {"t": 0, "type": "fire", "d": 5}], "music": true}
"""
import json, sys, wave
import numpy as np
from scipy.signal import lfilter

SR = 48000
rng = np.random.default_rng(7)
lp = lambda x, a: lfilter([a], [1, a - 1], x)

def whoosh(d=0.6):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(8):
        s0, s1 = k * n // 8, (k + 1) * n // 8
        out[s0:s1] = lp(x[s0:s1], 0.01 + 0.24 * k / 8)
    return out * np.sin(np.pi * np.arange(n) / n) ** 2

def boom(d=1.6):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 55 * np.exp(-tt * 1.5) + 30
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3)
    noise = lp(rng.standard_normal(n), 0.05) * np.exp(-tt * 4)
    return body * 1.0 + noise * 2.5

def click(d=0.25):
    n = int(d * SR); tt = np.arange(n) / SR
    a = rng.standard_normal(n) * np.exp(-tt * 120)
    b = np.zeros(n); k = int(0.07 * SR); b[k:] = rng.standard_normal(n - k) * np.exp(-tt[: n - k] * 90) * 0.8
    return lp(a + b, 0.5)

def fire(d):
    n = int(d * SR); base = lp(rng.standard_normal(n), 0.05) * 0.35; cr = np.zeros(n)
    for _ in range(int(d * 14)):
        p = rng.integers(0, max(1, n - 400)); ln = int(rng.integers(40, 300))
        cr[p:p + ln] += rng.standard_normal(ln) * np.exp(-np.arange(ln) / (ln / 4)) * rng.uniform(0.3, 0.9)
    return base + cr * 0.5

def planes(d):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 92 + 4 * np.sin(2 * np.pi * 0.3 * tt); ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sign(np.sin(ph)) * 0.25 + np.sin(2 * ph) * 0.2)
    return lp(x + 0.15 * rng.standard_normal(n), 0.08)

def pop(d=0.12):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 4000 * tt) * tt) * np.exp(-tt * 40)

def mg(d=0.7):
    """Ráfaga de ametralladora: disparos cortos a ~16 por segundo."""
    n = int(d * SR); out = np.zeros(n); shot_n = int(0.05 * SR); st = np.arange(shot_n) / SR
    shot = lp(rng.standard_normal(shot_n), 0.35) * np.exp(-st * 70) + np.sin(2 * np.pi * 120 * st) * np.exp(-st * 50) * 0.6
    t = 0.0
    while t < d - 0.05:
        p = int(t * SR); out[p:p + shot_n] += shot[: n - p] * rng.uniform(0.7, 1.0); t += 1 / 16
    return out

def creak(d=1.2):
    """Chirrido metálico de una válvula al girar."""
    n = int(d * SR); tt = np.arange(n) / SR
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * tt)
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    am = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt))) * np.sin(np.pi * tt / d)
    return lp(saw * am, 0.25)

def music(total, bpm=100):
    """Pulso grave de tensión: bombo suave en cada tiempo + drone en Re menor."""
    n = int(total * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    drone = (np.sin(2 * np.pi * 73.4 * tt) + 0.5 * np.sin(2 * np.pi * 110 * tt) + 0.35 * np.sin(2 * np.pi * 87.3 * tt))
    drone *= 0.55 + 0.45 * np.sin(2 * np.pi * tt / 8) ** 2
    out += lp(drone, 0.03) * 0.5
    beat = 60 / bpm; k = 0
    kick_n = int(0.35 * SR); kt = np.arange(kick_n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-kt * 8) + 40) / SR) * np.exp(-kt * 9)
    while k * beat < total:
        p = int(k * beat * SR); amp = 1.0 if k % 4 == 0 else 0.55
        out[p:p + kick_n] += kick[: n - p] * amp
        k += 1
    fade = np.minimum(1, np.minimum(tt / 1.0, (total - tt) / 1.5))
    return out * fade

def norm(x, v): return x / (np.abs(x).max() + 1e-9) * v

# ---- S06 Dazzle ----
import math
from pathlib import Path
P=Path(__file__).parent
TL=json.load(open(P/'timeline.json',encoding='utf8'));TOTAL=math.ceil(TL['total']*30)/30
SC={s['id']:(s['start'],s['start']+s['dur']) for s in TL['timeline']}
def wt(sid,word):return next(w['s'] for w in TL['words'] if w['scene']==sid and w['w'].lower().strip('.,?!')==word.lower())
def sea(d):
 n=int(d*SR);tt=np.arange(n)/SR
 return lp(rng.standard_normal(n),.02)*(.6+.4*np.sin(2*np.pi*.23*tt)**2)
def ping(d=1.2):
 n=int(d*SR);tt=np.arange(n)/SR
 return np.sin(2*np.pi*1180*tt)*np.exp(-tt*4.5)+.3*np.sin(2*np.pi*2360*tt)*np.exp(-tt*7)
def splash(d=.9):
 n=int(d*SR);tt=np.arange(n)/SR
 return lp(rng.standard_normal(n),.3)*np.exp(-tt*5)*np.minimum(1,tt*60)
def stamp(d=.3):
 n=int(d*SR);tt=np.arange(n)/SR
 return (np.sin(2*np.pi*90*tt)*1.2+lp(rng.standard_normal(n),.2))*np.exp(-tt*22)
def tick(d=.06):
 n=int(d*SR);tt=np.arange(n)/SR
 return np.sin(2*np.pi*2600*tt)*np.exp(-tt*90)
def brush(d=.5):
 n=int(d*SR);tt=np.arange(n)/SR
 return (lp(rng.standard_normal(n),.35)-lp(rng.standard_normal(n),.03))*np.sin(np.pi*tt/d)**2
def engine(d=2):
 n=int(d*SR);tt=np.arange(n)/SR
 x=np.sin(2*np.pi*42*tt)+.5*np.sin(2*np.pi*84*tt)+lp(rng.standard_normal(n),.02)
 return x*(.7+.3*np.sin(2*np.pi*2.2*tt)**2)*np.minimum(1,tt*20+.5)*np.minimum(1,(d-tt)*20)
EVENTS=[]
def ev(t,kind,vol=.1,d=None):EVENTS.append(dict(t=round(float(t),3),type=kind,vol=vol,**({'d':d} if d else {})))
for sid in ('01','02','06','08','09','12'):
 a,b=SC[sid];b=min(b,TOTAL);ev(a,'sea',.07,b-a);ev(a,'engine',.05,b-a)
ev(0,'ping',.09);ev(wt('01','zebra'),'boom',.16,.6);ev(wt('01','zebra')-.25,'whoosh',.10,.4)
for s in TL['timeline'][2:]:ev(s['start']-.12,'whoosh',.075,.36)
ev(wt('03','U-boats'),'ping',.07)
for j in (0,2,3):ev(wt('03','sinking')+j*.35,'splash',.09)
ev(wt('03','replaced'),'stamp',.10)
ev(wt('04',"can't"),'pop',.08);ev(wt('04','artist'),'pop',.10);ev(wt('04','idea'),'tick',.12);ev(wt('04','idea')+.08,'pop',.10)
ev(wt('05','hide'),'pop',.08);ev(wt('05','Confuse'),'brush',.14,.7);ev(wt('05','Confuse'),'boom',.08,.3)
ev(SC['06'][0]+.2,'pop',.08);ev(SC['06'][0]+1.3,'splash',.06,.6);ev(wt('06','not'),'stamp',.09)
for at in np.arange(SC['07'][0]+.2,SC['07'][1],.5):ev(at,'tick',.07)
ev(wt('07','speed'),'pop',.08);ev(wt('07','heading'),'pop',.08)
ev(wt('08','bow'),'pop',.09);ev(wt('08','bow')+.35,'pop',.09);ev(wt('08','turning'),'pop',.10)
ev(SC['09'][0],'whoosh',.12,1.4);ev(wt('09','misses'),'splash',.12);ev(wt('09','misses'),'pop',.08)
for i in range(15):ev(SC['10'][0]+.3+i*.12,'pop',.04,.1)
ev(wt('10','thousands'),'pop',.09);ev(wt('10','America'),'pop',.09)
ev(SC['11'][0]+.1,'pop',.08);ev(wt('11','proof'),'stamp',.14);ev(wt('12','safer'),'pop',.08)
ev(SC['12'][0],'ping',.07)
def main():
 n=int(TOTAL*SR);bed=norm(music(TOTAL,92),.045)[:n]
 gen={'boom':boom,'pop':pop,'whoosh':whoosh,'sea':sea,'ping':ping,'splash':splash,'stamp':stamp,'tick':tick,'brush':brush,'engine':engine}
 for e in EVENTS:
  fn=gen[e['type']];x=fn(e['d']) if 'd' in e else fn();x=norm(x,e['vol']);a=int(e['t']*SR);b=min(n,a+len(x))
  if b>a:bed[a:b]+=x[:b-a]
 nn=int(.12*SR);k=np.linspace(0,1,nn);bed[-nn:]=bed[-nn:]*(1-k)+bed[:nn]*k
 peak=np.abs(bed).max()
 if peak>.93:bed*=.93/peak
 with wave.open(str(P/'sfx.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((bed*32767).astype(np.int16).tobytes())
 json.dump({'bpm':92,'events':EVENTS},open(P/'sfx.json','w'),indent=2)
 print('SFX',TOTAL,'s',len(EVENTS),'events',flush=True)
if __name__=='__main__':main()

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


import math
from pathlib import Path
P=Path(__file__).parent
TL=json.load(open(P/'timeline.json',encoding='utf8'));TOTAL=math.ceil(TL['total']*30)/30
SC={s['id']:(s['start'],s['start']+s['dur']) for s in TL['timeline']}
def wt(sid,word):return next(w['s'] for w in TL['words'] if w['scene']==sid and w['w'].lower()==word.lower())
def water(d=1.0):
 n=int(d*SR);tt=np.arange(n)/SR;x=lp(rng.standard_normal(n),.16)-lp(rng.standard_normal(n),.009)
 return x*(.4+.6*np.sin(np.pi*tt/d)**2)*np.minimum(1,(d-tt)*4)
def crunch(d=.8):
 n=int(d*SR);tt=np.arange(n)/SR
 x=lp(rng.standard_normal(n),.35)*np.exp(-tt*7)
 return x+sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*8) for f in (210,317,480))*.25
def engine(d=2):
 n=int(d*SR);tt=np.arange(n)/SR
 return (np.sin(2*np.pi*48*tt)+.35*np.sin(2*np.pi*97*tt)+lp(rng.standard_normal(n),.04))*(.75+.25*np.sin(2*np.pi*7*tt))
EVENTS=[]
def ev(t,kind,vol=.1,d=None):EVENTS.append(dict(t=round(t,3),type=kind,vol=vol,**({'d':d} if d else {})))
ev(0,'engine',.085,3.7);ev(0,'water',.07,3.7);ev(0,'creak',.12)
ev(wt('01','exploded'),'boom',.61);ev(wt('01','exploded')+.07,'crunch',.22);ev(wt('01','exploded')+.11,'water',.20,2.1);ev(wt('01','exploded')+.1,'fire',.08,2.8)
ev(wt('01','rammed'),'crunch',.15)
for s in TL['timeline'][1:]:ev(max(0,s['start']-.17),'whoosh',.095,.42)
ev(SC['02'][0],'whoosh',.12,2.9)
ev(SC['03'][0]+.1,'pop',.12);ev(SC['03'][0]+.3,'engine',.065,5.2);ev(SC['03'][0]+.3,'water',.04,5.2)
for sid,offset in [('04',.05),('04',.4),('04',.8),('05',0),('05',.15),('05',.3),('07',.05),('09',0),('10',0),('11',0),('11',.15),('11',.35),('11',.6)]:ev(SC[sid][0]+offset,'pop',.11)
ev(wt('05','Campbeltown'),'whoosh',.09,.5);ev(wt('05','hidden'),'pop',.15)
for at in np.arange(wt('05','delayed'),SC['05'][1],.4):ev(float(at),'click',.07)
ev(SC['06'][0],'engine',.15,3.8);ev(SC['06'][0],'water',.105,3.8)
ev(wt('06','rammed'),'crunch',.48);ev(wt('06','rammed'),'boom',.28);ev(wt('06','rammed')+.06,'water',.23,1.05);ev(wt('06','rammed')+.1,'creak',.18)
ev(SC['07'][0],'creak',.06);ev(SC['07'][0],'water',.04,3.7)
for at in np.arange(SC['07'][0],SC['08'][0]+.4,.55):ev(float(at),'click',.055)
ev(wt('08','exploded'),'boom',.65);ev(wt('08','exploded')+.04,'crunch',.24);ev(wt('08','exploded')+.08,'water',.24,1.8)
ev(SC['09'][0]+.2,'whoosh',.085,1.8);ev(SC['09'][1]-.4,'click',.12);ev(SC['10'][0],'engine',.055,2.8);ev(SC['10'][0],'water',.04,2.8)
def main():
 n=int(TOTAL*SR);bed=norm(music(TOTAL,96),.075)[:n]
 gen={'boom':boom,'click':click,'pop':pop,'creak':creak,'whoosh':whoosh,'water':water,'crunch':crunch,'engine':engine,'fire':fire}
 for e in EVENTS:
  fn=gen[e['type']];x=fn(e['d']) if 'd' in e else fn();x=norm(x,e['vol']);a=int(e['t']*SR);b=min(n,a+len(x))
  if b>a:bed[a:b]+=x[:b-a]
 # Gentle peak limiting prevents SFX sums from clipping without crushing the deep boom.
 peak=np.abs(bed).max()
 if peak>.93:bed*=.93/peak
 with wave.open(str(P/'sfx.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((bed*32767).astype(np.int16).tobytes())
 json.dump({'bpm':96,'music_vol':.075,'events':EVENTS},open(P/'sfx.json','w'),indent=2)
 print('SFX',TOTAL,'s',len(EVENTS),'events',flush=True)
if __name__=='__main__':main()

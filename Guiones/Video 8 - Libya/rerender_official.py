import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import engine as E,storyboard as S
cache=max([d for d in P.glob('_v8_*') if (d/'video.mp4').exists()],key=lambda d:(d/'video.mp4').stat().st_mtime)
ids=set()
for sid,p in S.PLANS.items():
    if p['kind']=='official':
        a,b=E.SC[sid];ids.update(range(int(a//25),int((b-1e-6)//25)+1))
def render(i):
    subprocess.run([sys.executable,str(P/'build.py'),'--worker',json.dumps([i,i*750,(i+1)*750,str(cache/f's{i:03}.mp4')])],check=True)
with ThreadPoolExecutor(2) as pool:list(pool.map(render,sorted(ids)))
(P/'_prep/final_cache.txt').write_text(str(cache),encoding='utf-8');print('updated',sorted(ids),cache)

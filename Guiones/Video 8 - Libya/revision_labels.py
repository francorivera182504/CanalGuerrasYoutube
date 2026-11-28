"""Rehacer únicamente los segmentos con topónimos próximos/ocultos."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).resolve().parent
import engine as E,storyboard as S
cache=P/'_v8_25640'
ids=set()
for sid,p in S.PLANS.items():
    if 'AL-KHADIM' in p['labels'] or ('SYRIA' in p['labels'] and p['asset']=='contract'):
        a,b=E.SC[sid];ids.update(range(int(a//25),int((b-1e-6)//25)+1))
def render(i):
    subprocess.run([sys.executable,str(P/'build.py'),'--worker',json.dumps([i,i*750,(i+1)*750,str(cache/f's{i:03}.mp4')])],check=True)
    print('label segment',i,flush=True)
if __name__=='__main__':
    print('affected',sorted(ids),flush=True)
    with ThreadPoolExecutor(4) as pool:list(pool.map(render,sorted(ids)))
    subprocess.run([sys.executable,str(P/'build.py'),'--reuse',str(cache)],check=True)
    subprocess.run([sys.executable,str(P/'finalize.py')],check=True)

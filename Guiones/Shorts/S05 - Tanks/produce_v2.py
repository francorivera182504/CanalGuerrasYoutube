"""Run only after the v2 stills have been visually checked. Hidden background job."""
from pathlib import Path
import subprocess,sys,time
P=Path(__file__).resolve().parent
assert (P/'_revision_v2/stills_approved.txt').exists(), 'Inspect and approve stills first'
for script,args in [('render_all_3d.py',[]),('build.py',[]),('review.py',[]),('qa.py',[]),('revision_qa.py',[])]:
    print(time.strftime('%H:%M:%S'),script,' '.join(args),flush=True)
    subprocess.run([sys.executable,'-u',str(P/script)]+args,cwd=P,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
print('V2 RENDER, ENCODE AND QA COMPLETE',flush=True)

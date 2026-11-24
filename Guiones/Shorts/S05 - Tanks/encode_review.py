"""Finish after the final crew motion pass; never re-render other shots."""
from pathlib import Path
import subprocess,sys,time,json
p=Path(__file__).resolve().parent;deadline=time.monotonic()+900
while 'ALL 3D COMPLETE' not in (p/'render3d/_crew_motion.log').read_text(encoding='utf8',errors='replace'):
 if time.monotonic()>deadline:raise TimeoutError('crew render incomplete')
 if 'Traceback' in (p/'render3d/_crew_motion.err').read_text(encoding='utf8',errors='replace'):raise RuntimeError('crew render failed')
 time.sleep(3)
for script in ('build.py','review.py','qa.py'):
 print(time.strftime('%H:%M:%S'),script,flush=True)
 subprocess.run([sys.executable,'-u',str(p/script)],cwd=p,check=True)
print('FINAL ENCODE, REVIEW AND QA COMPLETE',flush=True)

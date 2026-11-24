"""Wait for full 3D PNG sequences, assemble and review in background."""
from pathlib import Path
import subprocess,time,sys
p=Path(__file__).resolve().parent;deadline=time.monotonic()+7200
while True:
 log=p/'render3d/_batch.log'
 if log.exists() and 'ALL 3D COMPLETE' in log.read_text(encoding='utf8',errors='replace'):break
 if log.exists() and 'Traceback' in log.read_text(encoding='utf8',errors='replace'):raise RuntimeError('3D batch failed')
 if time.monotonic()>deadline:raise TimeoutError('3D batch incomplete')
 time.sleep(5)
# Final hook pass includes the visible broken stumps, then encoding can consume it.
print(time.strftime('%H:%M:%S'),'final hook fracture pass',flush=True)
subprocess.run([sys.executable,'-u',str(p/'render_all_3d.py'),'hook','cross'],cwd=p,check=True)
for script in ('build.py','review.py'):
 print(time.strftime('%H:%M:%S'),script,flush=True)
 subprocess.run([sys.executable,'-u',str(p/script)],cwd=p,check=True)
print('DELIVERABLES AND REVIEW COMPLETE',flush=True)

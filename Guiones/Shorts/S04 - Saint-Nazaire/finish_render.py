"""Background finish: wait for the checked 3D batch, encode, extract review."""
from pathlib import Path
import subprocess,time,sys,json
P=Path(__file__).parent
log=P/'render3d/_camera_fix.log'
deadline=time.monotonic()+1800
while 'ALL 3D COMPLETE' not in log.read_text(encoding='utf8',errors='replace'):
 if time.monotonic()>deadline:raise TimeoutError('3D batch did not finish; inspect render3d logs')
 time.sleep(5)
for script in ('build.py','review.py'):
 print(time.strftime('%H:%M:%S'),script,flush=True)
 subprocess.run([sys.executable,'-u',str(P/script)],cwd=P,check=True)
print('DELIVERABLES AND REVIEW COMPLETE',flush=True)

from pathlib import Path
import subprocess,sys,time
p=Path(__file__).parent
blender=r'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe'
for shot in (tuple(sys.argv[1:]) or ('night','hook','ram','blast')):
 with (p/'render3d'/('_'+shot+'.log')).open('w',encoding='utf8') as log:
  print(time.strftime('%H:%M:%S'),shot,flush=True)
  subprocess.run([blender,'-b','-t','8','-P',str(p/'blender_nazaire.py'),'--','--shot',shot,'--samples','32'],cwd=p,stdout=log,stderr=subprocess.STDOUT,check=True)
 expected={'night':1,'hook':113,'ram':115,'blast':64}[shot]
 files=list((p/'render3d'/shot).glob('f_*.png'))
 if len(files)!=expected:raise RuntimeError(f'{shot}: {len(files)}/{expected} frames')
print('ALL 3D COMPLETE',flush=True)

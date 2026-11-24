"""Hidden background batch, absolute output paths; verifies every PNG."""
from pathlib import Path
import subprocess,sys,time
p=Path(__file__).resolve().parent
blender=r'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe'
counts={'hook':165,'cross':122,'stall':71,'crew':103}
still='--still' in sys.argv
shots=[s for s in sys.argv[1:] if s in counts] or list(counts)
for shot in shots:
 out=(p/'render3d'/shot).resolve();out.mkdir(parents=True,exist_ok=True)
 print(time.strftime('%H:%M:%S'),shot,'stills' if still else 'sequence',flush=True)
 args=[blender,'-b','-t','10','-P',str(p/'blender_tank.py'),'--','--shot',shot,'--samples','32','--out',str(out)]
 if still:args+=['--still','1,36,70','--res','0.5']
 with (p/'render3d'/('_'+shot+('_test' if still else '')+'.log')).open('w',encoding='utf8') as log:
  subprocess.run(args,cwd=p,stdout=log,stderr=subprocess.STDOUT,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 if not still:
  missing=[i for i in range(1,counts[shot]+1) if not (out/f'f_{i:04d}.png').exists()]
  if missing:raise RuntimeError(f'{shot}: missing {len(missing)} frames')
print('ALL STILLS COMPLETE' if still else 'ALL 3D COMPLETE',flush=True)

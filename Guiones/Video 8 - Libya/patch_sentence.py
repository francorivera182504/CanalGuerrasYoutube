"""Sustituye la escena 126 en su hueco medido, sin desplazar el resto del montaje."""
import json,math,subprocess,sys,wave,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).resolve().parent;PREP=P/'_prep';FF=shutil.which('ffmpeg');sid='126'
tl=json.loads((P/'timeline.json').read_text(encoding='utf-8'));s=next(s for s in tl['timeline'] if s['id']==sid)
w=json.loads((P/'audio'/f'{sid}.words.json').read_text(encoding='utf-8'));source_dur=w[-1]['e']+.4
target=s['dur'];factor=target/source_dur
tmp=PREP/'sentence126.wav'
subprocess.run([FF,'-y','-loglevel','error','-i',str(P/'audio'/f'{sid}.mp3'),'-af',f'atrim=duration={source_dur},apad=whole_dur={source_dur},atempo={1/factor},apad,atrim=duration={target}','-ar','48000','-ac','1',str(tmp)],check=True)
before=PREP/'voz_before126.wav'
if not before.exists():shutil.copy2(P/'voz.wav',before)
with wave.open(str(before),'rb') as wf:params=wf.getparams();raw=wf.readframes(wf.getnframes())
with wave.open(str(tmp),'rb') as wf:patch=wf.readframes(wf.getnframes())
assert params.nchannels==1 and params.sampwidth==2 and params.framerate==48000
start=round(s['start']*48000);end=round((s['start']+target)*48000);n=(end-start)*2
patch=(patch+b'\0'*n)[:n]
with wave.open(str(P/'voz.wav'),'wb') as wf:wf.setparams(params);wf.writeframes(raw[:start*2]+patch+raw[end*2:])
tl['words']=[x for x in tl['words'] if x['scene']!=sid]+[dict(w=x['w'],s=round(s['start']+x['s']*factor,4),e=round(s['start']+x['e']*factor,4),scene=sid) for x in w]
tl['words'].sort(key=lambda x:x['s']);(P/'timeline.json').write_text(json.dumps(tl,ensure_ascii=False,indent=1),encoding='utf-8')
(PREP/'sentence126_patch.json').write_text(json.dumps(dict(scene=sid,source_duration=source_dur,target_duration=target,atempo=1/factor,text='The footage points towards Sudan, but the nationality of those men is still unclear.'),indent=2),encoding='utf-8')
# Refresh the raw cache as the inverse of the completed pitch-preserving time adjustment.
raw_tl=json.loads((PREP/'timeline_raw.json').read_text(encoding='utf-8'));global_factor=898.5/raw_tl['total'];rs=next(x for x in raw_tl['timeline'] if x['id']==sid)
raw_tl['words']=[x for x in raw_tl['words'] if x['scene']!=sid]+[dict(w=x['w'],s=round(rs['start']+x['s']*rs['dur']/source_dur,4),e=round(rs['start']+x['e']*rs['dur']/source_dur,4),scene=sid) for x in w];raw_tl['words'].sort(key=lambda x:x['s'])
(PREP/'timeline_raw.json').write_text(json.dumps(raw_tl,ensure_ascii=False,indent=1),encoding='utf-8')
raw_patch=PREP/'sentence126_raw.wav'
subprocess.run([FF,'-y','-loglevel','error','-i',str(tmp),'-af',f'atempo={global_factor},apad,atrim=duration={rs["dur"]}',str(raw_patch)],check=True)
with wave.open(str(PREP/'voz_raw.wav'),'rb') as wf:par=wf.getparams();data=wf.readframes(wf.getnframes())
with wave.open(str(raw_patch),'rb') as wf:part=wf.readframes(wf.getnframes())
ra=round(rs['start']*48000);rb=round((rs['start']+rs['dur'])*48000);ln=(rb-ra)*2;part=(part+b'\0'*ln)[:ln]
with wave.open(str(PREP/'voz_raw.wav'),'wb') as wf:wf.setparams(par);wf.writeframes(data[:ra*2]+part+data[rb*2:])
cache=max([d for d in P.glob('_v8_*') if (d/'video.mp4').exists()],key=lambda d:(d/'video.mp4').stat().st_mtime)
ids=range(int(s['start']//25),int((s['start']+target-1e-5)//25)+1)
def render(i):
    job=[i,i*750,min(27000,(i+1)*750),str(cache/f's{i:03}.mp4')]
    subprocess.run([sys.executable,str(P/'build.py'),'--worker',json.dumps(job)],check=True)
with ThreadPoolExecutor(2) as pool:list(pool.map(render,ids))
print('Reusing final render segments:',cache,flush=True)
subprocess.run([sys.executable,str(P/'build.py'),'--reuse',str(cache)],check=True)
subprocess.run([sys.executable,str(P/'review.py')],check=True)

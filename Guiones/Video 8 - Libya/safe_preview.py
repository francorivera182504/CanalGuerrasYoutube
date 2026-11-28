"""AAC ligero: compresión suave y banda de voz para evitar picos de codificación."""
import json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;PREP=P/'_prep';ROOT=P.parents[1];FF=shutil.which('ffmpeg')
def call(args):
    r=subprocess.run([FF,*map(str,args)],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr[-2500:])
    return r
def measure(path):
    r=call(['-hide_banner','-nostats','-i',path,'-vn','-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','NUL'])
    return json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1]),r.stderr
def protect(upload,master):
    pcm=PREP/'preview_compressed.wav';tmp=PREP/'preview_safe_final.mp4'
    threshold=.18
    for attempt in range(3):
        af=f'highpass=f=45,lowpass=f=6000,acompressor=threshold={threshold}:ratio=5:attack=1:release=80:knee=4:makeup=1'
        call(['-y','-loglevel','error','-i',master,'-vn','-af',af,'-ar','16000','-ac','1',pcm])
        m,_=measure(pcm);gain=-15-float(m['input_i'])
        call(['-y','-loglevel','error','-i',upload,'-i',pcm,'-map','0:v','-map','1:a','-c:v','copy','-af',f'volume={gain}dB','-c:a','aac','-b:a','32k','-ar','16000','-ac','1','-movflags','+faststart','-t','900',tmp])
        m,log=measure(tmp);i=float(m['input_i']);peak=float(m['input_tp']);print('safe preview',attempt,i,peak,flush=True)
        if abs(i+15)<=.25 and peak<=0:
            tmp.replace(upload);(PREP/'upload_loudness.log').write_text(log,encoding='utf-8');return m
        threshold*=.65
    raise RuntimeError('AAC preview did not pass the loudness and peak checks')
if __name__=='__main__':
    upload=ROOT/'Render/Video8_upload.mp4';master=ROOT/'Render/Video8_Libya.mp4';m=protect(upload,master)
    call(['-v','error','-xerror','-err_detect','explode','-i',upload,'-f','null','NUL'])
    f=PREP/'verification.json';v=json.loads(f.read_text(encoding='utf-8'))
    v['upload'].update(bytes=upload.stat().st_size,lufs=float(m['input_i']),true_peak_dbtp=float(m['input_tp']),decode='passed',two_pass=True,audio_peak_protection=True,audio_sample_rate=16000)
    f.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    assert upload.stat().st_size<=10_000_000
    report=P/'Producción (Codex).md';s=report.read_text(encoding='utf-8');s+='\nCopia ligera final: AAC mono a 32 kb/s y 16 kHz, compresión suave de transitorios, vídeo de dos pasadas conservado. Sonoridad '+m['input_i']+' LUFS; pico real '+m['input_tp']+' dBTP; '+str(upload.stat().st_size)+' bytes. Nueva decodificación completa correcta.\n';report.write_text(s,encoding='utf-8')

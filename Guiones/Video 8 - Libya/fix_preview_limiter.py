"""Limita transitorios antes de AAC de bajo bitrate, midiendo la salida codificada."""
import json,math
from finalize import P,PREP,FF,master,upload,run,loud,probe
gain=0.;limit=.4
for attempt in range(4):
    tmp=PREP/'upload_limited.mp4'
    filt=f'aresample=192000,alimiter=limit={limit}:level=false:latency=true,aresample=32000,volume={gain}dB'
    run([FF,'-y','-loglevel','error','-i',upload,'-i',master,'-map','0:v','-map','1:a','-c:v','copy','-af',filt,'-c:a','aac','-ac','1','-b:a','32k','-ar','32000','-movflags','+faststart','-t','900',tmp])
    l=loud(tmp,'upload_limited_loudness.log');i=float(l['input_i']);peak=float(l['input_tp']);print(attempt,i,peak,flush=True)
    if abs(i+14)<=.18 and peak<=-.5:break
    change=-14-i
    gain+=change
    expected=peak+change
    if expected>-.5:limit*=10**(-(expected+1)/20)
else:raise RuntimeError('Preview limiter did not reach requested loudness')
tmp.replace(upload)
run([FF,'-v','error','-xerror','-err_detect','explode','-i',upload,'-f','null','NUL'],'Video8_upload_decode.log')
f=PREP/'verification.json';v=json.loads(f.read_text(encoding='utf-8'))
v['upload'].update(probe=probe(upload),bytes=upload.stat().st_size,lufs=i,true_peak_dbtp=peak,decode='passed',two_pass=True,audio_peak_protection=True)
assert upload.stat().st_size<=10_000_000
f.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
(PREP/'upload_loudness.log').write_text((PREP/'upload_limited_loudness.log').read_text(encoding='utf-8'),encoding='utf-8')
report=P/'Producción (Codex).md';s=report.read_text(encoding='utf-8');s+='\nAjuste final de la copia ligera: el vídeo conserva sus dos pasadas; el audio se recodificó desde el máster con limitador de transitorios y medición tras AAC. Resultado: '+f'{i:.2f} LUFS, {peak:.2f} dBTP, {upload.stat().st_size:,} bytes. Decodificación completa repetida y correcta.\n';report.write_text(s,encoding='utf-8')

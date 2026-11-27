"""Repite solo el upload de 2 pasadas + reporte + master de audio (sin re-renderizar cuadros)."""
import json,math
from pathlib import Path
import build
B=build;tmp=Path(B.HERE,'_encode');dest=Path(B.ROOT,'Render','Shorts');out=dest/'S11_BullAllen.mp4';up=dest/'S11_upload.mp4'
nf=math.ceil(B.TOTAL*B.FPS);passlog=str(tmp/'upload_pass')
common=[B.FF,'-y','-loglevel','error','-i',str(out),'-c:v','libx264','-preset','slow','-b:v','1300k','-pix_fmt','yuv420p','-passlogfile',passlog]
B.run(common+['-pass','1','-an','-f','null','NUL']);B.run(common+['-pass','2','-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart',str(up)])
report={'approved_total_s':B.TOTAL,'encoded_duration_s':nf/B.FPS,'frame_count':nf,'format':'1080x1920 30 fps','master':{'path':str(out)},'upload':{'path':str(up)}}
json.dump(report,open(Path(B.HERE,'render_report.json'),'w'),indent=2)
from master_audio import master
master()

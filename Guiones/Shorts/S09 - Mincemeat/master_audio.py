"""Master an existing image render; retain the checked video bitstreams."""
from pathlib import Path
import json,os,math
import build
P=Path(__file__).parent;FF=build.FF;tmp=P/'_encode';run=build.run
def master():
    video=tmp/'video.mp4';raw=tmp/'mix.wav';mix=tmp/'mix_limited.wav'
    # Look-ahead peak control preserves voice level while taming brief booms.
    run([FF,'-y','-loglevel','error','-i',str(raw),'-af','volume=8dB,alimiter=limit=0.65:level=false:attack=5:release=100:latency=true','-c:a','pcm_s24le',str(mix)])
    m=build.loud_measure(mix);json.dump(m,open(tmp/'loudnorm_pass1_limited.json','w'),indent=2)
    filt=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json"
    dest=Path(build.ROOT,'Render/Shorts');master=dest/'S09_Mincemeat.mp4';upload=dest/'S09_upload.mp4'
    audio=tmp/'final_audio.wav'
    run([FF,'-y','-loglevel','error','-i',str(mix),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(audio)])
    # Master video comes from the CRF18 sequence. Upload video retains its bounded two-pass encoding.
    for old,destination,rate in [(video,master,'192k'),(upload,upload,'128k')]:
        temp=tmp/('master_final.mp4' if rate=='192k' else 'upload_final.mp4')
        run([FF,'-y','-loglevel','error','-i',str(old),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a',rate,'-ar','48000','-t',str(math.ceil(build.TOTAL*build.FPS)/build.FPS),'-movflags','+faststart',str(temp)])
        os.replace(temp,destination)
    report=json.load(open(P/'render_report.json'))
    for key,path in [('master',master),('upload',upload)]:
        report[key].update(bytes=path.stat().st_size,loudness=build.loud_measure(path))
        report[key]['integrated_lufs']=float(report[key]['loudness']['input_i'])
        report[key]['true_peak_dbtp']=float(report[key]['loudness']['input_tp'])
        assert abs(float(report[key]['loudness']['input_i'])+14)<=.5,report[key]
    assert upload.stat().st_size<=10_000_000
    json.dump(report,open(P/'render_report.json','w'),indent=2)
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':master()

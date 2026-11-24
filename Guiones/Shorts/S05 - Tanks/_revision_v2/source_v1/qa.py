"""Checks against approved inputs and final encoded outputs. No input edits."""
from pathlib import Path
import json,hashlib,subprocess,math
import numpy as np
from PIL import Image
import build
p=Path(__file__).resolve().parent
def check():
 result={};hashes=json.loads((p/'approved_inputs_sha256.json').read_text())
 result['approved_inputs_unchanged']=all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in hashes.items())
 assert result['approved_inputs_unchanged']
 groups=build.build_subs();result['subtitle_blocks']=len(groups);result['shortest_subtitle_s']=min(e-s for s,e,g in groups)
 assert all(len(g) in (2,3) and e-s>=.64999 for s,e,g in groups)
 assert [w['w'] for s,e,g in groups for w in g]==[w['w'] for w in build.WORDS]
 result['crushes_sync_s']=build.wt('01','crushes');assert result['crushes_sync_s']==1.15
 result['frames_3d']={shot:len(list((p/'render3d'/shot).glob('f_*.png'))) for shot in build.COUNTS}
 assert result['frames_3d']==build.COUNTS
 first=np.asarray(build.frame(0));last=np.asarray(build.frame((math.ceil(build.TOTAL*30)-1)/30))
 result['loop_raw_first_last_identical']=bool(np.array_equal(first,last));assert result['loop_raw_first_last_identical']
 result['format']='1080x1920, 30 fps, 1456 frames';result['duration_s']=math.ceil(build.TOTAL*30)/30
 report=json.loads((p/'render_report.json').read_text())
 for key in ('master','upload'):
  info=report[key];assert abs(info['integrated_lufs']+14)<=.5
  result[key]={'path':info['path'],'bytes':info['bytes'],'lufs':info['integrated_lufs'],'true_peak_dbtp':info['true_peak_dbtp']}
 assert result['upload']['bytes']<=10_000_000
 # Probe actual streams, not the filename or renderer's intended configuration.
 probe=str(Path(build.FF).with_name('ffprobe.exe'))
 for key in ('master','upload'):
  rr=subprocess.run([probe,'-v','error','-show_streams','-show_format','-of','json',result[key]['path']],check=True,capture_output=True,text=True)
  data=json.loads(rr.stdout);v=next(s for s in data['streams'] if s['codec_type']=='video')
  from fractions import Fraction
  assert (v['width'],v['height'],v['r_frame_rate'],v['nb_frames'])==(1080,1920,'30/1','1456'),v
  assert abs(float(Fraction(v['avg_frame_rate']))-30)<.001,v
  result[key]['nominal_fps']=v['r_frame_rate'];result[key]['average_fps']=float(Fraction(v['avg_frame_rate']))
  result[key]['probe_duration_s']=float(data['format']['duration'])
  result[key]['video_codec']=v['codec_name'];result[key]['pixel_format']=v['pix_fmt']
 decode=(p/'_review/decode_checks.log').read_text(encoding='utf8')
 result['black_detection_events']=[s for s in decode.splitlines() if 'black_start:' in s]
 result['freeze_detection_events']=[s for s in decode.splitlines() if 'freeze_start:' in s]
 assert not result['black_detection_events']
 # Last encoded frame is 1455/30 = 48.5s. Difference reflects H.264 quantization.
 a=np.asarray(Image.open(p/'_review/frame_00.000.jpg')).astype(float)
 b=np.asarray(Image.open(p/'_review/frame_48.500.jpg')).astype(float)
 result['encoded_loop_mean_abs_rgb_difference']=float(np.mean(np.abs(a-b)))
 result['contact_sheets']=[str(f) for f in sorted((p/'_review').glob('sheet_*.jpg'))]
 result['source_timeline_note']='Last scene metadata ends 48.706s; authoritative total and voice end at 48.526s. Kept inputs intact and encoded 48.533333s.'
 (p/'_review/technical_qa.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 print(json.dumps(result,indent=2))
if __name__=='__main__':check()

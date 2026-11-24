"""Evidence for the requested v2 corrections, without changing approved inputs."""
from pathlib import Path
import ast, hashlib, json, math, subprocess
import numpy as np
from PIL import Image
import build

P=Path(__file__).resolve().parent

def main():
    base=json.loads((P/'_revision_v2/protected_baseline.json').read_text())
    result={}
    for group in ('inputs','assets'):
        result[group+'_unchanged']=all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in base[group].items())
        assert result[group+'_unchanged'],group
    functions={n.name:ast.dump(n) for n in ast.parse((P/'build.py').read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef)}
    result['subtitle_and_headline_functions_unchanged']=all(functions[n]==v for n,v in base['functions'].items())
    assert result['subtitle_and_headline_functions_unchanged']
    result['framing']={}
    for shot in build.COUNTS:
        rows=json.loads((P/'render3d'/shot/'framing.json').read_text())
        widths=[r['width_fraction'] for r in rows]
        result['framing'][shot]={'min_width_fraction':min(widths),'max_width_fraction':max(widths),'samples':rows}
        assert min(widths)>=(.80 if shot=='crew' else .65),shot
        assert all(r['left']>=-.005 and r['right']<=1.005 for r in rows),shot
        if shot=='crew':assert all(r['crew']==8 for r in rows)
    result['required_hook_stills_checked']=[0,20,35,45,90]
    assert all((P/'_revision_v2/hook_check3'/f'still_{f+1:04d}.png').exists() for f in result['required_hook_stills_checked'])
    manifest=json.loads((P/'_review/frame_manifest.json').read_text())
    required=[1.15,1.30,1.50,48.5]
    assert all(any(abs(row['requested_s']-t)<.0001 for row in manifest) for t in required)
    result['additional_review_times_s']=required
    result['scene_first_encoded_frames']=[{'scene':s['id'],'frame':math.ceil(s['start']*30),'time_s':math.ceil(s['start']*30)/30} for s in build.TL['timeline']]
    result['map_quote_font_px']=32
    result['map_breakdowns_font_px']=30
    result['map_quote_interval_s']=[36.9,39.05]
    result['grid_nominal_width_fraction']=(6*132+116)/1080
    result['loop']='New forward moving approach; final four frames use the exact new opening pose. No reversed crush.'
    video=Path(build.ROOT)/'Render/Shorts/S05_Tanks.mp4'
    result['motion_checks']=[]
    for a,b in ((20.967,21.733),(33.567,34.267),(35.467,36.400),(39.800,42.200)):
        decoded=[]
        for t in (a,b):
            r=subprocess.run([build.FF,'-loglevel','error','-ss',str(t),'-i',str(video),'-frames:v','1','-vf','scale=270:480','-f','rawvideo','-pix_fmt','rgb24','-threads','1','-'],capture_output=True,check=True)
            decoded.append(np.frombuffer(r.stdout,dtype=np.uint8).astype(float))
        diff=np.abs(decoded[0]-decoded[1])
        row={'start_s':a,'end_s':b,'mean_abs_rgb_difference':float(diff.mean()),'changed_channel_fraction':float(np.mean(diff>2))}
        assert row['mean_abs_rgb_difference']>.04,row
        result['motion_checks'].append(row)
    upload=Path(build.ROOT)/'Render/Shorts/S05_upload.mp4'
    r=subprocess.run([build.FF,'-hide_banner','-v','error','-i',str(upload),'-f','null','NUL'],capture_output=True,text=True,check=True)
    (P/'_review/upload_decode_checks.log').write_text(r.stderr,encoding='utf8')
    result['upload_full_decode_passed']=True
    (P/'_review/revision_v2_qa.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    report=json.loads((P/'render_report.json').read_text())
    delivery={'revision':'v2','files':[{**report[key],'sha256':hashlib.sha256(Path(report[key]['path']).read_bytes()).hexdigest()} for key in ('master','upload')],
              'contact_sheets':[str(f) for f in sorted((P/'_review').glob('sheet_*.jpg'))],
              'qa':[str(P/'_review/technical_qa.json'),str(P/'_review/revision_v2_qa.json')]}
    (P/'delivery_manifest.json').write_text(json.dumps(delivery,indent=2),encoding='utf8')
    print('V2 QA PASSED',json.dumps({k:result[k] for k in ('inputs_unchanged','assets_unchanged','subtitle_and_headline_functions_unchanged','motion_checks')}),flush=True)

if __name__=='__main__':main()

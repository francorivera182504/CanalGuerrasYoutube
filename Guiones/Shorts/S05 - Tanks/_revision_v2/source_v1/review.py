"""Extract required encoded review frames, 4x3 sheets and technical checks."""
from pathlib import Path
import sys,json,subprocess,math,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent
FF=r'C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
FONT=r'C:\Windows\Fonts\arialbd.ttf'
def sheets(files,prefix):
    for i in range(0,len(files),12):
        sheet=Image.new('RGB',(1080,1560),(8,16,23));d=ImageDraw.Draw(sheet)
        for j,(t,path) in enumerate(files[i:i+12]):
            im=Image.open(path).convert('RGB').resize((270,480),Image.Resampling.LANCZOS);x=j%4*270;y=j//4*520
            sheet.paste(im,(x,y+40));d.text((x+12,y+6),f'{t:.3f} s',font=ImageFont.truetype(FONT,24),fill='white')
        sheet.save(P/prefix/f'sheet_{i//12+1:02d}.jpg',quality=93)
def main():
    if '--preview' in sys.argv:
        fs=sorted(P.joinpath('_prep').glob('test_*.jpg'));sheets([(float(f.stem[5:]),f) for f in fs],'_prep');return
    out=P/'_review';out.mkdir(exist_ok=True)
    root=P.parents[2];video=root/'Render/Shorts/S05_Tanks.mp4'
    times=[0,.2,.4,.6,.8,1,1.2,1.4,1.6,2,2.5,3,4,5]+list(range(6,49))
    times=sorted(set(times+[1.15,1.35,5.4667,9.2,13.25,15.35,16.4,18.55,19.35,23.0,24.1,26.5,27.67,28.4,29.1,30.0,34.25,35.8,36.8,38.1,38.9,39.2,40.7,42.25,42.55,48.4,48.5]))
    # Decode once and select exact frame indices. Seeking to 48.5s can miss the
    # final packet because MP4 concat quantizes its PTS a fraction of a ms early.
    indices=sorted(set(min(1455,int(math.ceil(round(t*30,2)))) for t in times))
    select='+'.join(f'eq(n\\,{i})' for i in indices)
    subprocess.run([FF,'-y','-loglevel','error','-i',str(video),'-an','-vf','select='+select+',scale=out_range=full','-fps_mode','vfr','-pix_fmt','yuvj420p','-threads','2','-q:v','2',str(out/'_sample_%04d.jpg')],check=True)
    import shutil
    fs=[];manifest=[]
    for j,index in enumerate(indices):
        sample=out/f'_sample_{j+1:04d}.jpg'
        if not sample.exists():raise RuntimeError(f'Missing decoded frame {index}')
        for t in times:
            if min(1455,int(math.ceil(round(t*30,2))))!=index:continue
            path=out/f'frame_{t:06.3f}.jpg';shutil.copyfile(sample,path);fs.append((t,path));manifest.append({'requested_s':t,'frame_index':index,'frame_s':index/30,'path':str(path)})
        sample.unlink()
    fs.sort();json.dump(manifest,open(out/'frame_manifest.json','w'),indent=2)
    sheets(fs,'_review');json.dump(times,open(out/'times.json','w'),indent=2)
    # One continuous decode finds any corruption, black frames and long accidental freezes.
    r=subprocess.run([FF,'-hide_banner','-i',str(video),'-vf','blackdetect=d=0.03:pix_th=0.10,freezedetect=n=-50dB:d=0.7','-an','-f','null','NUL'],capture_output=True,text=True)
    (out/'decode_checks.log').write_text(r.stderr,encoding='utf8')
    print('Review:',len(times),'frames',math.ceil(len(times)/12),'sheets',flush=True)
if __name__=='__main__':main()

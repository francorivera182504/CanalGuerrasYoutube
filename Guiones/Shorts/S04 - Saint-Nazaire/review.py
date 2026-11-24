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
    root=P.parents[2];video=root/'Render/Shorts/S04_Saint_Nazaire.mp4'
    times=[0,.2,.4,.6,.8,1,1.2,1.6,2,2.5,3,4,5]+list(range(6,43))
    times=sorted(set(times+[.833,.9,6.4,6.85,17.9,22.5,24.5,27.15,27.5,28.5,30.5,32.8,33.133,33.5,35.5,38.5,40.5,42.8]))
    fs=[]
    for t in times:
        path=out/f'frame_{t:06.3f}.jpg'
        subprocess.run([FF,'-y','-loglevel','error','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(path)],check=True)
        fs.append((t,path))
    sheets(fs,'_review');json.dump(times,open(out/'times.json','w'),indent=2)
    # One continuous decode finds any corruption, black frames and long accidental freezes.
    r=subprocess.run([FF,'-hide_banner','-i',str(video),'-vf','blackdetect=d=0.03:pix_th=0.10,freezedetect=n=-50dB:d=0.7','-an','-f','null','NUL'],capture_output=True,text=True)
    (out/'decode_checks.log').write_text(r.stderr,encoding='utf8')
    print('Review:',len(times),'frames',math.ceil(len(times)/12),'sheets',flush=True)
if __name__=='__main__':main()

"""Sonoridad medida, preview de dos pasadas, extracción del MP4 y validación final."""
import json,math,re,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;ROOT=P.parents[1];PREP=P/'_prep';RENDER=ROOT/'Render'
FF=shutil.which('ffmpeg');FP=str(Path(FF).with_name('ffprobe.exe'))
master=RENDER/'Video8_Libya.mp4';upload=RENDER/'Video8_upload.mp4'
def run(args,log=None):
    r=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if log:(PREP/log).write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError('Command failed: '+r.stderr[-3000:])
    return r
def probe(path):return json.loads(run([FP,'-v','error','-show_format','-show_streams','-of','json',path]).stdout)
def loud(path,log):
    r=run([FF,'-hide_banner','-nostats','-i',path,'-vn','-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','NUL'],log)
    return json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}')+1])
def extract(path,t,out):run([FF,'-y','-loglevel','error','-ss',str(t),'-i',path,'-frames:v','1','-q:v','2',out])
if __name__=='__main__':
    assert master.exists()
    import engine as E
    from review import stamp
    srt='\n'.join(f"{i}\n{stamp(a)} --> {stamp(b)}\n{' '.join(w['w'] for w in g)}\n" for i,(a,b,g) in enumerate(E.build_subs(),1))
    (P/'Video8_Libya.srt').write_text(srt,encoding='utf-8')
    (RENDER/'Video8_Libya.srt').write_text(srt,encoding='utf-8')
    l=loud(master,'master_loudness.log');print('master LUFS',l['input_i'],flush=True)
    if abs(float(l['input_i'])+14)>.12:
        delta=-14-float(l['input_i']);tmp=PREP/'master_corrected.mp4'
        run([FF,'-y','-loglevel','error','-i',master,'-map','0:v','-map','0:a','-c:v','copy','-af',f'volume={delta}dB','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',tmp])
        tmp.replace(master);l=loud(master,'master_loudness.log')
    common=[FF,'-y','-hide_banner','-nostats','-i',master,'-vf','scale=480:270:flags=lanczos,fps=10','-c:v','libx264','-preset','slow','-tune','animation','-threads','4','-b:v','50k','-pix_fmt','yuv420p','-passlogfile',PREP/'upload2pass']
    run(common+['-pass','1','-an','-f','null','NUL'],'upload_pass1.log');print('upload pass 1 complete',flush=True)
    run(common+['-pass','2','-af','loudnorm=I=-14:TP=-5:LRA=11','-c:a','aac','-ac','1','-b:a','32k','-ar','32000','-movflags','+faststart',upload],'upload_pass2.log');print('upload pass 2 complete',flush=True)
    assert upload.stat().st_size<=10_000_000,upload.stat().st_size
    ul=loud(upload,'upload_loudness.log')
    if float(ul['input_tp'])>-.3 or abs(float(ul['input_i'])+14)>.2:
        from safe_preview import protect
        protect(upload,master);ul=loud(upload,'upload_loudness.log')
    if abs(float(ul['input_i'])+14)>.18 and float(ul['input_tp'])>0:
        tmp=PREP/'upload_corrected.mp4';delta=-14-float(ul['input_i'])
        run([FF,'-y','-loglevel','error','-i',upload,'-map','0:v','-map','0:a','-c:v','copy','-af',f'volume={delta}dB','-c:a','aac','-ac','1','-b:a','32k','-ar','32000','-movflags','+faststart',tmp])
        tmp.replace(upload);ul=loud(upload,'upload_loudness.log')
    for path in [master,upload]:
        run([FF,'-v','error','-xerror','-err_detect','explode','-threads','2','-i',path,'-f','null','NUL'],path.stem+'_decode.log')
        print('decoded',path.name,flush=True)
    # Controls come from the encoded master, not only the frame renderer.
    for t in range(6):extract(master,t,PREP/f'chk_{t:03}.jpg')
    frames=[]
    for t in range(0,900,30):
        out=PREP/f'contact_{t:03}.jpg';extract(master,t,out);frames.append((t,out))
    sheet=Image.new('RGB',(1920,math.ceil(len(frames)/4)*290),(17,23,28));d=ImageDraw.Draw(sheet)
    for i,(t,path) in enumerate(frames):
        im=Image.open(path).resize((480,270),Image.Resampling.LANCZOS);x=i%4*480;y=i//4*290;sheet.paste(im,(x,y));d.text((x+8,y+271),f'{t//60:02}:{t%60:02}',fill='white')
    sheet.save(PREP/'sheet.jpg',quality=88)
    hook=Image.new('RGB',(1440,540))
    for i in range(6):hook.paste(Image.open(PREP/f'chk_{i:03}.jpg').resize((480,270)),((i%3)*480,(i//3)*270))
    hook.save(PREP/'hook_review.jpg',quality=90)
    gp=json.loads((P/'guion.json').read_text(encoding='utf-8'))
    metrics={'spoken_words':sum(len(s['text'].split()) for s in gp['scenes']),'master':{'probe':probe(master),'bytes':master.stat().st_size,'lufs':float(l['input_i']),'true_peak_dbtp':float(l['input_tp']),'decode':'passed'},'upload':{'probe':probe(upload),'bytes':upload.stat().st_size,'lufs':float(ul['input_i']),'true_peak_dbtp':float(ul['input_tp']),'two_pass':True,'decode':'passed'},'visual_review':'pending final encoded contact sheet inspection','srt':'Render/Video8_Libya.srt','thumbnails':[str(p.relative_to(ROOT)) for p in sorted((ROOT/'Miniatura/Libya').glob('*.png'))]}
    assert abs(metrics['master']['lufs']+14)<=.2
    assert -15.3<=metrics['upload']['lufs']<=-13.8
    assert metrics['upload']['true_peak_dbtp']<=0
    for k in ['master','upload']:assert abs(float(metrics[k]['probe']['format']['duration'])-900)<.2
    v=next(s for s in metrics['master']['probe']['streams'] if s['codec_type']=='video');assert (v['width'],v['height'])==(1920,1080)
    (PREP/'verification.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
    report=f'''# Producción de Video 8 — Libya

Guion: 2166 palabras, 175 escenas, primera frase de 5 palabras. Cada escena termina una frase completa. Máster de 15:00, 1920×1080 a 30 fps. Voz Ryan generada con Scripts/voz.py a +4 %, seguida de atempo 0.8998809126 con tono preservado. Los tiempos y subtítulos proceden de las marcas de palabra originales escaladas con el audio.

Motor: engine.py, mapa.py y build.py locales, con storyboard de Libia, mapas Natural Earth, subtítulos por frases sin caja y sin titular superior. Hook ilustrado en hook2d.py sobre el mismo puerto de Benghazi del resto del vídeo. No utiliza los fotogramas de Blender.

El dron avanza desde el cuadro cero e impacta a los 0,20 segundos. La corbeta 734 ocupa más del 40 % de la altura inicial; el plano se abre al puerto. Fuego deformable multicapa, destello, chispas balísticas, agua, ondas y humo ascendente se calculan por fotograma; temblor decreciente y escora animada. No hay sprite de explosión. Se retiraron las notas editoriales; ANIMATED RECONSTRUCTION aparece solo en el ataque y el pecio. Nombres geográficos de 34 px. Los mapas tienen acercamientos suaves de seis segundos a sus lugares, barcos en navegación, conexiones que se trazan y personajes con movimiento de torso y brazo. Las frases de más de ocho segundos cambian composición a los 7,5 segundos.

Correcciones durante la revisión: márgenes transparentes de los personajes; diferenciación de carguero, petrolero y gasero; buque de desembarco distinto de Merkury para Crimea; corbeta volcada y parcialmente sumergida; barcos situados en el mar y traslados terrestres anclados a lugares; conexiones de personajes y acuerdos con puntos del mapa; retirada de dos mapas generados incorrectos de las miniaturas.

## Mediciones finales

- Máster: {metrics['master']['lufs']:.2f} LUFS; {metrics['master']['true_peak_dbtp']:.2f} dBTP; {metrics['master']['bytes']:,} bytes.
- Copia ligera: {metrics['upload']['lufs']:.2f} LUFS; {metrics['upload']['bytes']:,} bytes; 480×270 a 10 fps; vídeo H.264 de dos pasadas y audio AAC mono. Su compresión permite cumplir el límite de 10 MB; publicar el máster de 1080p.
- Decodificación completa con -xerror y -err_detect explode: ambos archivos pasan.
- Fotogramas de control y hoja cada 30 segundos extraídos del máster codificado. Estado de revisión visual final: consultar _prep/verification.json.

## Reproducción del montaje final

Desde la raíz del proyecto, con los audios y recursos ya presentes:

```powershell
python 'Guiones/Video 8 - Libya/build.py'
python 'Guiones/Video 8 - Libya/finalize.py'
python 'Guiones/Video 8 - Libya/package.py'
```

Para regenerar la voz desde el guion: Scripts/voz.py, luego Scripts/short_join.py y retime.py. retime.py conserva _prep/voz_raw.wav y _prep/timeline_raw.json para que el ajuste de tempo sea reproducible y no se aplique dos veces. prepare.py y configure.py documentan la importación inicial de V7; no son necesarios para reconstruir la versión final.
'''
    (P/'Producción (Codex).md').write_text(report,encoding='utf-8')
    print('verified',master.name,metrics['master']['lufs'],upload.stat().st_size,'bytes',flush=True)

"""Deterministic local thumbnail composition. No generation or uploads."""
from pathlib import Path
import argparse
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

ROOT = Path(r'E:\Historias TIK\WarMap Stick')
OUT = ROOT / 'Miniatura/Crimea'
WORK = OUT / '_work'
SIZE = (1280, 720)
YELLOW = '#FFD628'
WHITE = '#FFFFFF'
RED = '#FF393E'
IMPACT = r'C:\Windows\Fonts\impact.ttf'
ARIAL = r'C:\Windows\Fonts\arialbd.ttf'
RESAMPLE = Image.Resampling.LANCZOS
A_FRAME = 'f_0052.png'


def font(size):
    return ImageFont.truetype(IMPACT, size)


def gradient_mask(left, right, max_alpha=255, size=SIZE):
    x = np.arange(size[0], dtype=float)
    a = np.clip((right - x) / (right - left), 0, 1)
    a = a * a * (3 - 2 * a)
    return Image.fromarray(np.tile((a * max_alpha).astype('uint8'), (size[1], 1)))


def color_layer(color, alpha):
    im = Image.new('RGBA', alpha.size, color)
    im.putalpha(alpha)
    return im


def vignette(im, strength=.24):
    y, x = np.mgrid[0:im.height, 0:im.width]
    r = ((x - im.width * .55) / (im.width * .75)) ** 2 + ((y - im.height * .45) / (im.height * .85)) ** 2
    mask = Image.fromarray((np.clip(r * strength, 0, .4) * 255).astype('uint8'))
    return Image.alpha_composite(im.convert('RGBA'), color_layer('#020815', mask))


def text(im, word, x, y, size, fill=YELLOW, maxwidth=None, stroke=9):
    f = font(size)
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    bb = d.textbbox((0, 0), word, font=f, stroke_width=stroke)
    pad = 20
    tile = Image.new('RGBA', (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2))
    ImageDraw.Draw(tile).text((pad - bb[0], pad - bb[1]), word, font=f, fill=fill,
                              stroke_width=stroke, stroke_fill='#030508')
    tile = tile.crop(tile.getbbox())
    if maxwidth and tile.width > maxwidth:
        tile = tile.resize((maxwidth, round(tile.height * maxwidth / tile.width)), RESAMPLE)
    shadow = Image.new('RGBA', im.size)
    al = tile.getchannel('A').filter(ImageFilter.GaussianBlur(6))
    shadow.paste(color_layer('#000000', al.point(lambda v: round(v * .85))), (x + 6, y + 9))
    im = Image.alpha_composite(im, shadow)
    im.alpha_composite(tile, (x, y))
    return im, (x, y, x + tile.width, y + tile.height)


def glow(im, mask, color, radius=16, opacity=.7):
    g = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: round(v * opacity))
    return Image.alpha_composite(im, color_layer(color, g))


def arrow(im, points, width=7):
    layer = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(layer)
    d.line(points, fill='#06070A', width=width + 6, joint='curve')
    d.line(points, fill=RED, width=width, joint='curve')
    a, b = points[-5], points[-1]
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L = 27
    head = [(b[0] + L * math.cos(ang + 2.65), b[1] + L * math.sin(ang + 2.65)), b,
            (b[0] + L * math.cos(ang - 2.65), b[1] + L * math.sin(ang - 2.65))]
    d.line(head, fill='#06070A', width=width + 6, joint='curve')
    d.line(head, fill=RED, width=width, joint='curve')
    return Image.alpha_composite(im, layer)


def bridge_icon(im, center, width=160, angle=0):
    """A clear red broken bridge symbol, drawn locally with a real central gap."""
    tile = Image.new('RGBA', (260, 155))
    d = ImageDraw.Draw(tile)
    col = RED
    # Separate decks and the two fractured arch halves.
    d.line([(20, 98), (96, 98), (107, 112)], fill=col, width=12, joint='curve')
    d.line([(151, 107), (163, 98), (240, 98)], fill=col, width=12, joint='curve')
    d.line([(25, 97), (52, 64), (77, 48), (103, 44)], fill=col, width=9, joint='curve')
    d.line([(158, 44), (184, 48), (210, 64), (236, 97)], fill=col, width=9, joint='curve')
    for x, yy in [(51, 67), (76, 49), (184, 49), (210, 67)]:
        d.line([(x, yy), (x, 96)], fill=col, width=6)
    for x in [36, 224]:
        d.line([(x, 100), (x, 132)], fill=col, width=10)
    # Lightning-shaped cut separates both halves.
    d.line([(136, 20), (120, 56), (138, 66), (122, 99)], fill='#FFE7DC', width=8, joint='curve')
    tile = tile.resize((width, round(width * 155 / 260)), RESAMPLE)
    if angle:
        tile = tile.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    x, y = round(center[0] - tile.width / 2), round(center[1] - tile.height / 2)
    m = Image.new('L', im.size)
    m.paste(tile.getchannel('A'), (x, y))
    im = glow(im, m, '#FF202D', 14, 1.0)
    sh = Image.new('RGBA', im.size)
    sh.paste(color_layer('#000000', tile.getchannel('A').filter(ImageFilter.MaxFilter(7))), (x, y + 3))
    im = Image.alpha_composite(im, sh)
    im.alpha_composite(tile, (x, y))
    return im


def compose_a():
    src = Image.open(ROOT / 'Guiones/Video 6 - Crimea/render3d/hook' / A_FRAME).convert('RGB')
    src = ImageEnhance.Color(src).enhance(1.24)
    src = ImageEnhance.Contrast(src).enhance(1.17)
    src = ImageEnhance.Brightness(src).enhance(1.10)
    src = src.filter(ImageFilter.UnsharpMask(1.5, 120, 3))
    base = src.resize(SIZE, RESAMPLE).filter(ImageFilter.GaussianBlur(22)).convert('RGBA')
    base = Image.blend(base, Image.new('RGBA', SIZE, '#07101A'), .6)
    zoom = src.resize((1344, 756), RESAMPLE)
    scene = Image.new('RGBA', SIZE)
    scene.paste(zoom, (230, -36))
    mask = ImageChops.invert(gradient_mask(265, 520))
    base = Image.composite(scene, base, mask)
    base = Image.alpha_composite(base, color_layer('#030A13', gradient_mask(370, 650, 225)))
    base = vignette(base, .13)
    # The foreground arch is submerged; point into its large water splash.
    p0, p1, p2, p3 = (642, 247), (800, 174), (1003, 228), (1030, 490)
    pts = []
    for u in np.linspace(0, 1, 60):
        pts.append(tuple(round((1-u)**3*p0[j]+3*(1-u)**2*u*p1[j]+3*(1-u)*u*u*p2[j]+u**3*p3[j]) for j in (0,1)))
    base = arrow(base, pts, 7)
    base, _ = text(base, 'WHY', 38, 76, 196, WHITE, maxwidth=455, stroke=10)
    base, _ = text(base, 'THIS', 38, 274, 196, WHITE, maxwidth=455, stroke=10)
    base, _ = text(base, 'BRIDGE?', 34, 475, 166, YELLOW, maxwidth=504, stroke=10)
    return base


def crimea_sticker(width=316):
    """Use the same Natural Earth Crimea geometry as the supplied video renderer."""
    geo = json.loads((ROOT / 'Guiones/Video 6 - Crimea/_prep/geo.json').read_text())['crimea']
    k = math.cos(math.radians(47))
    rings = [[(p[0]*k, -p[1]) for p in ring] for ring in geo]
    flat = [p for r in rings for p in r]
    x0, y0 = min(p[0] for p in flat), min(p[1] for p in flat)
    x1, y1 = max(p[0] for p in flat), max(p[1] for p in flat)
    scale = (width - 50) / (x1 - x0)
    h = round((y1-y0)*scale+50)
    m = Image.new('L', (width*3, h*3))
    d = ImageDraw.Draw(m)
    for ring in rings:
        d.polygon([((p[0]-x0)*scale*3+75,(p[1]-y0)*scale*3+75) for p in ring],fill=255)
    m=m.resize((width,h),RESAMPLE)
    y,x=np.mgrid[0:h,0:width]
    val=np.clip(1-np.hypot((x-width*.35)/(width*.85),(y-h*.25)/(h*.9)),0,1)
    rgb=np.zeros((h,width,3),dtype='uint8')
    rgb[:,:,0]=12+val*35
    rgb[:,:,1]=80+val*90
    rgb[:,:,2]=188+val*67
    im=Image.fromarray(rgb).convert('RGBA'); im.putalpha(m)
    edge=ImageChops.subtract(m.filter(ImageFilter.MaxFilter(9)), m.filter(ImageFilter.MinFilter(3)))
    im=Image.alpha_composite(im,color_layer('#A4F2FF',edge))
    return im,m


def compose_b():
    src=Image.open(WORK/'video_0383.0s.png').convert('RGB')
    # This crop excludes all baked-in text and the original general.
    base=src.crop((0,170,1040,755)).resize(SIZE,RESAMPLE).filter(ImageFilter.GaussianBlur(7))
    base=ImageEnhance.Color(base).enhance(1.35)
    base=ImageEnhance.Brightness(base).enhance(.54).convert('RGBA')
    base=Image.alpha_composite(base,color_layer('#020811',gradient_mask(430,940,200)))
    base=vignette(base,.20)
    general=Image.open(ROOT/'Guiones/Video 6 - Crimea/_prep/cut_el_general.png').convert('RGBA')
    general=general.resize((round(general.width*790/general.height),790),RESAMPLE)
    # Lower legs deliberately extend past the frame; face, hand and medals stay large.
    gx,gy=748,12
    gm=Image.new('L',SIZE); gm.paste(general.getchannel('A'),(gx,gy))
    base=glow(base,gm,'#1B90DA',22,.48)
    shadow=Image.new('RGBA',SIZE)
    shadow.paste(color_layer('#000000',general.getchannel('A').filter(ImageFilter.GaussianBlur(11))), (gx+9,gy+12))
    base=Image.alpha_composite(base,shadow)
    base.alpha_composite(general,(gx,gy))
    cr,cm=crimea_sticker(332)
    cx,cy=594,142
    m=Image.new('L',SIZE); m.paste(cm,(cx,cy))
    base=glow(base,m,'#008CFF',30,.95)
    base=glow(base,m,'#00CCFF',10,.65)
    base.alpha_composite(cr,(cx,cy))
    base=bridge_icon(base,(814,425),134,-9)
    base,_=text(base,'WORTH',34,84,186,WHITE,maxwidth=552,stroke=10)
    base,_=text(base,'THE',38,281,172,WHITE,maxwidth=430,stroke=10)
    base,_=text(base,'COST?',34,465,194,YELLOW,maxwidth=560,stroke=10)
    return base


def compose_c():
    src=Image.open(WORK/'video_0352.0s.png').convert('RGB')
    underlay=Image.open(WORK/'map_352_clean_underlay.png').convert('RGB')
    # Restore the subtitle band using the exact map renderer/view, without text.
    # Top headline is outside the final crop. No content-aware or AI fill is used.
    band=(350,922,1540,1002)
    src.paste(underlay.crop(band),band[:2])
    src.save(WORK/'video_0352.0s_text_removed.png')
    box=(200,170,1800,1070)
    base=src.crop(box).resize(SIZE,RESAMPLE)
    base=ImageEnhance.Color(base).enhance(1.38)
    base=ImageEnhance.Contrast(base).enhance(1.22)
    base=ImageEnhance.Brightness(base).enhance(.84).convert('RGBA')
    # A calm top band gives the headline an uninterrupted silhouette.
    y=np.arange(720)
    a=(np.clip((245-y)/180,0,1)*175).astype('uint8')
    topmask=Image.fromarray(np.tile(a[:,None],(1,1280)))
    base=Image.alpha_composite(base,color_layer('#030A16',topmask))
    # Reinforce the real road geometry from the source frame.
    corridor=[(1675,361),(1380,377),(1255,397),(1114,470),(840,470),(758,595),(670,686),(651,792),(595,1002)]
    pts=[((x-box[0])*.8,(y-box[1])*.8) for x,y in corridor]
    m=Image.new('L',SIZE); ImageDraw.Draw(m).line(pts,fill=255,width=9,joint='curve')
    base=glow(base,m,'#FFC31D',19,.9)
    layer=Image.new('RGBA',SIZE); d=ImageDraw.Draw(layer)
    d.line(pts,fill='#FFC629',width=10,joint='curve')
    d.line(pts,fill='#FFF5AC',width=4,joint='curve')
    base=Image.alpha_composite(base,layer)
    # Kerch bridge is tiny at the wide map scale; place the icon at its actual map point.
    bridgepoint=((1058.88-box[0])*.8,(901.479-box[1])*.8)
    base=bridge_icon(base,bridgepoint,188,-14)
    base=vignette(base,.10)
    # The entire three-word question remains readable at 160px wide.
    base,_=text(base,'NOT CUT OFF?',38,27,170,YELLOW,maxwidth=1202,stroke=10)
    return base


names=[('A','Crimea_A_WHY_THIS_BRIDGE.jpg',compose_a),
       ('B','Crimea_B_WORTH_THE_COST.jpg',compose_b),
       ('C','Crimea_C_NOT_CUT_OFF.jpg',compose_c)]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only',nargs='+',choices=['A','B','C'],default=['A','B','C'],
                    help='Rebuild only these thumbnails; reuse the others in review sheets.')
args=parser.parse_args()
finals=[]
for letter,name,fn in names:
    if letter in args.only:
        im=fn().convert('RGB')
        im.save(OUT/name,quality=95,subsampling=0,optimize=True,dpi=(72,72))
        im.resize((320,180),RESAMPLE).save(OUT/f'_small_{letter}.jpg',quality=94,subsampling=0,optimize=True)
    finals.append((letter,Image.open(OUT/name)))

sheet=Image.new('RGB',(1920,416),'#0C121D')
d=ImageDraw.Draw(sheet)
labels=['A  |  WHY THIS BRIDGE?','B  |  WORTH THE COST?','C  |  NOT CUT OFF?']
for i,((letter,im),label) in enumerate(zip(finals,labels)):
    x=i*640
    d.text((x+20,14),label,font=ImageFont.truetype(ARIAL,24),fill=YELLOW)
    sheet.paste(im.resize((640,360),RESAMPLE),(x,56))
sheet.save(OUT/'_sheet.jpg',quality=94,subsampling=0,optimize=True)

tiny=Image.new('RGB',(480,90))
for i,(_,im) in enumerate(finals): tiny.paste(im.resize((160,90),RESAMPLE),(i*160,0))
tiny.save(WORK/'readability_160.jpg',quality=95,subsampling=0)

manifest={
    'A':{'file':names[0][1],'source':f'Guiones/Video 6 - Crimea/render3d/hook/{A_FRAME}','method':'Real source render, 0.7x scale at (+230,-36), left gradient, PIL text and red arrow','arrow_target':[1030,490],'arrow_subject':'Water splash where the foreground arch fell'},
    'B':{'file':names[1][1],'source':'Render/Video6_Crimea.mp4 @ 00:06:23.000','background_crop':[0,170,1040,755],'sticker':'Guiones/Video 6 - Crimea/_prep/cut_el_general.png','crimea_geometry':'Guiones/Video 6 - Crimea/_prep/geo.json'},
    'C':{'file':names[2][1],'source':'Render/Video6_Crimea.mp4 @ 00:05:52.000','crop':[200,170,1800,1070],'subtitle_restoration':'Exact original region_scene map at View(36.0,46.6,10.0) underlay, band (350,922,1540,1002)','bridge_icon':'PIL graphic at actual Kerch map coordinates'},
    'spec':{'size':[1280,720],'format':'JPEG','text_font':'Impact','yellow':'#FFD628','uploads':False,'generative_ai':False}
}
(WORK/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for _,name,_ in names:
    p=OUT/name
    with Image.open(p) as im:
        assert im.size==SIZE and im.format=='JPEG' and p.stat().st_size<2_000_000
        print(name,im.size,f'{p.stat().st_size:,} bytes')

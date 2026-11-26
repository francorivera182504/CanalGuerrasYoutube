"""Miniaturas Video 7 (Israel, Palestina e Iran): fondos de nuestras escenas + stickers propios + texto Impact."""
import os, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CUT = os.path.join(ROOT, 'Guiones', 'Video 7 - Middle East', '_prep'); WORK = os.path.join(HERE, '_work')
sys.path.insert(0, os.path.join(ROOT, 'Miniatura', 'Nuevas')); import poner_texto as PT
PT.HERE = HERE
W, Y, R = PT.W, PT.Y, PT.R

def bg(sid, dark=0.8, blur=0):
    im = Image.open(os.path.join(WORK, f'bg_{sid}.jpg')).convert('RGB').resize((1280, 720), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return ImageEnhance.Brightness(im).enhance(dark).convert('RGBA')

def stick(can, name, h, xy, flip=False, glow=None):
    s = Image.open(os.path.join(CUT, f'cut_{name}.png')).convert('RGBA')
    s = s.resize((int(s.width * h / s.height), h), Image.LANCZOS)
    if flip: s = s.transpose(Image.FLIP_LEFT_RIGHT)
    x, y = xy[0] - s.width // 2, xy[1] - s.height
    if glow:
        g = Image.new('RGBA', s.size, glow + (0,)); g.putalpha(s.split()[3].filter(ImageFilter.GaussianBlur(26)).point(lambda a: int(min(255, a * 1.1))))
        can.alpha_composite(g, (x, y))
    sh = Image.new('RGBA', s.size, (0, 0, 0, 0)); sh.putalpha(s.split()[3].filter(ImageFilter.GaussianBlur(12)).point(lambda a: int(a * 0.6)))
    can.alpha_composite(sh, (x + 10, y + 12)); can.alpha_composite(s, (x, y))

def glowline(can, pts, col, w=10):
    L = Image.new('RGBA', can.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.line(pts, fill=col + (255,), width=w * 3, joint='curve'); L = L.filter(ImageFilter.GaussianBlur(14))
    d = ImageDraw.Draw(L); d.line(pts, fill=col + (255,), width=w, joint='curve'); d.line(pts, fill=(255, 255, 255, 230), width=max(2, w // 3), joint='curve')
    can.alpha_composite(L)

def arcpts(p0, p1, hgt, n=60):
    return [(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t - hgt * math.sin(math.pi * t)) for t in [i / n for i in range(n + 1)]]

# A: HOW IT CONNECTS - mapa Levante + Iran, arco que los une, 3 lideres por igual
a = bg('702', 0.85)
glowline(a, arcpts((300, 330), (1010, 300), 150), (255, 214, 40), 9)
stick(a, 'el_isr_leader', 330, (170, 715), glow=(80, 150, 255)); stick(a, 'el_pal_leader', 330, (420, 715), flip=True, glow=(60, 220, 120))
stick(a, 'el_iran_leader', 360, (1000, 715), glow=(255, 200, 40))
a.convert('RGB').save(os.path.join(HERE, 'ME_A_how_it_connects.png'))

# B: ONE BUILDING - embajada grande, multitud, fondo oscuro
b = bg('905', 0.45, blur=6)
stick(b, 'el_crowd_tehran', 360, (330, 715), glow=(255, 214, 40)); stick(b, 'el_embassy', 520, (900, 700), glow=(255, 214, 40))
b.convert('RGB').save(os.path.join(HERE, 'ME_B_one_building.png'))

# C: WHY NO PEACE? - negociadores con grieta roja entre ellos
c = bg('206', 0.55, blur=5)
stick(c, 'el_negotiators', 470, (640, 715), glow=(120, 180, 255))
crack = [(640, 230), (615, 320), (662, 400), (628, 480), (670, 560), (640, 640), (655, 720)]
glowline(c, crack, (255, 59, 48), 10)
c.convert('RGB').save(os.path.join(HERE, 'ME_C_why_no_peace.png'))

T = {
    'ME_A_how_it_connects': dict(lines=[[('HOW IT ', W), ('CONNECTS', Y)]], pos='top', size=150),
    'ME_B_one_building':    dict(lines=[[('ONE', W)], [('BUILDING', Y)]], pos='tl', size=190),
    'ME_C_why_no_peace':    dict(lines=[[('WHY ', W), ('NO PEACE?', Y)]], pos='top', size=160),
}
outs = [PT.render(n, cfg) for n, cfg in T.items()]
sheet = Image.new('RGB', (1920, 360 + 141), (240, 240, 240))
for i, o in enumerate(outs):
    sheet.paste(Image.open(o).resize((640, 360)), (i * 640, 0)); sheet.paste(Image.open(o).resize((250, 141)), (i * 640 + 195, 360))
sheet.save(os.path.join(HERE, '_sheet.jpg'), quality=88); print(outs)

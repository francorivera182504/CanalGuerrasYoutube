"""Texto estilo nicho (caja roja/negra con letras blancas) sobre el arte v2 de Codex.
python texto_v2.py -> ME2_A.jpg, ME2_B.jpg, ME2_C.jpg + _sheet_final.jpg
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
F = r'C:\Windows\Fonts\ariblk.ttf'
RED, BLACK, WHITE, YEL = (228, 28, 36), (12, 12, 14), (255, 255, 255), (255, 214, 40)

def load(name):
    im = Image.open(os.path.join(HERE, name)).convert('RGB'); w, h = im.size
    if abs(w / h - 16 / 9) > 0.01:
        if w / h > 16 / 9: nw = int(h * 16 / 9); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else: nh = int(w * 9 / 16); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((1280, 720), Image.LANCZOS).convert('RGBA')

def box(can, text, xy, size, bg=RED, fg=WHITE, anchor='l', pad=(22, 10), tilt=0):
    f = ImageFont.truetype(F, size); d = ImageDraw.Draw(can)
    l, t, r, b = d.textbbox((0, 0), text, font=f); tw, th = r - l, b - t
    W, H = tw + pad[0] * 2, th + pad[1] * 2
    L = Image.new('RGBA', (W + 40, H + 40), (0, 0, 0, 0)); dl = ImageDraw.Draw(L)
    dl.rectangle((20, 20, 20 + W, 20 + H), fill=bg + (255,))
    dl.text((20 + pad[0] - l, 20 + pad[1] - t), text, font=f, fill=fg)
    if tilt: L = L.rotate(tilt, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', L.size, (0, 0, 0, 0)); sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.7)))
    x = xy[0] - (L.width // 2 if anchor == 'c' else 20); y = xy[1] - 20
    can.alpha_composite(sh, (x + 6, y + 8)); can.alpha_composite(L, (x, y))

def outline(can, text, xy, size, fg=WHITE, anchor='l'):
    f = ImageFont.truetype(F, size); d = ImageDraw.Draw(can)
    w = d.textlength(text, font=f); x = xy[0] - (w / 2 if anchor == 'c' else 0)
    L = Image.new('RGBA', can.size, (0, 0, 0, 0)); ImageDraw.Draw(L).text((x, xy[1]), text, font=f, fill=fg, stroke_width=size // 14, stroke_fill=BLACK)
    sh = Image.new('RGBA', can.size, (0, 0, 0, 0)); sh.putalpha(L.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.8)))
    can.alpha_composite(sh, (6, 8)); can.alpha_composite(L)

outs = []
def save(can, name):
    p = os.path.join(HERE, name); can.convert('RGB').save(p, quality=92); outs.append(p)

if os.path.exists(os.path.join(HERE, 'v2_A_three_leaders.png')):
    a = load('v2_A_three_leaders.png')
    outline(a, '78 YEARS', (640, 14), 96, anchor='c'); box(a, 'OF CONFLICT', (640, 128), 60, anchor='c')
    save(a, 'ME2_A_78_years.jpg')
if os.path.exists(os.path.join(HERE, 'v2_B_1948_2026_split.png')):
    b = load('v2_B_1948_2026_split.png')
    box(b, '1948', (40, 30), 92, bg=BLACK, tilt=0); box(b, '2026', (930, 30), 92, bg=RED)
    save(b, 'ME2_B_1948_2026.jpg')
if os.path.exists(os.path.join(HERE, 'v2_C_map_fire.png')):
    c = load('v2_C_map_fire.png')
    outline(c, 'HOW IT', (40, 24), 100); box(c, 'BEGAN', (40, 148), 96)
    save(c, 'ME2_C_how_it_began.jpg')

if outs:
    S = Image.new('RGB', (640 * len(outs), 360 + 141), (240, 240, 240))
    for i, o in enumerate(outs):
        S.paste(Image.open(o).resize((640, 360)), (i * 640, 0)); S.paste(Image.open(o).resize((250, 141)), (i * 640 + 195, 360))
    S.save(os.path.join(HERE, '_sheet_final.jpg'), quality=88)
print(outs)

"""Pone el texto grande (Impact, blanco y amarillo, borde negro y sombra) sobre las ilustraciones de Codex.
Uso: python poner_texto.py            -> procesa todas las de TEXTOS
     python poner_texto.py PH_D_no_oil -> solo esa
Cada línea es una lista de (palabra, color). pos = 'tl' (arriba izquierda), 'tr', 'top' (centrado arriba), 'bl'.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
IMPACT = r'C:\Windows\Fonts\impact.ttf'
W, Y, R = '#FFFFFF', '#FFD628', '#FF3B30'

TEXTOS = {
    'PH_D_no_oil':         dict(lines=[[('NO', W)], [('OIL?', Y)]], pos='tl', size=230),
    'PH_E_face_off':       dict(lines=[[('BIG ', W), ('MISTAKE?', Y)]], pos='top', size=170),
    'WW_D_stalin_shocked': dict(lines=[[('STALIN', W)], [('FAILED?', Y)]], pos='tl', size=172),
    'WW_E_giant_vs_tiny':  dict(lines=[[('3.7M', Y)], [('vs ', W), ('170M', R)]], pos='tl', size=190),
    'CR_D_putin_crimea':   dict(lines=[[('WHY', W)], [('CRIMEA?', Y)]], pos='tl', size=210),
    'CR_E_one_bridge':     dict(lines=[[('ONE', W)], [('BRIDGE', Y)]], pos='tl', size=220),
    'IR_A_deal_torn':      dict(lines=[[('STILL', W)], [('NOT', W)], [('OVER?', Y)]], pos='tl', size=175),
    'IR_B_hormuz_choke':   dict(lines=[[('NO', W)], [('END?', Y)]], pos='tl', size=230),
    # Ronda "minas de oro" (25-nov-2026)
    'HZ_A_one_wrong_move': dict(lines=[[('ONE ', W), ('WRONG ', Y), ('MOVE', W)]], pos='top', size=150),
    'CR_F_feeds_the_war':  dict(lines=[[('FEEDS ', Y), ('THE WAR', W)]], pos='top', size=160),
    'WW_F_where_are_they': dict(lines=[[('WHERE', Y)], [('ARE THEY?', W)]], pos='tl', size=150),
    'PH_F_missed_them':    dict(lines=[[('MISSED ', Y), ('THEM', W)]], pos='top', size=170),
    'VN_A_how_america_lost': dict(lines=[[('HOW AMERICA ', W), ('LOST', Y)]], pos='top', size=140),
    'IR_C_now_what':       dict(lines=[[('NOW', W)], [('WHAT?', Y)]], pos='tr', size=200),
}

def render(name, cfg):
    src = os.path.join(HERE, name + '.png')
    im = Image.open(src).convert('RGB')
    # recorte a 16:9 y 1280x720
    w, h = im.size
    if abs(w / h - 16 / 9) > 0.01:
        if w / h > 16 / 9:
            nw = int(h * 16 / 9); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = int(w * 9 / 16); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im = im.resize((1280, 720), Image.LANCZOS)

    size = cfg['size']; f = ImageFont.truetype(IMPACT, size); stroke = max(8, size // 18)
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    # medir líneas
    metrics = []
    for line in cfg['lines']:
        lw = sum(d.textlength(t, font=f) for t, _ in line)
        metrics.append(lw)
    lh = int(size * 1.0)
    total_h = lh * len(cfg['lines'])
    maxw = max(metrics)
    if cfg['pos'] == 'top':
        x0, y0 = None, 18
    elif cfg['pos'] == 'bl':
        x0, y0 = 40, 720 - total_h - 30
    elif cfg['pos'] == 'tr':
        x0, y0 = 1280 - maxw - 40, 18
    else:
        x0, y0 = 40, 18
    for i, line in enumerate(cfg['lines']):
        x = (1280 - metrics[i]) / 2 if x0 is None else x0
        y = y0 + i * lh
        for t, col in line:
            d.text((x, y), t, font=f, fill=col, stroke_width=stroke, stroke_fill='#05060A')
            x += d.textlength(t, font=f)
    # sombra
    alpha = layer.split()[3]
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.8)))
    base = im.convert('RGBA')
    base.alpha_composite(shadow, (8, 10))
    base.alpha_composite(layer)
    out = os.path.join(HERE, name + '.jpg')
    base.convert('RGB').save(out, quality=92)
    return out

if __name__ == '__main__':
    names = sys.argv[1:] or list(TEXTOS)
    outs = [render(n, TEXTOS[n]) for n in names if os.path.exists(os.path.join(HERE, n + '.png'))]
    # hoja de contacto + vista pequeña (como en el feed del móvil)
    if outs:
        cols = 2; tw, th = 640, 360
        S = Image.new('RGB', (cols * tw, ((len(outs) + 1) // 2) * th), 'black')
        for i, o in enumerate(outs):
            S.paste(Image.open(o).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
        tag = os.environ.get('SHEET', '')
        S.save(os.path.join(HERE, f'_sheet{tag}.jpg'), quality=88)
        sm = Image.new('RGB', (len(outs) * 250, 141), 'white')
        for i, o in enumerate(outs):
            sm.paste(Image.open(o).resize((246, 138)), (i * 250, 1))
        sm.save(os.path.join(HERE, f'_small{tag}.jpg'), quality=90)
    print('\n'.join(outs))

"""S13 Krummlauf — primer Short con la fórmula de los 3 s (cuadro 0 = clímax, sujeto grande, contraste, cambio cada <=1.5 s).
Escenario: calle en ruinas + mapa real (Natural Earth). Sin plantilla: subtítulo blanco simple, rótulos atlas.
python build.py --prep | --frame t... | (render)."""
import json, math, os, subprocess, sys, re
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
PREP = os.path.join(HERE, '_prep'); CAP = os.path.join(HERE, 'assets')
FF = r'C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
FSUB = r'C:\Windows\Fonts\seguibl.ttf'; FATL = r'C:\Windows\Fonts\georgiab.ttf'; FATI = r'C:\Windows\Fonts\georgiaz.ttf'
W, H, FPS = 1080, 1920, 30
WHITE = (255, 255, 255); RED = (225, 45, 35); GOLD = (255, 205, 90); ORANGE = (255, 150, 40)
TL = json.load(open(os.path.join(HERE, 'timeline.json'), encoding='utf8')); WORDS = TL['words']; TOTAL = TL['total']
SC = {s['id']: (s['start'], s['start'] + s['dur']) for s in TL['timeline']}
def wt(scene, word, k=0):
    hits = [w['s'] for w in WORDS if w['scene'] == scene and w['w'].lower().strip('.,?!') == word.lower()]
    return hits[k]
D = {'fonts': {}, 'texts': {}, 'img': {}}

def ease(x, kind='inout'):
    x = min(1.0, max(0.0, x))
    if kind == 'back': c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == 'out': return 1 - (1 - x) ** 3
    if kind == 'lin': return x
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind='inout'): return ease((t - t0) / max(1e-6, t1 - t0), kind)
def hsh(i, k=0): return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0

# ---------------- assets ----------------
def font(path, size):
    k = (path, int(size))
    if k not in D['fonts']: D['fonts'][k] = ImageFont.truetype(path, int(size))
    return D['fonts'][k]
def cut(name):
    im = Image.open(os.path.join(CAP, name + '.png')).convert('RGBA'); arr = np.asarray(im)
    ink = np.min(arr[:, :, :3], axis=2) < 235; lab, num = ndimage.label(ink); sizes = np.bincount(lab.ravel()); sizes[0] = 0
    keep = [i for i in range(1, num + 1) if sizes[i] > max(60, sizes.max() * .01)]
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(np.isin(lab, keep), iterations=2))
    white = (arr[:, :, :3] > 238).all(-1); wl, _ = ndimage.label(white)
    fg &= ~np.isin(wl, list(set(np.unique(np.r_[wl[0], wl[-1], wl[:, 0], wl[:, -1]])) - {0}))
    im.putalpha(Image.fromarray((fg * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(.6))); return im.crop(im.getbbox())
def img(name):
    if name not in D['img']: D['img'][name] = Image.open(os.path.join(PREP, name + '.png')).convert('RGBA')
    return D['img'][name]
def scaled(name, h, flip=False):
    key = (name, int(h), flip)
    if key not in D['img']:
        im = img(name)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = h / im.height; D['img'][key] = im.resize((max(1, int(im.width * s)), max(1, int(h))), Image.LANCZOS)
    return D['img'][key]
def sticker(can, name, x, y, h, flip=False, alpha=1.0, anchor='mb', shadow=True):
    """Pega un sticker; (x,y) = centro-abajo (mb) o centro (mm). Devuelve la caja (x0,y0,escala)."""
    im = scaled(name, h, flip)
    x0 = int(x - im.width / 2); y0 = int(y - im.height) if anchor == 'mb' else int(y - im.height / 2)
    if alpha < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    if shadow and anchor == 'mb':
        sh = Image.new('L', (int(im.width * .85), max(4, int(im.width * .12))))
        ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, sh.height - 1), fill=int(110 * alpha)); sh = sh.filter(ImageFilter.GaussianBlur(8))
        can.paste((15, 12, 10), (int(x - sh.width / 2), int(y - sh.height / 2)), sh)
    can.paste(im, (x0, y0), im)
    return x0, y0, h / img(name).height
def pt(box, fx, fy, name):
    """Punto relativo (fracción del sticker original) -> pantalla."""
    x0, y0, s = box; im = img(name); return x0 + fx * im.width * s, y0 + fy * im.height * s

def halo_text(can, s, xy, size, fill=WHITE, path=FATL, spacing=0, halo=(10, 10, 12), hw=5, alpha=1.0):
    size = max(4, int(size)); key = ('T', s, size, fill, path, spacing, halo, hw)
    if key not in D['texts']:
        f = font(path, size); pad = hw + 14
        tw = (sum(f.getlength(ch) for ch in s) + spacing * (len(s) - 1)) if spacing else f.getlength(s)
        asc, desc = f.getmetrics(); lay = Image.new('RGBA', (int(tw + 2 * pad), int(asc + desc + 2 * pad))); d = ImageDraw.Draw(lay)
        if spacing:
            x = pad
            for ch in s: d.text((x, pad), ch, font=f, fill=fill, stroke_width=hw, stroke_fill=halo); x += f.getlength(ch) + spacing
        else: d.text((pad, pad), s, font=f, fill=fill, stroke_width=hw, stroke_fill=halo)
        sh = lay.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * .55))
        if len(D['texts']) > 300: D['texts'].clear()
        D['texts'][key] = (lay, sh)
    lay, sh = D['texts'][key]
    x = xy[0] - lay.width / 2; y = xy[1] - lay.height / 2
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.getchannel('A').point(lambda v: int(v * alpha))); sh = sh.point(lambda v: int(v * alpha))
    can.paste((0, 0, 0), (int(x) + 3, int(y) + 5), sh); can.paste(lay, (int(x), int(y)), lay)
def label(can, s, xy, size, t, t0, path=FATL, fill=WHITE, spacing=4, t1=None, pop=False):
    if t < t0 or (t1 is not None and t > t1 + .3): return
    a = ramp(t, t0, t0 + .3, 'out') * (1 - (ramp(t, t1, t1 + .3) if t1 is not None else 0))
    sz = size * (lerp(1.18, 1, ease((t - t0) / .25, 'out')) if pop else 1)
    while sz > 20 and font(path, sz).getlength(s) + spacing * len(s) > 860: sz -= 2
    halo_text(can, s, (xy[0], xy[1] - (0 if pop else 16 * (1 - a))), sz, fill, path, spacing=spacing, alpha=a)

# ---------------- fondos ----------------
def bg_street(zoom=1.0, fx=.5, fy=.5, dark=0.0, blur=0):
    key = ('bg', round(zoom, 3), round(fx, 3), round(fy, 3), round(dark, 2), blur)
    if key in D['img']: return D['img'][key].copy()
    b = img('bg_street'); s = max(W / b.width, H / b.height) * zoom
    bw, bh = b.width * s, b.height * s; x0 = (bw - W) * fx; y0 = (bh - H) * fy
    im = b.resize((int(bw), int(bh)), Image.BILINEAR).crop((int(x0), int(y0), int(x0) + W, int(y0) + H))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark: im = ImageEnhance.Brightness(im).enhance(1 - dark)
    if len(D['img']) > 400: D['img'] = {k: v for k, v in D['img'].items() if not (isinstance(k, tuple) and k[0] == 'bg')}
    D['img'][key] = im; return im.copy()

MAP = dict(lon0=-2.0, lon1=36.0, lat0=60.0, lat1=42.0)
def map_prep():
    tif = os.path.join(ROOT, 'Recursos', 'naturalearth', 'NE1_HR_LC_SR_W_DR', 'NE1_HR_LC_SR_W_DR.tif')
    Image.MAX_IMAGE_PIXELS = None; big = Image.open(tif); s = big.width / 360
    box = (int((MAP['lon0'] + 180) * s), int((90 - MAP['lat0']) * s), int((MAP['lon1'] + 180) * s), int((90 - MAP['lat1']) * s))
    im = big.crop(box).convert('RGB'); im = im.resize((int(im.width * .63 * 2), im.height * 2), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    water = (a[..., 2] > a[..., 1] + 6) & (a[..., 2] > a[..., 0] + 15)
    g = a.mean(-1, keepdims=True); a = g + (a - g) * .55                      # desaturado: invierno 1944
    a[water] = a[water] * .55 + np.array((20, 38, 58)) * .45
    a[~water] = a[~water] * .8 + np.array((70, 72, 62)) * .2
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 60, 2)).save(os.path.join(PREP, 'map.png'))
def mxy(lon, lat):
    m = img('map'); return ((lon - MAP['lon0']) / (MAP['lon1'] - MAP['lon0']) * m.width, (MAP['lat0'] - lat) / (MAP['lat0'] - MAP['lat1']) * m.height)
class MapCam:
    def __init__(self, lon, lat, z): self.c = mxy(lon, lat); self.z = z
    def P(self, lon, lat): x, y = mxy(lon, lat); return (W / 2 + (x - self.c[0]) * self.z, H / 2 + (y - self.c[1]) * self.z)
    def render(self):
        m = img('map'); w, h = W / self.z, H / self.z; x0, y0 = self.c[0] - w / 2, self.c[1] - h / 2
        return m.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BILINEAR).convert('RGBA')

# ---------------- efectos ----------------
def flash(can, x, y, r, k=1.0, ang=0):
    if k <= 0: return
    lay = Image.new('RGBA', (int(r * 4), int(r * 4))); d = ImageDraw.Draw(lay); c = r * 2
    for i, (rr, col, a) in enumerate([(1.9, ORANGE, 70), (1.2, ORANGE, 150), (.75, (255, 220, 120), 230), (.4, WHITE, 255)]):
        d.ellipse((c - r * rr, c - r * rr * .8, c + r * rr, c + r * rr * .8), fill=col + (int(a * k),))
    for j in range(7):   # estrella del fogonazo
        aa = ang + (j - 3) * .32 + hsh(j, int(k * 9)) * .2; L = r * (1.2 + 1.2 * hsh(j, 3))
        d.polygon([(c, c), (c + math.cos(aa - .07) * L * .4, c + math.sin(aa - .07) * L * .4), (c + math.cos(aa) * L, c + math.sin(aa) * L), (c + math.cos(aa + .07) * L * .4, c + math.sin(aa + .07) * L * .4)], fill=(255, 235, 160, int(240 * k)))
    lay = lay.filter(ImageFilter.GaussianBlur(2)); can.alpha_composite(lay, (int(x - c), int(y - c)))
def tracer(can, a, b, u, col=(255, 210, 110), w=7):
    """Bala trazadora: segmento que avanza de a a b con u in [0,1]."""
    if not 0 <= u <= 1: return
    p = (lerp(a[0], b[0], u), lerp(a[1], b[1], u)); q = (lerp(a[0], b[0], max(0, u - .18)), lerp(a[1], b[1], max(0, u - .18)))
    lay = Image.new('RGBA', can.size); d = ImageDraw.Draw(lay)
    d.line((q, p), fill=col + (110,), width=w * 3); lay = lay.filter(ImageFilter.GaussianBlur(6)); d = ImageDraw.Draw(lay)
    d.line((q, p), fill=(255, 250, 220, 255), width=w); can.alpha_composite(lay)
def sparks(can, x, y, t, seed, n=10, spread=1.0, ang=-1.2):
    d = ImageDraw.Draw(can)
    for i in range(n):
        u = (t * 3 + hsh(i, seed)) % 1; a = ang + (hsh(i, seed + 1) - .5) * 2.2 * spread; L = 30 + 140 * u
        x1, y1 = x + math.cos(a) * L, y + math.sin(a) * L + 90 * u * u
        d.line((x + math.cos(a) * L * .6, y + math.sin(a) * L * .6 + 50 * u * u, x1, y1), fill=(255, int(230 - 120 * u), 80), width=4)
def wall(can, x0, x1, ytop, t=0):
    """Muro de escombros en primer plano (oclusor)."""
    d = ImageDraw.Draw(can); pts = [(x0, H)]
    for i in range(9): pts.append((lerp(x0, x1, i / 8), ytop + (hsh(i, 5) - .5) * 60 + (40 if i in (0, 8) else 0)))
    pts.append((x1, H)); d.polygon(pts, fill=(112, 92, 78), outline=(10, 8, 8))
    d.line(pts[1:-1], fill=(10, 8, 8), width=9)
    for r in range(12):
        y = ytop + 70 + r * 62
        if y > H: break
        d.line((x0, y, x1, y), fill=(78, 62, 52), width=5)
        for c in range(8):
            xx = x0 + (c + (.5 if r % 2 else 0)) * (x1 - x0) / 7
            d.line((xx, y, xx, y + 62), fill=(78, 62, 52), width=5)
def arrow(can, pts, k, col=RED, w=26):
    if k <= 0: return
    n = max(2, int(len(pts) * k)); P = pts[:n]
    lay = Image.new('RGBA', can.size); d = ImageDraw.Draw(lay)
    d.line(P, fill=(0, 0, 0, 120), width=w + 12, joint='curve'); d.line(P, fill=col + (255,), width=w, joint='curve')
    (ax, ay), (bx, by) = P[-2], P[-1]; a = math.atan2(by - ay, bx - ax); L = w * 2.2
    tip = (bx + math.cos(a) * L * .6, by + math.sin(a) * L * .6)
    d.polygon([tip, (bx + math.cos(a + 2.3) * L, by + math.sin(a + 2.3) * L), (bx + math.cos(a - 2.3) * L, by + math.sin(a - 2.3) * L)], fill=col + (255,), outline=(0, 0, 0, 160))
    can.alpha_composite(lay)
def bezier(p0, c, p1, n=40): return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]) for u in np.linspace(0, 1, n)]

# ---------------- subtítulos ----------------
def build_subs():
    groups = []
    for scene in TL['timeline']:
        sid = scene['id']; ws = [w.copy() for w in WORDS if w['scene'] == sid]; n = len(ws); a, b = SC[sid]; b = min(b, TOTAL)
        starts = [w['s'] for w in ws]; starts[0] = a
        @lru_cache(None)
        def solve(i):
            if i == n: return 0, []
            best = (1e9, [])
            for count in (1, 2, 3):
                j = i + count
                if j > n: continue
                tail = solve(j); end = starts[j] if j < n else b; dur = end - starts[i]
                pen = max(0, .65 - dur) ** 2 * 1000 + (dur - 1) ** 2 + (.03 if count == 2 else 0) + (.6 if count == 1 else 0)
                if pen + tail[0] < best[0]: best = (pen + tail[0], [(starts[i], end, ws[i:j])] + tail[1])
            return best
        blocks = solve(0)[1]; ss = [x[0] for x in blocks] + [b]
        for i in range(len(blocks) - 1, -1, -1): ss[i] = min(ss[i], ss[i + 1] - .65)
        ss[0] = max(a, ss[0])
        for i in range(1, len(blocks)): ss[i] = max(ss[i], ss[i - 1] + .65)
        for i, (_, _, g) in enumerate(blocks): groups.append((ss[i], ss[i + 1], ' '.join(w['w'] for w in g)))
    return groups
def subtitle(can, t):
    look = 0 if t >= math.ceil(TOTAL * FPS) / FPS - 4 / FPS else t
    for s, e, txt in D['subs']:
        if s <= look < e: break
    else: return
    size = 78
    while font(FSUB, size).getlength(txt) > 860: size -= 2
    halo_text(can, txt, (540, 1450), size, WHITE, FSUB, hw=6, halo=(0, 0, 0))

# ---------------- coreografía ----------------
# Puntos de los stickers (fracciones del PNG recortado) — se ajustan tras ver los assets.
SOLDIER_MUZZLE = (.996, .43); SOLDIER_EYE = (.33, .20); SOLDIER_MIRROR = (.87, .25)
RIFLE_MUZZLE = (.998, .48); RIFLE_BEND = (.87, .29); RIFLE_MIRROR = (.85, .05)
TANK_GUN = (.997, .26); TANK_HATCH = (.45, .03)
HOOK_SHOTS = [0.0, .32, .64, .96, 1.28, 1.6, 1.92]

def hook(can, t, t0, loop=False):
    """Escena gancho: soldado tras el muro, cañón curvo dispara sobre él hacia la calle (clímax en el cuadro 0)."""
    u = t - t0; z = 1.0 + .03 * u + (.18 * ramp(u, 1.25, 1.6, 'out') if not loop else 0)
    base = bg_street(1.12, .62, .55)
    base = base.convert('RGBA')
    # enemigos lejos en la calle (abajo-derecha), se tiran al suelo
    for j, (ex, ey) in enumerate([(900, 1330)]):
        sticker(base, 'soviet_inf', ex, ey, 230, flip=False, alpha=1)
    box = sticker(base, 'soldier_krumm', 470, 1210, 660)
    wall(base, -40, 640, 1060)
    mz = pt(box, *SOLDIER_MUZZLE, 'soldier_krumm'); tgt = (900, 1220)
    for k, s in enumerate(HOOK_SHOTS):
        v = u - s
        if 0 <= v < .22: tracer(base, mz, (tgt[0] + 40 * hsh(k, 2), tgt[1] + 30 * hsh(k, 3)), v / .22)
        if -0.0 <= v < .12: flash(base, mz[0] + 20, mz[1] + 10, 95 * (1 - v / .12 * .5), 1 - v / .12 * .3, ang=.45)
        if .18 <= v < .5: sparks(base, tgt[0], tgt[1] + 40, v, k, n=7, ang=-1.8)
    if z > 1.001:
        fx, fy = mz[0] - 60, mz[1]; w, h = W / z, H / z; x0 = min(max(0, fx - w * .55), W - w); y0 = min(max(0, fy - h * .45), H - h)
        base = base.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BILINEAR)
    can.alpha_composite(base)
    if not loop: label(can, 'AROUND CORNERS', (540, 330), 98, t, t0 - .3, spacing=4)

def rifle_view(t, z, fx, fy, heat=0.0, cracks=0.0, glow_pulse=0.0):
    """Primer plano del fusil sobre la calle desenfocada. Devuelve (canvas, caja)."""
    can = bg_street(1.25, .5, .5, dark=.45, blur=10).convert('RGBA')
    h = 560 * z; im = scaled('rifle', h); bx, by = pt((0, 0, h / img('rifle').height), fx, fy, 'rifle')
    x0 = int(540 - bx); y0 = int(860 - by); box = (x0, y0, h / img('rifle').height)
    can.paste(im, (x0, y0), im)
    bend = pt(box, *RIFLE_BEND, 'rifle')
    if heat > 0:
        lay = Image.new('RGBA', can.size); d = ImageDraw.Draw(lay); r = 130 * z / 2.2
        d.ellipse((bend[0] - r, bend[1] - r, bend[0] + r, bend[1] + r), fill=(255, 70, 20, int(170 * heat * (.75 + .25 * glow_pulse))))
        lay = lay.filter(ImageFilter.GaussianBlur(r * .45)); can.alpha_composite(lay)
    if cracks > 0:
        d = ImageDraw.Draw(can)
        for i in range(int(6 * cracks) + 1):
            a = hsh(i, 7) * 6.28; L = (40 + 70 * hsh(i, 8)) * z / 2.2 * min(1, cracks * 2)
            p = bend; pts = [p]
            for s in range(4): p = (p[0] + math.cos(a + (hsh(i, s) - .5)) * L / 4, p[1] + math.sin(a + (hsh(i, s) - .5)) * L / 4); pts.append(p)
            d.line(pts, fill=(15, 10, 8), width=max(3, int(5 * z / 2.2)))
    return can, box

def frame(t, preview=False):
    can = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    s = lambda sid: SC[sid][0]
    if t < s('02'):                                   # 01 GANCHO
        hook(can, t, 0)
    elif t < s('03'):                                 # 02 cada bala lo destruye: primer plano de la curva
        u = t - s('02'); z = lerp(1.6, 2.3, ramp(u, 0, SC['02'][1] - s('02'), 'out'))
        shots = [s('02') + .15 + .45 * i for i in range(8)]; pulse = max([0] + [max(0, 1 - (t - x) / .3) for x in shots if t >= x])
        c, box = rifle_view(t, z, *RIFLE_BEND, heat=ramp(t, wt('02', 'every'), wt('02', 'destroying'), 'lin'), cracks=ramp(t, wt('02', 'destroying'), SC['02'][1]), glow_pulse=pulse)
        bend = pt(box, *RIFLE_BEND, 'rifle'); mz = pt(box, *RIFLE_MUZZLE, 'rifle')
        if pulse > .5: sparks(c, bend[0], bend[1] + 20, t, int(t * 3), n=12, ang=1.2)
        if pulse > .6: flash(c, mz[0], mz[1], 120, pulse, ang=1.1)
        can.alpha_composite(c)
    elif t < s('04') or (s('09') <= t < s('10')):     # 03 / 09 MAPA REAL
        late = t >= s('09'); a0 = s('09') if late else s('03'); a1 = SC['09'][1] if late else SC['03'][1]
        if not late: z = lerp(1.0, 1.45, ramp(t, a0, a1)); lon, lat = lerp(20, 15.5, ramp(t, a0, a1)), lerp(51.5, 52.3, ramp(t, a0, a1))
        else: z = lerp(1.45, 3.2, ramp(t, a0, a1)); lon, lat = lerp(15.5, 13.4, ramp(t, a0, a1 - .5)), 52.5
        cam = MapCam(lon, lat, z); can.alpha_composite(cam.render())
        path = [cam.P(*p) for p in bezier((31, 53.5), (24, 52), (19.5, 52.3), 30)] + [cam.P(*p) for p in bezier((19.5, 52.3), (16.5, 52.4), (14.2, 52.5), 20)[1:]]
        k = (lerp(.15, .72, ramp(t, wt('03', 'Soviet'), wt('03', 'west') + .3)) if not late else lerp(.72, 1, ramp(t, a0, a0 + 1.2)))
        if t >= (wt('03', 'Soviet') if not late else a0): arrow(can, path, k)
        bx, by = cam.P(13.4, 52.52); d = ImageDraw.Draw(can); r = 13 * max(1, z)
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=WHITE, outline=(0, 0, 0), width=4)
        label(can, 'BERLIN', (bx, by - 60), 46, t, (wt('03', 'streets') if not late else a0), spacing=5)
        if not late:
            label(can, 'GERMANY  1945', (540, 330), 70, t, wt('03', 'Germany'), spacing=6)
            sx, sy = cam.P(22.0, 53.4); label(can, 'SOVIET ARMY', (sx, sy), 44, t, wt('03', 'Soviet'), fill=(255, 210, 200), spacing=4)
        else:
            label(can, 'WAR ENDS', (540, 330), 100, t, a0 + .1, spacing=8, pop=True)
            label(can, 'LIMITED NUMBERS', (540, 450), 50, t, wt('09', 'limited'), spacing=4)
    elif t < s('05'):                                 # 04 tanque y soldados demasiado cerca
        u = t - s('04'); c = bg_street(1.05, .4, .6).convert('RGBA')
        tb = sticker(c, 'tank', 470, 1290, 470)
        hx, hy = pt(tb, *TANK_HATCH, 'tank')
        if t >= wt('04', 'crews'): sticker(c, 'crewman', hx, hy + 40, 240 * ramp(t, wt('04', 'crews'), wt('04', 'crews') + .3, 'back') + 1, shadow=False)
        ex = lerp(1250, 900, ramp(t, wt('04', 'Enemy'), wt('04', 'close') + .2, 'out'))
        sticker(c, 'soviet_inf', ex, 1330, 330)
        gx, gy = pt(tb, *TANK_GUN, 'tank')
        if t >= wt('04', 'guns'):
            d = ImageDraw.Draw(c); k = ramp(t, wt('04', 'guns'), wt('04', 'guns') + .4)
            for i in range(14):
                if i / 14 < k and i % 2 == 0: d.line((gx + i * 40, gy, gx + i * 40 + 30, gy), fill=RED, width=10)
            label(c, 'TOO CLOSE', (870, 900), 64, t, wt('04', 'close'), fill=(255, 225, 215), spacing=5)
        can.alpha_composite(c)
    elif t < s('06'):                                 # 05 la Krummlauf: 30° y 90°
        z = lerp(.5, .56, ramp(t, s('05'), SC['05'][1]))
        c, box = rifle_view(t, z, .5, .4)
        if t >= wt('05', 'curved'):
            bend = pt(box, *RIFLE_BEND, 'rifle'); d = ImageDraw.Draw(c); k = ramp(t, wt('05', 'curved'), wt('05', 'curved') + .5)
            d.arc((bend[0] - 110, bend[1] - 110, bend[0] + 110, bend[1] + 110), 0, 30 * k, fill=GOLD, width=9)
            d.line((bend[0], bend[1], bend[0] + 170, bend[1]), fill=GOLD, width=6)
        label(c, 'KRUMMLAUF', (540, 330), 104, t, wt('05', 'Krummlauf'), spacing=6, pop=True)
        label(c, '“curved barrel”', (540, 430), 46, t, wt('05', 'Krummlauf') + .15, path=FATI, spacing=1, fill=(235, 230, 220))
        label(c, '30°  INFANTRY', (540, 1080), 62, t, wt('05', 'Thirty'), fill=GOLD, spacing=4)
        if t >= wt('05', 'Ninety'):
            sticker(c, 'tank', 290, 1330, 150 * ramp(t, wt('05', 'Ninety'), wt('05', 'Ninety') + .3, 'back') + 1)
            label(c, '90°  TANKS', (730, 1250), 62, t, wt('05', 'Ninety'), fill=GOLD, spacing=4)
        can.alpha_composite(c)
    elif t < s('07'):                                 # 06 visor de espejo
        u = t - s('06'); c = bg_street(1.12, .62, .55).convert('RGBA')
        sticker(c, 'soviet_inf', 900, 1330, 230)
        box = sticker(c, 'soldier_krumm', 470, 1210, 660); wall(c, -40, 640, 1060)
        eye = pt(box, *SOLDIER_EYE, 'soldier_krumm'); mir = pt(box, *SOLDIER_MIRROR, 'soldier_krumm'); mz = pt(box, *SOLDIER_MUZZLE, 'soldier_krumm')
        k = ramp(t, wt('06', 'mirror'), wt('06', 'aim') + .2, 'lin'); d = ImageDraw.Draw(c)
        segs = [(eye, mir), (mir, mz), (mz, (880, 1200))]; tot = 3 * k
        for i, (a, b) in enumerate(segs):
            f = min(1, max(0, tot - i))
            if f <= 0: break
            n = int(16 * f)
            for j in range(n):
                p = (lerp(a[0], b[0], j / 16), lerp(a[1], b[1], j / 16)); d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=(120, 230, 255))
        if t >= wt('06', 'head'):
            hx, hy = eye[0], eye[1] - 60; d.line((hx - 40, hy - 40, hx + 40, hy + 40), fill=(90, 230, 120), width=0)
            label(c, 'HEAD STAYS DOWN', (540, 330), 70, t, wt('06', 'head'), spacing=5)
        can.alpha_composite(c)
    elif t < s('08'):                                 # 07 la bala no quiere girar: raspa la curva
        z = 2.6; c, box = rifle_view(t, z, *RIFLE_BEND, heat=.35)
        bend = pt(box, *RIFLE_BEND, 'rifle'); mz = pt(box, *RIFLE_MUZZLE, 'rifle')
        path = [(bend[0] - 700, bend[1] - 20)] + bezier((bend[0] - 250, bend[1] - 8), (bend[0] + 60, bend[1]), (mz[0], mz[1]), 30)
        period = 1.1; v = ((t - s('07')) % period) / period
        i = int(v * (len(path) - 1)); p = path[i]; d = ImageDraw.Draw(c)
        d.ellipse((p[0] - 22, p[1] - 12, p[0] + 22, p[1] + 12), fill=(215, 170, 70), outline=(20, 15, 5), width=4)
        if abs(p[0] - bend[0]) < 260: sparks(c, p[0], p[1] - 10, t, int(t * 5), n=12, ang=-1.6)
        label(c, 'SCRAPE', (540, 330), 96, t, wt('07', 'scrapes'), spacing=8, pop=True)
        can.alpha_composite(c)
    elif t < s('09'):                                 # 08 ~300 disparos
        a0, a1 = s('08'), SC['08'][1]; z = lerp(1.5, 2.1, ramp(t, a0, a1))
        k = ramp(t, wt('08', 'lasted') - .2, wt('08', 'rounds') + .2, 'lin')
        c, box = rifle_view(t, z, *RIFLE_BEND, heat=.3 + .7 * k, cracks=k, glow_pulse=(t * 8) % 1)
        n = int(300 * k); halo_text(c, f'{n}', (540, 360), int(200 * (1 + .15 * max(0, 1 - (t - wt('08', 'rounds')) * 4)) if t >= wt('08', 'rounds') else 200), GOLD, FATL)
        label(c, 'SHOTS', (540, 500), 54, t, a0 + .1, spacing=8)
        if k >= 1: label(c, 'WORN OUT', (540, 1150), 80, t, wt('08', 'rounds') + .3, fill=(255, 120, 100), spacing=6, pop=True)
        can.alpha_composite(c)
    else:                                             # 10 pregunta: vuelve el gancho (bucle)
        hook(can, t, s('10'), loop=True)
    subtitle(can, t)
    return post(can, t)

SHAKES = [(x, 16, .25) for x in HOOK_SHOTS[:4]]
def post(can, t):
    dx = dy = 0
    for at, amp, dur in SHAKES + D.get('shk', []):
        u = t - at
        if 0 <= u < dur: aa = amp * math.exp(-u * 13); dx += aa * math.sin(u * 101 + 1); dy += aa * math.cos(u * 83)
    if abs(dx) + abs(dy) > .3:
        big = can.resize((W + 100, H + 150), Image.BILINEAR); x = round(50 + dx); y = round(75 + dy); can = big.crop((x, y, x + W, y + H))
    return can

def prep():
    os.makedirs(PREP, exist_ok=True)
    if not os.path.exists(os.path.join(PREP, 'map.png')): map_prep()
    for n in ('rifle', 'soldier_krumm', 'soviet_inf', 'tank', 'crewman'): cut(n).save(os.path.join(PREP, n + '.png'))
    Image.open(os.path.join(CAP, 'bg_street.png')).convert('RGB').save(os.path.join(PREP, 'bg_street.png'))
    print('PREP COMPLETE', flush=True)

def init():
    D['subs'] = build_subs()
    S = [s for s in TL['timeline']]
    D['shk'] = [(SC['10'][0] + x, 14, .25) for x in HOOK_SHOTS[:3]]
if os.path.exists(os.path.join(PREP, 'bg_street.png')): init()

# ---------------- render ----------------
def seg(args):
    index, f0, f1, out = args
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-threads', '2', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-threads', '2', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).convert('RGB').tobytes())
        if (f - f0) % 60 == 0: print(f'seg{index}: {f - f0}/{f1 - f0}', flush=True)
    p.stdin.close()
    if p.wait(): raise RuntimeError('ffmpeg segment failed')
def run(cmd): return subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf8')
def loud_measure(path):
    r = run([FF, '-hide_banner', '-i', str(path), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'])
    return json.loads(re.findall(r'\{\s*"input_i"[\s\S]*?\}', r.stderr)[-1])
def render():
    subprocess.run([sys.executable, os.path.join(HERE, 'sound.py')], check=True, cwd=HERE)
    tmp = Path(HERE, '_encode'); tmp.mkdir(exist_ok=True)
    nf = math.ceil(TOTAL * FPS); nw = 4; step = math.ceil(nf / nw)
    jobs = [(i, i * step, min(nf, (i + 1) * step), str(tmp / f's{i:02d}.mp4')) for i in range(nw)]
    workers = []; logs = []
    for i, f0, f1, path in jobs:
        log = open(tmp / f'segment_{i}.log', 'w', encoding='utf8'); logs.append(log)
        workers.append(subprocess.Popen([sys.executable, '-u', __file__, '--segment', str(i), str(f0), str(f1), path], cwd=HERE, stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)))
    codes = [p.wait() for p in workers]
    for log in logs: log.close()
    if any(codes): raise RuntimeError(f'Segment failures: {codes}')
    lst = tmp / 'list.txt'; lst.write_text(''.join("file '" + j[3].replace('\\', '/') + "'\n" for j in jobs), encoding='utf8')
    video = tmp / 'video.mp4'; run([FF, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(video)])
    mix = tmp / 'mix.wav'; run([FF, '-y', '-loglevel', 'error', '-i', os.path.join(HERE, 'voz.wav'), '-i', os.path.join(HERE, 'sfx.wav'), '-filter_complex', '[0:a]apad[v];[v][1:a]amix=inputs=2:normalize=0:duration=longest[a]', '-map', '[a]', '-t', str(nf / FPS), '-c:a', 'pcm_s24le', str(mix)])
    dest = Path(ROOT, 'Render', 'Shorts'); dest.mkdir(parents=True, exist_ok=True); out = dest / 'S13_Krummlauf.mp4'; up = dest / 'S13_upload.mp4'
    run([FF, '-y', '-loglevel', 'error', '-i', str(video), '-i', str(mix), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(nf / FPS), str(out)])
    passlog = str(tmp / 'upload_pass'); common = [FF, '-y', '-loglevel', 'error', '-i', str(out), '-c:v', 'libx264', '-preset', 'slow', '-b:v', '1350k', '-pix_fmt', 'yuv420p', '-passlogfile', passlog]
    run(common + ['-pass', '1', '-an', '-f', 'null', 'NUL']); run(common + ['-pass', '2', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-movflags', '+faststart', str(up)])
    json.dump({'approved_total_s': TOTAL, 'frame_count': nf, 'master': {'path': str(out)}, 'upload': {'path': str(up)}}, open(Path(HERE, 'render_report.json'), 'w'), indent=2)
    from master_audio import master
    master()

if __name__ == '__main__':
    if '--segment' in sys.argv: seg((int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]))
    elif '--prep' in sys.argv: prep()
    elif '--frame' in sys.argv:
        for t in map(float, sys.argv[sys.argv.index('--frame') + 1:]): frame(t, True).convert('RGB').save(os.path.join(PREP, f'test_{t:05.2f}.jpg'), quality=90)
    else: render()

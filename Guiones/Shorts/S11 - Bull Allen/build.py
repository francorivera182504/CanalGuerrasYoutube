"""S11 Bull Allen — estilo nuevo: mapa real a pantalla completa (sin plantilla).
Cámara 3D sobre relieve real (Natural Earth + Terrarium/Mapzen), figuras de pie sobre el mapa,
subtítulo blanco simple, rótulos tipo atlas. python build.py --prep | --frame t... | (render)."""
import json, math, os, subprocess, sys, re
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
PREP = os.path.join(HERE, '_prep'); CAP = os.path.join(HERE, 'assets')
FF = r'C:\Users\Franco\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
FSUB = r'C:\Windows\Fonts\seguibl.ttf'; FATL = r'C:\Windows\Fonts\georgiab.ttf'; FATI = r'C:\Windows\Fonts\georgiaz.ttf'
W, H, FPS = 1080, 1920, 30; F = 1700.0
WHITE = (255, 255, 255); RED = (230, 60, 45); GOLD = (255, 205, 90); GREEN = (120, 230, 140); BLUE = (90, 170, 255)
TL = json.load(open(os.path.join(HERE, 'timeline.json'), encoding='utf8')); WORDS = TL['words']; TOTAL = TL['total']
SC = {s['id']: (s['start'], s['start'] + s['dur']) for s in TL['timeline']}
def wt(scene, word): return next(w['s'] for w in WORDS if w['scene'] == scene and w['w'].lower().strip('.,?!') == word.lower())
D = {}

def ease(x, kind='inout'):
    x = min(1.0, max(0.0, x))
    if kind == 'back': c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
    if kind == 'out': return 1 - (1 - x) ** 3
    if kind == 'lin': return x
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, k): return a + (b - a) * k
def ramp(t, t0, t1, kind='inout'): return ease((t - t0) / max(1e-6, t1 - t0), kind)
def hsh(i, k=0): return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0

# ---------------- mundo (metros, origen = cumbre de Mount Tambu, x este, y sur) ----------------
LON0, LAT0 = 147.02418, -7.161271; KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
def geo(lon, lat): return ((lon - LON0) * KX, -(lat - LAT0) * KY)
def lonlat(x, y): return (LON0 + x / KX, LAT0 - y / KY)
AID = (1550.0, -40.0); J = (800.0, 30.0)
NESTS = [(-60.0, -95.0), (75.0, 35.0), (-25.0, 115.0)]
WOUND = [(380 + 300 * hsh(i, 1), -420 + 840 * ((i * 5) % 12 + hsh(i, 2)) / 12) for i in range(12)]
WOUND.sort(key=lambda p: math.hypot(p[0] - J[0], p[1] - J[1]))
US = [(470.0, -190.0), (560.0, 170.0), (650.0, -10.0)]

def bez(p0, c, p1, n=28): return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]) for u in np.linspace(0, 1, n)]
@lru_cache(None)
def route(i):
    """Camino AID -> herido i, siguiendo la ladera (puntos cada ~10 m)."""
    w = WOUND[i]; pts = bez(AID, (1180, -110), J, 40)[:-1] + bez(J, ((J[0] + w[0]) / 2 + 40 * (hsh(i, 3) - .5), (J[1] + w[1]) / 2 + 60 * (hsh(i, 4) - .5)), w, 24)
    out = [pts[0]]
    for p in pts[1:]:
        a = out[-1]; L = math.hypot(p[0] - a[0], p[1] - a[1]); n = max(1, int(L / 10))
        out += [(lerp(a[0], p[0], k / n), lerp(a[1], p[1], k / n)) for k in range(1, n + 1)]
    return tuple(out)
def along(pts, u):
    u = min(1, max(0, u)); n = u * (len(pts) - 1); i = min(len(pts) - 2, int(n)); f = n - i
    return (lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f))

# ---------------- cámara ----------------
class Cam:
    def __init__(s, x, y, mpp, tilt=0, head=0, sy=960, S=1.0):
        s.S = S; x, y, mpp = x * S, y * S, mpp * S
        s.x, s.y, s.mpp, s.tilt, s.head, s.sy = x, y, mpp, tilt, head, sy
        ph, h = math.radians(tilt), math.radians(head); fh = np.array((math.sin(h), -math.cos(h)))
        s.f = np.array((fh[0] * math.sin(ph), fh[1] * math.sin(ph), -math.cos(ph)))
        s.r = np.array((-fh[1], fh[0], 0.0)); s.up = np.array((fh[0] * math.cos(ph), fh[1] * math.cos(ph), math.sin(ph)))
        s.D = mpp * F; s.C = np.array((x, y, 0.0)) - s.D * s.f
    def ray(s, u, v):
        d = s.f + (u - W / 2) / F * s.r - (v - s.sy) / F * s.up; t = -s.C[2] / d[2]; return s.C + t * d
    def P(s, p):
        q = np.array((p[0] * s.S, p[1] * s.S, 0.0)) - s.C; z = q @ s.f
        if z <= 1: return None
        return (W / 2 + F * (q @ s.r) / z, s.sy - F * (q @ s.up) / z, s.D / z)
KEYS = {}
def blend_cam(a, b, k, logz=True):
    S = lerp(a.S, b.S, k); m = math.exp(lerp(math.log(a.mpp), math.log(b.mpp), k)) / S
    return Cam(lerp(a.x, b.x, k) / S, lerp(a.y, b.y, k) / S, m, lerp(a.tilt, b.tilt, k), lerp(a.head, b.head, k), lerp(a.sy, b.sy, k), S)

# ---------------- escenarios (stages) ----------------
STAGES = ('png', 'local', 'tambu'); FADE = {'png': (1e9, 1e9), 'local': (80, 130), 'tambu': (22, 34)}
def stage_affine(g):
    """metros -> px del stage (lineal; mercator linealizado en el centro)."""
    x0, _ = geo(g['lon0'], 0); x1, _ = geo(g['lon1'], 0); ax = g['w'] / (x1 - x0); bx = -x0 * ax
    if g.get('merc'):
        M = lambda la: math.log(math.tan(math.pi / 4 + math.radians(la) / 2)); lc = (g['lat0'] + g['lat1']) / 2
        dpy = g['h'] / (M(g['lat0']) - M(g['lat1'])) * (M(lc + 1e-4) - M(lc - 1e-4)) / 2e-4  # px por grado
        ay = dpy / KY; yc = (M(g['lat0']) - M(lc)) / (M(g['lat0']) - M(g['lat1'])) * g['h']; by = yc - ay * geo(0, lc)[1] * 1
        by = yc - ay * (-(lc - LAT0) * KY)
    else:
        _, y0 = geo(0, g['lat0']); _, y1 = geo(0, g['lat1']); ay = g['h'] / (y1 - y0); by = -y0 * ay
    return ax, bx, ay, by
def solve_persp(src, dst):
    A = []; B = []
    for (x, y), (X, Y) in zip(src, dst):
        A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]; B += [X, Y]
    return np.linalg.solve(np.array(A, float), np.array(B, float))

def init():
    if D: return
    D.update(icons={}, texts={}, fonts={})
    geoj = json.load(open(os.path.join(PREP, 'geo.json')))
    D['stages'] = {}
    for n in STAGES:
        im = Image.open(os.path.join(PREP, f'stage_{n}.png')).convert('RGBA'); mips = [im]
        while mips[-1].width > 700: m = mips[-1]; mips.append(m.resize((m.width // 2, m.height // 2), Image.LANCZOS))
        D['stages'][n] = dict(mips=mips, aff=stage_affine(geoj[n]), w=im.width, h=im.height, fe=90 if n != 'png' else 0)
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / (W * .62), (yy - H * .48) / (H * .6))
    D['vig'] = Image.fromarray((np.clip(1 - .55 * np.clip(r - .55, 0, 1) ** 1.6, 0, 1) * 255).astype(np.uint8))
    D['subs'] = build_subs()

def render_map(cam):
    corners = [(0, 0), (W, 0), (W, H), (0, H)]; wc = [cam.ray(u, v) for u, v in corners]
    sc = cam.ray(W / 2, H * .62); dc = np.linalg.norm(sc - cam.C); mpp_c = dc / F
    layers = []
    for n in reversed(STAGES):
        st = D['stages'][n]; ax, bx, ay, by = st['aff']
        pts = [(ax * p[0] + bx, ay * p[1] + by) for p in wc]
        lo, hi = FADE[n]; a = 1 - ramp(mpp_c, lo, hi, 'lin')
        if a <= 0: continue
        cx, cy = ax * sc[0] + bx, ay * sc[1] + by
        if not (-st['w'] < cx < 2 * st['w'] and -st['h'] < cy < 2 * st['h']) and n != 'png': continue
        layers.append((n, pts, a, mpp_c * ax))
        fe = st['fe'] + 4
        if a >= 1 and all(fe < x < st['w'] - fe and fe < y < st['h'] - fe for x, y in pts): break
    can = Image.new('RGB', (W, H), (18, 52, 80))
    for n, pts, a, s in reversed(layers):
        st = D['stages'][n]; lvl = int(min(len(st['mips']) - 1, max(0, math.floor(math.log2(max(1e-6, s * 1.15))))))
        k = 2 ** lvl; c = solve_persp(corners, [(x / k, y / k) for x, y in pts])
        im = st['mips'][lvl].transform((W, H), Image.PERSPECTIVE, tuple(c), Image.BILINEAR)
        if a < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
        can.paste(im, (0, 0), im)
    if cam.tilt > 1:  # bruma de distancia
        rows = np.array([np.linalg.norm(cam.ray(W / 2, v) - cam.C) for v in range(0, H, 16)]) / cam.D
        al = np.clip((rows - 1.5) / 3.5, 0, .82); m = Image.fromarray((al * 255).astype(np.uint8)[:, None]).resize((W, H), Image.BILINEAR)
        can.paste((168, 192, 200), (0, 0), m)
    return can

# ---------------- dibujo ----------------
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
def icon(name, size, flip=False):
    key = (name, int(size), flip)
    if key not in D['icons']:
        im = Image.open(os.path.join(PREP, 'fig_' + name + '.png'))
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = size / im.height; im = im.resize((max(1, int(im.width * s)), max(1, int(size))), Image.LANCZOS)
        if len(D['icons']) > 200: D['icons'].clear()
        D['icons'][key] = im
    return D['icons'][key]
def figure(can, cam, name, p, size, flip=False, t=0, walk=False, alpha=1.0, pop=None):
    q = cam.P(p)
    if not q: return
    x, y, s = q; sz = size * s
    if pop is not None: sz *= max(.02, ease(pop, 'back'))
    if sz < 6: return
    sz = round(sz / 2) * 2; im = icon(name, sz, flip)
    if walk: y -= abs(math.sin(t * 9)) * sz * .035; im = im.rotate(3 * math.sin(t * 9), Image.BICUBIC, expand=True)
    if alpha < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    sh = Image.new('L', (int(im.width * .9), int(im.width * .9 * max(.22, math.cos(math.radians(cam.tilt))) * .5)))
    ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, sh.height - 1), fill=int(120 * alpha)); sh = sh.filter(ImageFilter.GaussianBlur(max(2, sz / 40)))
    can.paste((10, 18, 8), (int(x - sh.width / 2 + sz * .06), int(y - sh.height / 2)), sh)
    can.paste(im, (int(x - im.width / 2), int(y - im.height + sz * .02)), im)

def halo_text(can, s, xy, size, fill=WHITE, path=FATL, anchor='mm', spacing=0, halo=(12, 20, 14), hw=5, alpha=1.0):
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
        D['texts'][key] = (lay, sh, pad, asc + desc)
    lay, sh, pad, th = D['texts'][key]
    x = xy[0] - lay.width / 2 if anchor[0] == 'm' else (xy[0] - pad if anchor[0] == 'l' else xy[0] - lay.width + pad)
    y = xy[1] - lay.height / 2
    if alpha < 1:
        lay = lay.copy(); lay.putalpha(lay.getchannel('A').point(lambda v: int(v * alpha))); sh = sh.point(lambda v: int(v * alpha))
    can.paste((0, 0, 0), (int(x) + 3, int(y) + 5), sh); can.paste(lay, (int(x), int(y)), lay)
def atlas(can, cam, s, p, size, t, t0, dy=0, path=FATL, fill=WHITE, spacing=6, t1=None):
    if t < t0 or (t1 and t > t1 + .3): return
    q = cam.P(p) if p is not None else (W / 2, 0, 1)
    if not q: return
    a = ramp(t, t0, t0 + .35, 'out') * (1 - (ramp(t, t1, t1 + .3) if t1 else 0))
    halo_text(can, s, (q[0], q[1] + dy - 18 * (1 - a)), size, fill, path, spacing=spacing, alpha=a)
def leader(can, cam, p, t, t0, lines, side=1, dy=-260, dx=230):
    """Rótulo con línea guía (anotación de mapa)."""
    q = cam.P(p)
    if not q or t < t0: return
    x, y, _ = q; k = ramp(t, t0, t0 + .35, 'out'); d = ImageDraw.Draw(can)
    ex, ey = x + side * dx * k, y + dy * k; d.line((x, y, ex, ey), fill=WHITE, width=4); d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=WHITE)
    d.line((ex, ey, ex + side * 30 * k, ey), fill=WHITE, width=4)
    yy = ey
    for s, size, path, col, t1 in lines:
        if t >= t1: halo_text(can, s, (ex + side * 44, yy), size, col, path, anchor=('l' if side > 0 else 'r') + 'm', alpha=ramp(t, t1, t1 + .3, 'out'))
        yy += size * 1.25

def marker(can, cam, p, kind, scale=1.0, pop=1.0, alpha=1.0):
    q = cam.P(p)
    if not q: return
    x, y, s = q; r = 17 * s * scale * ease(pop, 'back')
    if r < 2: return
    d = ImageDraw.Draw(can)
    if kind == 'wounded':
        d.ellipse((x - r - 3, y - r - 3, x + r + 3, y + r + 3), fill=(25, 10, 8)); d.ellipse((x - r, y - r, x + r, y + r), fill=(250, 250, 245))
        a, b = r * .62, r * .2; d.rectangle((x - a, y - b, x + a, y + b), fill=RED); d.rectangle((x - b, y - a, x + b, y + a), fill=RED)
    elif kind == 'saved':
        d.ellipse((x - r - 3, y - r - 3, x + r + 3, y + r + 3), fill=(10, 30, 15)); d.ellipse((x - r, y - r, x + r, y + r), fill=GREEN)
        d.line((x - r * .5, y, x - r * .1, y + r * .4, x + r * .55, y - r * .45), fill=(10, 40, 18), width=max(2, int(r * .28)))
    elif kind == 'dead':
        d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 70, 70), outline=(20, 20, 20), width=3)
        a = r * .55; d.line((x - a, y - a, x + a, y + a), fill=(15, 15, 15), width=max(2, int(r * .3))); d.line((x - a, y + a, x + a, y - a), fill=(15, 15, 15), width=max(2, int(r * .3)))
    elif kind == 'medic':
        d.ellipse((x - r - 3, y - r - 3, x + r + 3, y + r + 3), fill=BLUE); d.ellipse((x - r, y - r, x + r, y + r), fill=(250, 250, 245))
        a, b = r * .62, r * .2; d.rectangle((x - a, y - b, x + a, y + b), fill=RED); d.rectangle((x - b, y - a, x + b, y + a), fill=RED)
    elif kind == 'nest':  # nido de ametralladora: anillo de sacos
        r *= 1.3; d.ellipse((x - r, y - r * .7, x + r, y + r * .7), fill=(120, 25, 20), outline=(255, 120, 100), width=max(2, int(r * .18)))
        d.ellipse((x - r * .45, y - r * .3, x + r * .45, y + r * .3), fill=(30, 8, 6))
    elif kind == 'aid':
        r *= 1.5; d.rounded_rectangle((x - r, y - r * .8, x + r, y + r * .8), radius=int(r * .25), fill=(250, 250, 245), outline=(20, 20, 20), width=3)
        a, b = r * .5, r * .16; d.rectangle((x - a, y - b, x + a, y + b), fill=RED); d.rectangle((x - b, y - a * .9, x + b, y + a * .9), fill=RED)

def dotted(can, cam, pts, t, col=(255, 255, 255), r=5, alpha=1.0, frac=1.0, march=True, step=3):
    d = ImageDraw.Draw(can); n = int(len(pts) * frac); off = int(t * 6) % step if march else 0
    c = tuple(int(lerp(0, v, alpha)) for v in col) if alpha < 1 else col
    for i in range(off, n, step):
        q = cam.P(pts[i])
        if not q: continue
        rr = max(1.5, r * q[2])
        if alpha < 1:  # mezcla con el fondo
            px = can.getpixel((min(W - 1, max(0, int(q[0]))), min(H - 1, max(0, int(q[1])))))
            c = tuple(int(lerp(p, v, alpha)) for p, v in zip(px, col))
        d.ellipse((q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr), fill=c)

class Glow:
    def __init__(s): s.lay = Image.new('RGB', (W // 2, H // 2)); s.d = ImageDraw.Draw(s.lay); s.core = []
    def line(s, a, b, col, w):
        s.d.line((a[0] / 2, a[1] / 2, b[0] / 2, b[1] / 2), fill=col, width=max(2, int(w))); s.core.append(('l', a, b, w))
    def disc(s, p, r, col, core=True):
        s.d.ellipse((p[0] / 2 - r / 2, p[1] / 2 - r / 2, p[0] / 2 + r / 2, p[1] / 2 + r / 2), fill=col)
        if core: s.core.append(('d', p, r * .35, 0))
    def apply(s, can):
        g1 = s.lay.filter(ImageFilter.GaussianBlur(9)); g2 = s.lay.filter(ImageFilter.GaussianBlur(2.5))
        can = ImageChops.add(can, ImageChops.add(ImageChops.add(g1, g1), g2).resize((W, H), Image.BILINEAR)); d = ImageDraw.Draw(can)
        for k, a, b, w in s.core:
            if k == 'l': d.line((a[0], a[1], b[0], b[1]), fill=(255, 245, 210), width=max(2, int(w * .45)))
            else: d.ellipse((a[0] - b, a[1] - b, a[0] + b, a[1] + b), fill=(255, 250, 230))
        return can

def tracers(gl, cam, t, t0, t1, targets, rate=9, seed=0):
    """Ráfagas desde los nidos hacia la ladera."""
    if t < t0: return
    k0 = int((t - .45 - t0) * rate); k1 = int((t - t0) * rate)
    for k in range(max(0, k0), k1 + 1):
        ts = t0 + k / rate
        if ts > t1 or ts > t: continue
        u = (t - ts) / .45
        if not 0 <= u <= 1: continue
        n = NESTS[(k + seed) % 3]; tg = targets[int(hsh(k, seed + 5) * len(targets)) % len(targets)]
        tg = (tg[0] + 160 * (hsh(k, seed + 6) - .5), tg[1] + 160 * (hsh(k, seed + 7) - .5))
        a = (lerp(n[0], tg[0], u), lerp(n[1], tg[1], u)); b = (lerp(n[0], tg[0], max(0, u - .16)), lerp(n[1], tg[1], max(0, u - .16)))
        pa, pb = cam.P(a), cam.P(b)
        if pa and pb: gl.line(pb, pa, (255, 150, 40), 7 * pa[2] + 2)
def sweep(can, cam, t, t0, k):
    """Abanicos de ametralladora barriendo la ladera."""
    lay = Image.new('L', (W, H)); d = ImageDraw.Draw(lay); ed = []
    for j, n in enumerate(NESTS):
        base = math.radians(-8 + 30 * math.sin((t - t0) * 1.7 + j * 2.1)); half = math.radians(7); L = 1250
        pts = [n] + [(n[0] + L * math.cos(base + a), n[1] + L * math.sin(base + a)) for a in np.linspace(-half, half, 8)]
        pp = [cam.P(p) for p in pts]
        if all(pp): d.polygon([(p[0], p[1]) for p in pp], fill=int(95 * k)); ed.append(pp)
    can.paste((255, 40, 25), (0, 0), lay.filter(ImageFilter.GaussianBlur(3)))
    dd = ImageDraw.Draw(can)
    for pp in ed: dd.line((pp[0][0], pp[0][1], pp[1][0], pp[1][1]), fill=(255, 110, 90), width=3); dd.line((pp[0][0], pp[0][1], pp[-1][0], pp[-1][1]), fill=(255, 110, 90), width=3)
def burst(can, gl, cam, p, t, t0, size=70):
    u = t - t0
    if not 0 <= u < 1.4: return
    q = cam.P(p)
    if not q: return
    x, y, s = q
    if u < .2: gl.disc((x, y), size * s * (.5 + 1.5 * u), (255, 150, 40))
    lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
    for j in range(5):
        a = j * 1.3 + hsh(int(t0 * 10), j); rr = size * s * (.4 + .9 * ease(u / 1.2, 'out')) * (.7 + .4 * hsh(j, 9))
        cx, cy = x + math.cos(a) * rr * .5, y - rr * .35 - u * 40 * s + math.sin(a) * rr * .25
        al = int(170 * (1 - ease(u / 1.4, 'lin'))); d.ellipse((cx - rr, cy - rr * .8, cx + rr, cy + rr * .8), fill=(95, 88, 75, al))
    can.alpha_composite(lay) if can.mode == 'RGBA' else can.paste(lay, (0, 0), lay)

def medal(size):
    k = ('medal', size)
    if k in D['icons']: return D['icons'][k]
    S = 4; w, h = 360 * S, 620 * S; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    stripes = [((0, 40, 104), 3), (WHITE, 1), ((0, 40, 104), 3), (WHITE, 1), ((190, 20, 40), 4), (WHITE, 1), ((0, 40, 104), 3), (WHITE, 1), ((0, 40, 104), 3)]
    tot = sum(s for _, s in stripes); x = 40 * S; rw = w - 80 * S
    for c, s in stripes: d.rectangle((x, 0, x + rw * s / tot, 230 * S), fill=c); x += rw * s / tot
    d.rectangle((40 * S, 0, w - 40 * S, 230 * S), outline=(20, 20, 20), width=5 * S)
    d.ellipse((w / 2 - 26 * S, 220 * S, w / 2 + 26 * S, 272 * S), outline=(200, 160, 60), width=10 * S)
    def star(cx, cy, R, r): return [(cx + (R if i % 2 == 0 else r) * math.sin(i * math.pi / 5), cy - (R if i % 2 == 0 else r) * math.cos(i * math.pi / 5)) for i in range(10)]
    cy = 430 * S; d.polygon(star(w / 2, cy, 175 * S, 70 * S), fill=(120, 85, 20)); d.polygon(star(w / 2, cy, 165 * S, 64 * S), fill=(232, 182, 70))
    for i in range(0, 10, 2):  # facetas
        pts = star(w / 2, cy, 165 * S, 64 * S); d.polygon([(w / 2, cy), pts[i], pts[(i + 1) % 10]], fill=(255, 214, 110))
    d.ellipse((w / 2 - 52 * S, cy - 52 * S, w / 2 + 52 * S, cy + 52 * S), fill=(150, 110, 40)); d.polygon(star(w / 2, cy, 44 * S, 18 * S), fill=(225, 228, 235))
    im = im.resize((int(w * size / h), size), Image.LANCZOS); D['icons'][k] = im; return im

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
                tail = solve(j)
                end = starts[j] if j < n else b; dur = end - starts[i]
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
    size = 80
    while font(FSUB, size).getlength(txt) > 860: size -= 2
    halo_text(can, txt, (540, 1400), size, WHITE, FSUB, hw=6, halo=(0, 0, 0))

# ---------------- coreografía ----------------
def sceneid(t): return next((s['id'] for s in TL['timeline'] if s['start'] <= t < s['start'] + s['dur']), '11')
SS = 2.3
HOOK_A = Cam(650, 0, 1.0, 40, -90, 800, SS); HOOK_B = Cam(690, 5, .88, 43, -90, 800, SS)
def trips():
    """(i, t_ir, t_toma, t_vuelta) por viaje visible."""
    if 'trips' in D: return D['trips']
    a7 = wt('07', 'Bull'); lf = wt('07', 'lifts'); b7 = SC['07'][1]
    T = [(0, a7 + .05, lf, b7 - .1)]
    e8 = [wt('08', 'Then'), wt('08', 'Again') - .25, wt('08', 'And') - .1, SC['08'][1]]
    for k in range(3): s0, s1 = e8[k], e8[k + 1]; T.append((k + 1, s0, lerp(s0, s1, .42), s1 - .05))
    D['trips'] = T; return T
def bull_state(t):
    """Posición de Bull y si carga a alguien (07-08)."""
    for i, t0, tp, t1 in trips():
        if t0 <= t < tp: return along(route(i), ease((t - t0) / (tp - t0), 'inout')), False, i
        if tp <= t < t1: return along(route(i), 1 - ease((t - tp) / (t1 - tp), 'inout')), True, i
    return AID, False, -1
def carried(t):
    """Cuántos heridos llegaron al puesto."""
    n = sum(1 for i, t0, tp, t1 in trips() if t >= t1)
    s9 = wt('09', 'Twelve')
    for j in range(4, 12):
        if t >= s9 + (j - 4) * .13 + .55: n += 1
    return n
def picked(i, t):
    for k, t0, tp, t1 in trips():
        if k == i: return t >= tp
    return t >= wt('09', 'Twelve') + (i - 4) * .13
def cam_at(t):
    sid = sceneid(t); a, b = SC[sid]
    if sid in ('01', '02'):
        c = blend_cam(HOOK_A, HOOK_B, ramp(t, 0, SC['02'][1], 'lin'))
        if sid == '02' and t >= wt('02', 'One'):
            bp = along(route(0), .55 - ramp(t, 0, SC['02'][1], 'lin') * .2); k = ramp(t, wt('02', 'One'), SC['02'][1])
            c = blend_cam(c, Cam(bp[0] + 40, bp[1], .7, 46, -90, 1050, SS), k)
        return c
    if sid == '03':
        A = Cam(*geo(146.6, -6.4), 1150, 0, 0, 900); B = Cam(*geo(147.04, -7.115), 16, 0, 0, 900); Cc = Cam(450, 0, 3.2, 48, -90, 980, SS)
        m = wt('03', 'Allied') - .4; n = wt('03', 'Mount') - .3
        if t < m: return blend_cam(A, B, ramp(t, wt('03', 'New') - .5, m))
        return blend_cam(B, Cc, ramp(t, n, b + .05))
    if sid == '04': return blend_cam(CAMS['04a'], CAMS['04b'], ramp(t, a, b, 'lin'))
    if sid == '05': return blend_cam(CAMS['04b'], CAMS['05'], ramp(t, a, a + 1.6))
    if sid == '06': return blend_cam(CAMS['05'], CAMS['06'], ramp(t, a, a + 1.6))
    if sid == '07':
        p, _, _ = bull_state(t); return blend_cam(CAMS['06'], follow(p), ramp(t, a, a + 1.0))
    if sid == '08':
        p, _, _ = bull_state(SC['07'][1] - .01); return blend_cam(follow(p), CAMS['08'], ramp(t, a, a + 1.2))
    if sid == '09': return blend_cam(CAMS['08'], CAMS['09'], ramp(t, a, a + 1.2))
    if sid == '10': return blend_cam(CAMS['09'], CAMS['10'], ramp(t, wt('10', 'For') - .3, b))
    return blend_cam(CAMS['10'], HOOK_A, ramp(t, a - .05, a + 1.1))

def fit(pA, yA, pB, yB, tilt, sy=960, ly=0.0):
    """Cámara (mirando al oeste) que pone el punto pA en la fila yA y pB en yB."""
    best = None
    for x in np.arange(-400, 2600, 20):
        for m in np.geomspace(.25, 3, 60):
            c = Cam(x, ly, m, tilt, -90, sy, SS); qa, qb = c.P(pA), c.P(pB)
            if not qa or not qb: continue
            e = (qa[1] - yA) ** 2 + (qb[1] - yB) ** 2
            if best is None or e < best[0]: best = (e, x, m)
    return Cam(best[1], ly, best[2], tilt, -90, sy, SS)
def follow(p): return Cam(p[0], p[1] * .6, .62, 46, -90, 1230, SS)
BP = (AID[0] - 40, AID[1] + 70)
CAMS = {'04a': fit(BP, 1230, (0, 0), 240, 44, ly=AID[1] + 40), '04b': fit(BP, 1270, (0, 0), 200, 46, ly=AID[1] + 40),
        '05': fit(US[2], 1050, (0, 0), 420, 44), '06': fit((1060, 0), 1230, (0, 0), 430, 40),
        '08': fit(AID, 1250, (0, 0), 330, 42), '09': fit(AID, 1180, (0, 0), 160, 46, ly=AID[1]), '10': fit(AID, 1150, (0, 0), 260, 30, ly=AID[1])}

SLOPE = WOUND + [J]
def frame(t, preview=False):
    init(); sid = sceneid(t); cam = cam_at(t); can = render_map(cam); gl = Glow()
    tilt_land = sid not in ('03',) or t > wt('03', 'Mount') - .3
    # ---- capas de mapa por escena ----
    if sid in ('01', '02'):
        bp = along(route(0), .55 - ramp(t, 0, SC['02'][1], 'lin') * .2)
        one = wt('02', 'One')
        for i in range(12):
            on = ramp(t, wt('01', 'twelve') + i * .05 - .3, wt('01', 'twelve') + i * .05)
            dim = 1 - .75 * ramp(t, one, one + .4) if i else 1
            if on > 0: dotted(can, cam, route(i), t, GOLD if i == 0 else WHITE, 4.5, alpha=on * dim)
        for i in range(1, 12): marker(can, cam, WOUND[i], 'wounded', 1, ramp(t, wt('01', 'wounded') + i * .04, wt('01', 'wounded') + i * .04 + .3, 'lin'))
        for n in NESTS: marker(can, cam, n, 'nest', 1.2)
        tracers(gl, cam, t, -0.5, SC['02'][1], SLOPE + [bp, bp], 11)
        for k, (tb, p) in enumerate([(.02, (bp[0] - 60, bp[1] - 330)), (1.5, (bp[0] - 150, bp[1] + 300)), (2.55, (bp[0] + 40, bp[1] - 380)), (4.2, (bp[0] - 220, bp[1] + 260))]):
            burst(can, gl, cam, p, t, tb, 95)
        marker(can, cam, AID, 'aid', 1.3)
        figure(can, cam, 'bull_carry', bp, 400, flip=False, t=t, walk=True)
    elif sid == '03':
        k = ramp(t, wt('03', 'Allied'), wt('03', 'Allied') + 1.2)
        if t < wt('03', 'Mount'):
            atlas(can, None, 'JULY 1943', None, 58, t, wt('03', 'July'), dy=420, spacing=10, t1=wt('03', 'Allied') - .2)
            atlas(can, cam, 'NEW GUINEA', geo(144.6, -5.6), 64, t, wt('03', 'New'), spacing=8, t1=wt('03', 'Allied') - .5)
            atlas(can, cam, 'AUSTRALIA', geo(143.5, -11.2), 40, t, wt('03', 'New') + .3, path=FATI, spacing=6, t1=wt('03', 'Allied') - .5)
            if t >= wt('03', 'Allied') - .5:
                atlas(can, cam, 'HUON GULF', geo(147.25, -6.95), 40, t, wt('03', 'Allied') - .2, path=FATI, fill=(200, 225, 240), spacing=4)
                q = cam.P(geo(147.067, -7.033))
                if q: ImageDraw.Draw(can).ellipse((q[0] - 8, q[1] - 8, q[0] + 8, q[1] + 8), fill=WHITE); halo_text(can, 'Salamaua', (q[0] + 18, q[1]), 34, WHITE, FATI, anchor='lm')
                jz = ramp(t, wt('03', 'Japanese'), wt('03', 'Japanese') + .6, 'out')
                if jz > 0:
                    zone = [geo(147.035 + .022 * math.cos(a) + .005 * math.sin(3 * a), -7.12 + .045 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)]
                    pp = [cam.P(p) for p in zone]
                    if all(pp):
                        lay = Image.new('L', (W, H)); ImageDraw.Draw(lay).polygon([(p[0], p[1]) for p in pp], fill=int(110 * jz)); can.paste((220, 40, 30), (0, 0), lay)
                        ImageDraw.Draw(can).line([(p[0], p[1]) for p in pp] + [(pp[0][0], pp[0][1])], fill=(255, 120, 100), width=4)
                        atlas(can, cam, 'JAPANESE', geo(147.035, -7.06), 34, t, wt('03', 'Japanese'), fill=(255, 190, 180), spacing=4)
                for p0, p1 in ((geo(147.11, -7.30), geo(147.045, -7.17)), (geo(146.99, -7.25), geo(147.015, -7.175))):
                    pts = bez(p0, ((p0[0] + p1[0]) / 2 + 900, (p0[1] + p1[1]) / 2), p1, 30)[: max(2, int(30 * k))]
                    pp = [cam.P(p) for p in pts]
                    if all(pp) and len(pp) > 1:
                        d = ImageDraw.Draw(can); d.line([(p[0], p[1]) for p in pp], fill=BLUE, width=16, joint='curve'); d.line([(p[0], p[1]) for p in pp], fill=(200, 230, 255), width=5, joint='curve')
                        (ax_, ay_), (bx_, by_) = pp[-2][:2], pp[-1][:2]; ang = math.atan2(by_ - ay_, bx_ - ax_)
                        d.polygon([(bx_ + math.cos(ang) * 34, by_ + math.sin(ang) * 34), (bx_ + math.cos(ang + 2.4) * 30, by_ + math.sin(ang + 2.4) * 30), (bx_ + math.cos(ang - 2.4) * 30, by_ + math.sin(ang - 2.4) * 30)], fill=BLUE)
                atlas(can, cam, 'ALLIES', geo(147.075, -7.205), 34, t, wt('03', 'Allied'), fill=(190, 225, 255), spacing=4)
        else:
            for n in NESTS: marker(can, cam, n, 'nest', 1.2, ramp(t, wt('03', 'Tambu'), wt('03', 'Tambu') + .4, 'lin'))
            atlas(can, cam, 'MOUNT TAMBU', (0, 0), 54, t, wt('03', 'Mount'), dy=-120, spacing=6)
            atlas(can, cam, '899 m', (0, 0), 32, t, wt('03', 'Tambu') + .2, dy=-70, path=FATI, spacing=2)
    else:
        n_saved = carried(t)
        # elementos persistentes de la ladera
        for n in NESTS: marker(can, cam, n, 'nest', 1.2)
        marker(can, cam, AID, 'aid', 1.3)
        hit = wt('05', 'Many')
        for i in range(12):
            if sid in ('04',) or (sid == '05' and t < hit): continue
            if picked(i, t): continue
            marker(can, cam, WOUND[i], 'wounded', 1, ramp(t, hit + i * .06, hit + i * .06 + .3, 'lin') if sid == '05' else 1)
        if sid in ('07', '08', '09', '10', '11'):
            for i in range(12):
                if picked(i, t) or sid in ('10', '11'): dotted(can, cam, route(i), t, GOLD, 4, alpha=.9 if sid != '11' else .5)
            for j in range(n_saved):
                p = (AID[0] - 40 + (j // 4) * 45, AID[1] - 110 - (j % 4) * 45); marker(can, cam, p, 'saved', .8, 1)
        if sid == '04':
            pop = ramp(t, SC['04'][0], SC['04'][0] + .5, 'lin'); big = 1 + .1 * ramp(t, wt('04', 'Big'), wt('04', 'Big') + .35, 'back') if t < wt('04', 'His') else 1.1
            figure(can, cam, 'bull', BP, 640 * big, t=t, pop=pop)
            atlas(can, None, 'LESLIE ALLEN', None, 58, t, wt('04', 'Leslie'), dy=250, spacing=6)
            atlas(can, None, 'Australian stretcher-bearer', None, 38, t, wt('04', 'stretcher-bearer'), dy=320, path=FATI, spacing=1, fill=(232, 236, 222))
            if t >= wt('04', 'Bull'): halo_text(can, '“BULL”', (540, 430), int(120 * ease(min(1, (t - wt('04', 'Bull')) / .3), 'back')) or 1, GOLD, FATI)
        elif sid in ('05', '06'):
            if sid == '05':
                for j, p in enumerate(US): figure(can, cam, 'us_pinned', p, 270, flip=j % 2 == 1, t=t, pop=ramp(t, SC['05'][0] + .1 + j * .15, SC['05'][0] + .6 + j * .15, 'lin'))
                if t >= wt('05', 'pinned'): atlas(can, None, 'U.S. TROOPS PINNED DOWN', None, 44, t, wt('05', 'pinned'), dy=300, spacing=4)
                tracers(gl, cam, t, SC['05'][0], SC['05'][1], US + WOUND, 12, 3)
                if t >= hit:
                    for k in range(3): burst(can, gl, cam, US[k], t, hit + k * .25 - .1, 80)
            else:
                sw = wt('06', 'sweep'); sweep(can, cam, t, sw, ramp(t, sw - .3, sw + .3, 'lin'))
                tracers(gl, cam, t, SC['06'][0], SC['06'][1], WOUND + [J], 14, 7)
                tw = wt('06', 'Two'); kl = wt('06', 'killed')
                for j, (p0, p1) in enumerate((((1050, -60), (720, -90)), ((1080, 80), (760, 70)))):
                    if t < tw: continue
                    p = (lerp(p0[0], p1[0], ramp(t, tw, kl, 'out')), lerp(p0[1], p1[1], ramp(t, tw, kl, 'out')))
                    marker(can, cam, p, 'dead' if t >= kl + j * .12 else 'medic', 1.2, ramp(t, tw + j * .1, tw + j * .1 + .3, 'lin'))
                atlas(can, cam, 'MACHINE GUNS', (0, -40), 40, t, wt('06', 'Machine'), dy=-90, fill=(255, 190, 175), spacing=4)
                if t >= kl: atlas(can, cam, '2 MEDICS KILLED', (900, 0), 36, t, kl + .1, dy=-130, spacing=3)
        elif sid in ('07', '08'):
            p, load, i = bull_state(t); prev, _, _ = bull_state(t - .05); q0, q1 = cam.P(prev), cam.P(p)
            flip = bool(q0 and q1 and q1[0] > q0[0])
            tracers(gl, cam, t, SC['07'][0], SC['08'][1], WOUND + [p, p, p], 11, 11)
            for k, tb in enumerate([SC['07'][0] + .6, wt('07', 'lifts') + .2, wt('07', 'carries'), SC['08'][0] + .4, wt('08', 'Again'), wt('08', 'And') + .2]):
                burst(can, gl, cam, (p[0] + 140 * (hsh(k, 1) - .5) * 2, p[1] + 140 * (hsh(k, 2) - .5) * 2), t, tb, 90)
            figure(can, cam, 'bull_carry' if load else 'bull', p, 470 if sid == '07' else 380, flip=flip if load else False, t=t, walk=True)
            if sid == '08' and t >= wt('08', 'Then'):
                q = cam.P(AID)
                if q: halo_text(can, f'{n_saved}', (q[0] + 170, q[1] - 50), 120, GREEN, FATL)
        elif sid == '09':
            s9 = wt('09', 'Twelve')
            for j in range(4, 12):
                u = ramp(t, s9 + (j - 4) * .13 - .35, s9 + (j - 4) * .13 + .55, 'inout')
                if 0 < u < 1:
                    q = cam.P(along(route(j), 1 - u))
                    if q: gl.disc((q[0], q[1]), 26 * q[2], (90, 255, 140))
            halo_text(can, f'{n_saved}', (540, 250), int(190 * (1 + .15 * (1 - min(1, max(0, t - s9) * 4)))), GREEN, FATL)
            if t >= wt('09', 'carried'): atlas(can, None, 'CARRIED OUT OF THE FIRE', None, 40, t, wt('09', 'carried'), dy=370, spacing=4)
            figure(can, cam, 'bull', BP, 520, t=t)
        elif sid == '10':
            figure(can, cam, 'bull', (BP[0], BP[1] + 160), 560, t=t)
            sv = wt('10', 'Silver')
            if t >= sv - .1:
                k = ramp(t, sv - .1, sv + .35, 'back'); m = medal(max(8, int(560 * k)))
                bob = 8 * math.sin(t * 2.2); can.paste(m, (int(790 - m.width / 2), int(900 - m.height / 2 + bob)), m)
                for j in range(12):
                    ang = j * math.pi / 6 + t * .5; r0 = 300 * k; ImageDraw.Draw(can).line((790 + math.cos(ang) * r0, 960 + math.sin(ang) * r0, 790 + math.cos(ang) * (r0 + 40), 960 + math.sin(ang) * (r0 + 40)), fill=GOLD, width=5)
                atlas(can, None, 'SILVER STAR', None, 64, t, wt('10', 'Star'), dy=470, spacing=8)
                atlas(can, None, 'awarded by the United States', None, 36, t, wt('10', 'Star') + .3, dy=535, path=FATI, spacing=1, fill=(235, 235, 225))
        else:
            k = ramp(t, SC['11'][0], SC['11'][1], 'lin'); p = along(route(0), .55 + .3 * k)
            tracers(gl, cam, t, SC['11'][0] - .3, 99, WOUND, 9, 2)
            figure(can, cam, 'bull', p, 520, t=t, walk=True)
    can = gl.apply(can)
    can.paste((0, 0, 0), (0, 0), D['vig'].point(lambda v: 255 - v))
    can = post(can, t); subtitle(can, t); return can

SHAKES = [(.02, 14, .3), (1.5, 10, .25), (2.55, 10, .25), (4.2, 8, .22)]
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
    if not os.path.exists(os.path.join(PREP, 'geo.json')): subprocess.run([sys.executable, os.path.join(HERE, 'terrain.py')], check=True)
    for n in ('bull', 'bull_carry', 'us_pinned'): cut(n).save(os.path.join(PREP, 'fig_' + n + '.png'))
    print('PREP COMPLETE', flush=True)

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
    dest = Path(ROOT, 'Render', 'Shorts'); dest.mkdir(parents=True, exist_ok=True); out = dest / 'S11_BullAllen.mp4'; up = dest / 'S11_upload.mp4'
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

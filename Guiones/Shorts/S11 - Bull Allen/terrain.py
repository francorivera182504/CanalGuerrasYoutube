"""S11: escenarios de mapa real. python terrain.py -> _prep/stage_local.png, _prep/stage_png.png, _prep/geo.json
local = relieve real (Terrarium z12, AWS Open Data / Mapzen) alrededor de Mount Tambu y Salamaua.
png   = Natural Earth I (relieve sombreado) de Nueva Guinea."""
import os, json, math, glob
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); PREP = os.path.join(HERE, '_prep'); DEM = os.path.join(HERE, '_dem')
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
Image.MAX_IMAGE_PIXELS = None

def tile_lonlat(x, y, z):
    n = 2 ** z; lon = x / n * 360 - 180; lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n)))); return lon, lat

def mosaic(z):
    fs = glob.glob(os.path.join(DEM, f'{z}_*.png')); xs = sorted({int(f.split('_')[-2]) for f in fs}); ys = sorted({int(f.split('_')[-1][:-4]) for f in fs})
    out = np.zeros((256 * len(ys), 256 * len(xs)), np.float32)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            a = np.asarray(Image.open(os.path.join(DEM, f'{z}_{x}_{y}.png')).convert('RGB')).astype(np.float32)
            out[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    lon0, lat0 = tile_lonlat(xs[0], ys[0], z); lon1, lat1 = tile_lonlat(xs[-1] + 1, ys[-1] + 1, z)
    return out, (lon0, lat0, lon1, lat1)

def fbm(shape, seed, scales=(3, 8, 24, 70)):
    rng = np.random.default_rng(seed); acc = np.zeros(shape, np.float32)
    for k, s in enumerate(scales):
        acc += ndimage.gaussian_filter(rng.standard_normal(shape).astype(np.float32), s) * (s ** .55)
    acc -= acc.mean(); return acc / (acc.std() + 1e-6)

def shade(dem, px_m, az=315, alt=38, exag=1.6):
    gy, gx = np.gradient(dem * exag, px_m)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    a, z = math.radians(az), math.radians(90 - alt)
    return np.clip(np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect), 0, 1)

def colorize(dem, hs, seed):
    land = dem > 0.5
    lo = np.array((38, 74, 40), np.float32); mid = np.array((70, 104, 52), np.float32); hi = np.array((118, 120, 74), np.float32)
    e = np.clip(dem / 1400, 0, 1)[..., None]
    col = np.where(e < .5, lo + (mid - lo) * (e / .5), mid + (hi - mid) * ((e - .5) / .5))
    n = fbm(dem.shape, seed)[..., None]; col = col * (1 + .09 * n)  # copa de selva
    dist = ndimage.distance_transform_edt(~land)[..., None]
    sea = np.array((16, 52, 84), np.float32) + np.array((40, 70, 60), np.float32) * np.exp(-dist / 18)
    beach = np.exp(-ndimage.distance_transform_edt(land) / 2.5)[..., None] * land[..., None]
    col = col * (1 - beach * .6) + np.array((150, 140, 100)) * beach * .6
    light = (.35 + .95 * hs)[..., None]
    out = np.where(land[..., None], col * light, sea * (.95 + .05 * fbm(dem.shape, seed + 1, (60, 200))[..., None]))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def feather(im, f):
    yy, xx = np.mgrid[0:im.height, 0:im.width]
    d = np.minimum(np.minimum(xx, im.width - 1 - xx), np.minimum(yy, im.height - 1 - yy))
    im = im.convert('RGBA'); im.putalpha(Image.fromarray((np.clip(d / f, 0, 1) * 255).astype(np.uint8))); return im

def local(z=12, up=3, name='local', seed=7, exag=1.6):
    dem, (lon0, lat0, lon1, lat1) = mosaic(z)
    dem = ndimage.zoom(dem, up, order=3); dem = ndimage.gaussian_filter(dem, 1.2)
    m = (lon1 - lon0) / dem.shape[1] * 111320 * math.cos(math.radians(7.1))
    im = feather(colorize(dem, shade(dem, m, exag=exag), seed), 420 if z == 12 else 160)
    im.save(os.path.join(PREP, f'stage_{name}.png'))
    np.save(os.path.join(PREP, f'dem_{name}.npy'), dem.astype(np.float32))
    return dict(lon0=lon0, lat0=lat0, lon1=lon1, lat1=lat1, w=im.width, h=im.height, merc=True, z=z)

def tambu(g, lon0=146.985, lon1=147.075, lat0=-7.125, lat1=-7.200, up=4):
    """Detalle de Mount Tambu: recorte del DEM z12 (mejor fuente) ampliado y suavizado."""
    dem = np.load(os.path.join(PREP, 'dem_local.npy'))
    M = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    px = lambda lon: (lon - g['lon0']) / (g['lon1'] - g['lon0']) * g['w']
    py = lambda lat: (M(g['lat0']) - M(lat)) / (M(g['lat0']) - M(g['lat1'])) * g['h']
    x0, x1, y0, y1 = int(px(lon0)), int(px(lon1)), int(py(lat0)), int(py(lat1))
    d = ndimage.zoom(dem[y0:y1, x0:x1], up, order=3); d = ndimage.gaussian_filter(d, 7)
    inv = lambda yy: math.degrees(2 * math.atan(math.exp(M(g['lat0']) - yy / g['h'] * (M(g['lat0']) - M(g['lat1'])))) - math.pi / 2)
    ilon = lambda xx: g['lon0'] + xx / g['w'] * (g['lon1'] - g['lon0'])
    m = (ilon(x1) - ilon(x0)) / d.shape[1] * 111320 * math.cos(math.radians(7.1))
    micro = shade(6 * fbm(d.shape, 21, (2, 4, 9)), m, exag=1)  # micro-relieve de selva
    im = colorize(d, np.clip(shade(d, m, exag=2.4) * (.72 + .55 * micro), 0, 1), 11)
    a = np.asarray(im).astype(np.float32); c = fbm(d.shape, 5, (1.2, 2.5)); a *= (1 + .16 * np.tanh(c))[..., None]  # copas
    im = feather(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 220)
    im.save(os.path.join(PREP, 'stage_tambu.png')); np.save(os.path.join(PREP, 'dem_tambu.npy'), d.astype(np.float32))
    return dict(lon0=ilon(x0), lat0=inv(y0), lon1=ilon(x1), lat1=inv(y1), w=im.width, h=im.height, merc=True)

def png():
    tif = os.path.join(ROOT, 'Recursos', 'naturalearth', 'NE1_HR_LC_SR_W_DR', 'NE1_HR_LC_SR_W_DR.tif')
    big = Image.open(tif); s = big.width / 360
    lon0, lon1, lat0, lat1 = 132.0, 160.0, 6.0, -18.0
    box = (int((lon0 + 180) * s), int((90 - lat0) * s), int((lon1 + 180) * s), int((90 - lat1) * s))
    im = big.crop(box).convert('RGB'); im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    # tono selva más oscuro y mar más profundo (coherente con el local)
    water = (a[..., 2] > a[..., 1] + 8) & (a[..., 2] > a[..., 0] + 20)
    a[water] = a[water] * (np.array((22, 60, 92)) / a[water].mean(0))
    a[~water] = a[~water] * (np.array((60, 92, 48)) / a[~water].mean(0))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 60, 2)).convert('RGBA').save(os.path.join(PREP, 'stage_png.png'))
    return dict(lon0=lon0, lat0=lat0, lon1=lon1, lat1=lat1, w=im.width, h=im.height, merc=False)

if __name__ == '__main__':
    os.makedirs(PREP, exist_ok=True)
    geo = dict(png=png(), local=local()); geo['tambu'] = tambu(geo['local'])
    dem = np.load(os.path.join(PREP, 'dem_tambu.npy'))
    json.dump(geo, open(os.path.join(PREP, 'geo.json'), 'w'), indent=1); print(geo, dem.min(), dem.max())
    for n in ('png', 'local', 'tambu'):
        im = Image.open(os.path.join(PREP, f'stage_{n}.png')); im = im.convert('RGB'); im.thumbnail((900, 900)); im.save(os.path.join(PREP, f'_thumb_{n}.jpg'), quality=85)

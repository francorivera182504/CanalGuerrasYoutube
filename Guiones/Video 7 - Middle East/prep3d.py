"""Prepara relieve + textura neón para las tomas 3D (kit reutilizable).
python prep3d.py   -> _prep/3d/<area>_dem.npy (alturas en m, rejilla 480x270) + <area>_tex.png (3840x2160) + areas.json
Textura = nuestro mapa neón 2D (mapa.py), así el 3D tiene el mismo estilo.
Elevación: tiles Terrarium públicos (s3 elevation-tiles-prod), en caché en Recursos/terrarium/.
"""
import json, math, os, sys, urllib.request
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mapa as M
from mapa import View, W, H
import engine as E
ROOT = os.path.normpath(os.path.join(HERE, "..", "..")); CACHE = os.path.join(ROOT, "Recursos", "terrarium"); OUT = os.path.join(HERE, "_prep", "3d")

# área: (vista, zoom de tiles, rellenos [(región, color, alfa)], oscuridad)
AREAS = {
    "iran":   (View(52.0, 32.2, 22.0), 6, [("Iran", "GOLD", 0.18)], 0.55),
    "hormuz": (View(56.3, 26.5, 4.8), 8, [("Iran", "GOLD", 0.14), ("Oman", "GREY", 0.10), ("United Arab Emirates", "GREY", 0.10)], 0.7),
    "levant": (View(35.0, 31.4, 7.0), 8, [("Israel", "BLUE", 0.22), ("Palestine", "GREEN", 0.25), ("SINAI", "GOLD", 0.45), ("GOLAN", "GOLD", 0.55), ("WB", "GOLD", 0.40), ("GAZA", "GOLD", 0.55)], 0.85),
}

def tile(z, x, y):
    p = os.path.join(CACHE, f"{z}_{x}_{y}.png")
    if not os.path.exists(p):
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", p)
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def dem(v, z, gw=480, gh=270):
    lon0 = v.lon - W / 2 / (M.K * v.s); lon1 = v.lon + W / 2 / (M.K * v.s); lat1 = v.lat + H / 2 / v.s; lat0 = v.lat - H / 2 / v.s
    lons = np.linspace(lon0, lon1, gw); lats = np.linspace(lat1, lat0, gh)
    tx0, ty0 = lonlat_to_tile(lon0, lat1, z); tx1, ty1 = lonlat_to_tile(lon1, lat0, z)
    xs = range(int(tx0), int(tx1) + 1); ys = range(int(ty0), int(ty1) + 1)
    mos = np.vstack([np.hstack([tile(z, x, y) for x in xs]) for y in ys])
    out = np.zeros((gh, gw), np.float32)
    for j, la in enumerate(lats):
        for i, lo in enumerate(lons):
            fx, fy = lonlat_to_tile(lo, la, z); px = int((fx - xs[0]) * 256); py = int((fy - ys[0]) * 256)
            out[j, i] = mos[min(py, mos.shape[0] - 1), min(px, mos.shape[1] - 1)]
    return np.maximum(out, -50), (lon0, lon1, lat0, lat1)

def texture(v, fills, dark):
    """renderiza el mapa neón a 2x (4 cuadrantes de media anchura)."""
    E.init(); big = Image.new("RGB", (W * 2, H * 2))
    for qx in (0, 1):
        for qy in (0, 1):
            cx = v.lon + (qx - 0.5) * (W / 2) / (M.K * v.s); cy = v.lat - (qy - 0.5) * (H / 2) / v.s
            sub = View(cx, cy, v.wdeg / 2)
            ms = [(E.rmask(sub, r), E.C(c), a) for r, c, a in fills]
            can, n = M.render(sub, ms)
            for m, c, a in ms: n.edge(m, c, 0.9)
            can = n.draw(can)
            # quitar viñeta del render (la textura no la necesita): aclarar bordes
            big.paste(can, (qx * W, qy * H))
    return ImageEnhance.Brightness(big).enhance(dark * 1.25)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); info = {}
    for name, (v, z, fills, dark) in AREAS.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
        d, bb = dem(v, z); np.save(os.path.join(OUT, f"{name}_dem.npy"), d)
        texture(v, fills, dark).save(os.path.join(OUT, f"{name}_tex.png"))
        info[name] = {"bbox": bb, "maxh": float(d.max()), "view": [v.lon, v.lat, v.wdeg]}
        print(name, bb, d.min(), d.max())
    p = os.path.join(OUT, "areas.json"); old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(info); json.dump(old, open(p, "w"), indent=1)

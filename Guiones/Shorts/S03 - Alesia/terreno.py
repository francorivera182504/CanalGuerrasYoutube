"""Terreno de Alesia a partir de tiles Terrarium z13 (Recursos/terreno_alesia).
Salida (en terreno/): height16.png (16 bit), color.png (satélite sintético, sin pueblos ni carreteras modernas),
rings.json (líneas interior/exterior en metros locales, centro = Mont-Auxois) y meta.json.
"""
import glob, json, math, os, re
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "..", "Recursos", "terreno_alesia")
OUT = os.path.join(HERE, "terreno"); os.makedirs(OUT, exist_ok=True)
Z = 13
LAT0, LON0 = 47.537, 4.500          # Mont-Auxois (Alise-Sainte-Reine)

tiles = {}
for f in glob.glob(os.path.join(SRC, f"terrarium_{Z}_*.png")):
    _, x, y = re.findall(r"\d+", os.path.basename(f))[-3:]
    tiles[(int(x), int(y))] = f
xs = sorted({k[0] for k in tiles}); ys = sorted({k[1] for k in tiles})
H = np.zeros((256 * len(ys), 256 * len(xs)))
for (x, y), f in tiles.items():
    a = np.asarray(Image.open(f).convert("RGB")).astype(float)
    H[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
n = 2 ** Z
def px(lat, lon):
    gx = (lon + 180) / 360 * n * 256
    gy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256
    return gx - xs[0] * 256, gy - ys[0] * 256
cx, cy = px(LAT0, LON0)
mpp = 40075016.686 * math.cos(math.radians(LAT0)) / (n * 256)   # metros por píxel
# recorte cuadrado de 1024 px (~13 km) centrado en el monte
S = 1024
x0, y0 = int(cx - S / 2), int(cy - S / 2)
H = H[y0:y0 + S, x0:x0 + S]
H = ndimage.gaussian_filter(H, 0.8)
cx, cy = cx - x0, cy - y0
print("mpp", round(mpp, 2), "size km", round(S * mpp / 1000, 2), "h", H.min().round(), H.max().round())

# ---------- líneas (polar, siguiendo el terreno) ----------
def ring(rmin, rmax, pick, smooth):
    th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    rs = []
    for t in th:
        rr = np.linspace(rmin, rmax, 60)
        xx = cx + np.cos(t) * rr / mpp; yy = cy - np.sin(t) * rr / mpp
        h = ndimage.map_coordinates(H, [yy, xx], order=1)
        rs.append(rr[np.argmin(h) if pick == "min" else np.argmax(h)])
    rs = np.array(rs)
    k = np.exp(-0.5 * (np.arange(-smooth * 2, smooth * 2 + 1) / smooth) ** 2); k /= k.sum()
    rs = np.convolve(np.r_[rs[-len(k):], rs, rs[:len(k)]], k, "same")[len(k):-len(k)]
    pts = np.c_[np.cos(th) * rs, np.sin(th) * rs]
    return pts
def perim(p): return np.sum(np.hypot(*(np.roll(p, -1, 0) - p).T))
inner = ring(1500, 2900, "min", 10)
outer = ring(3000, 4600, "max", 14)
# escalar a ~15 km y ~21 km de perímetro (cifras del MuséoParc)
inner *= 15000 / perim(inner); outer *= 21000 / perim(outer)
print("perim", round(perim(inner)), round(perim(outer)))
json.dump({"inner": inner.round(1).tolist(), "outer": outer.round(1).tolist()}, open(os.path.join(OUT, "rings.json"), "w"))

# ---------- color tipo satélite (estilizado, sin elementos modernos) ----------
gy_, gx_ = np.gradient(H * 2.5, mpp)
slope = np.degrees(np.arctan(np.hypot(gx_, gy_)))
az, alt = math.radians(315), math.radians(40)
asp = np.arctan2(-gx_, gy_)
shade = np.sin(alt) * np.cos(np.radians(slope)) + np.cos(alt) * np.sin(np.radians(slope)) * np.cos(az - asp)
shade = np.clip(shade, 0, 1)
rng = np.random.default_rng(7)
# parcelas: voronoi grosero de colores de cultivo
cells = rng.uniform(0, S, (5000, 2)); cols = np.array([[96, 128, 60], [128, 140, 70], [150, 140, 85], [84, 112, 52], [110, 130, 62], [160, 150, 98]])
lab = rng.integers(0, len(cols), len(cells))
yy, xx = np.mgrid[0:S, 0:S]
from scipy.spatial import cKDTree
_, idx = cKDTree(cells).query(np.c_[xx.ravel(), yy.ravel()])
# praderas: mezcla suave de verdes/ocres a varias escalas (sin parcelas modernas)
def fbm(sig):
    n = ndimage.gaussian_filter(rng.normal(size=(S, S)), sig); return (n - n.mean()) / n.std()
m = 0.55 * fbm(40) + 0.3 * fbm(12) + 0.15 * fbm(3)
t = np.clip((m + 1.6) / 3.2, 0, 1)[..., None]
c_lo, c_mid, c_hi = np.array([70, 104, 46.]), np.array([104, 128, 62.]), np.array([150, 142, 90.])
field = np.where(t < 0.55, c_lo + (c_mid - c_lo) * (t / 0.55), c_mid + (c_hi - c_mid) * ((t - 0.55) / 0.45))
field = field + fbm(1.2)[..., None] * 5
forest = np.array([38, 62, 34], float)
fmask = np.clip((slope - 14) / 8, 0, 1)                               # laderas = bosque
noise = ndimage.gaussian_filter(rng.normal(size=(S, S)), 6); noise = (noise - noise.min()) / (np.ptp(noise))
fmask = np.clip(fmask + (noise > 0.72) * 0.8, 0, 1)
plateau = np.clip((H - (H.max() - 45)) / 20, 0, 1)                    # meseta del oppidum un poco más clara
col = field * (1 - fmask[..., None]) + forest * fmask[..., None]
col = col * (1 - 0.25 * plateau[..., None]) + np.array([150, 140, 100]) * 0.25 * plateau[..., None]
# ríos: fondos de valle
valley = np.zeros_like(H, bool)
riv = ndimage.binary_opening(valley, iterations=1)
col[riv] = col[riv] * 0.5 + np.array([60, 90, 110]) * 0.5
col = col * (0.3 + 0.95 * shade[..., None])
col = np.clip(col + rng.normal(0, 4, col.shape), 0, 255).astype(np.uint8)
Image.fromarray(col).resize((2048, 2048), Image.LANCZOS).filter(ImageFilter.SMOOTH).save(os.path.join(OUT, "color.png"))
h16 = ((H - H.min()) / (H.max() - H.min()) * 65535).astype(np.uint16)
Image.fromarray(h16).save(os.path.join(OUT, "height16.png"))
json.dump({"mpp": mpp, "size_m": S * mpp, "hmin": float(H.min()), "hmax": float(H.max()), "center_px": [cx, cy]}, open(os.path.join(OUT, "meta.json"), "w"))
print("ok")

# versión sin sombreado para Blender (la luz la pone la geometría) + altura en metros
col3 = field * (1 - fmask[..., None]) + forest * fmask[..., None]
col3 = col3 * (1 - 0.25 * plateau[..., None]) + np.array([150, 140, 100]) * 0.25 * plateau[..., None]
col3 = np.clip(col3 * 1.05 + rng.normal(0, 3, col3.shape), 0, 255).astype(np.uint8)
Image.fromarray(col3).resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, "color_flat.png"))
np.save(os.path.join(OUT, "height.npy"), H.astype(np.float32))
print("flat ok")
np.save(os.path.join(OUT, "forest.npy"), fmask.astype(np.float32))

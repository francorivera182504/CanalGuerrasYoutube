"""Mapa neón (Natural Earth) para el Video 6 — Crimea. 1920x1080.
python mapa.py --prep   -> _prep/base.png + _prep/geo.json
python mapa.py --test   -> _prep/map_*.jpg (vistas de prueba)
Proyección: equirectangular con x escalado por cos(47°).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
NE = os.path.join(ROOT, "Recursos", "naturalearth")
PREP = os.path.join(HERE, "_prep", "map")
W, H = 1080, 1920
K = math.cos(math.radians(25.0))
LON0, LON1, LAT0, LAT1 = 110.0, 165.0, -15.0, 50.0
PPD = 60                                  # píxeles por grado de la base (lat)
BW, BH = int((LON1 - LON0) * K * PPD), int((LAT1 - LAT0) * PPD)

RED, BLUE, GREEN, GOLD, GREY = (255, 50, 40), (60, 150, 255), (60, 220, 140), (255, 190, 60), (150, 160, 175)

def simplify(pts, eps):
    if len(pts) < 4: return [tuple(p) for p in pts]
    if tuple(pts[0]) == tuple(pts[-1]):
        a = np.array(pts); k = int(np.argmax(np.hypot(*(a - a[0]).T)))
        return simplify(pts[:k + 1], eps)[:-1] + simplify(pts[k:], eps)
    a = np.array(pts); keep = np.zeros(len(a), bool); keep[0] = keep[-1] = True; st = [(0, len(a) - 1)]
    while st:
        i, j = st.pop()
        if j <= i + 1: continue
        p, q = a[i], a[j]; d = q - p; n = np.hypot(*d) or 1e-9
        v = a[i + 1:j] - p; dist = np.abs(d[0] * v[:, 1] - d[1] * v[:, 0]) / n; k = int(np.argmax(dist))
        if dist[k] > eps: keep[i + 1 + k] = True; st += [(i, i + 1 + k), (i + 1 + k, j)]
    return [tuple(map(float, x)) for x in a[keep]]

def prep():
    import shapefile
    os.makedirs(PREP, exist_ok=True)
    Image.MAX_IMAGE_PIXELS = None
    ne = Image.open(os.path.join(NE, "NE1_HR_LC_SR_W_DR", "NE1_HR_LC_SR_W_DR.tif"))
    box = (int((LON0 + 180) * 60), int((90 - LAT1) * 60), int((LON1 + 180) * 60), int((90 - LAT0) * 60))
    g = ne.crop(box).convert("RGB").resize((BW, BH), Image.LANCZOS)
    g = ImageEnhance.Brightness(ImageEnhance.Color(g).enhance(0.55)).enhance(0.5)
    g.save(os.path.join(PREP, "base.png"))
    geo = {"countries": {}, "crimea": [], "lakes": {}, "rivers": {}}
    rd = shapefile.Reader(os.path.join(NE, "ne_10m_admin_0_countries", "ne_10m_admin_0_countries.shp"))
    ia = [f[0] for f in rd.fields[1:]].index("ADMIN")
    for sr in rd.iterShapeRecords():
        name = sr.record[ia]; bb = sr.shape.bbox
        if bb[2] < LON0 or bb[0] > LON1 or bb[3] < LAT0 or bb[1] > LAT1: continue
        pts = sr.shape.points; parts = list(sr.shape.parts) + [len(pts)]
        for a, b in zip(parts, parts[1:]):
            ring = pts[a:b]; lo = [p[0] for p in ring]; la = [p[1] for p in ring]
            if max(lo) < LON0 - 5 or min(lo) > LON1 + 5 or max(la) < LAT0 - 3 or min(la) > LAT1 + 3: continue
            if len(ring) < 8 and (max(lo) - min(lo)) < 0.05: continue
            r = simplify(ring, 0.004)
            if name == "Russia" and 32 < min(lo) < 33 and 44 < min(la) < 45 and max(la) < 46.5:
                geo["crimea"].append(r); continue
            geo["countries"].setdefault(name, []).append(r)
    lk = shapefile.Reader(os.path.join(NE, "ne_10m_lakes", "ne_10m_lakes.shp")); il = [f[0] for f in lk.fields[1:]].index("name")
    for sr in lk.iterShapeRecords():
        if sr.record[il] == "Kakhovka Reservoir": geo["lakes"]["kakhovka"] = [simplify(sr.shape.points, 0.003)]
    rv = shapefile.Reader(os.path.join(NE, "ne_10m_rivers_lake_centerlines", "ne_10m_rivers_lake_centerlines.shp")); ir = [f[0] for f in rv.fields[1:]].index("name")
    for sr in rv.iterShapeRecords():
        n = sr.record[ir]
        if n in ("Dnipro", "Don", "Southern Bug", "Dniester") and sr.shape.bbox[1] < 52:
            geo["rivers"].setdefault(n, []).append(simplify(sr.shape.points, 0.005))
    json.dump(geo, open(os.path.join(PREP, "geo.json"), "w"))
    print("prep ok", BW, BH, {k: len(v) for k, v in geo["countries"].items() if k in ("Russia", "Ukraine")}, len(geo["crimea"]))

# ---------------- datos ----------------
G = {}
def load():
    if G: return
    G["base"] = Image.open(os.path.join(PREP, "base.png")).convert("RGB")
    G.update(json.load(open(os.path.join(PREP, "geo.json"))))
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((-300, -200, W + 300, H + 200), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220)).point(lambda v: int(110 + v * 145 / 255))
    G["vig"] = Image.merge("RGB", (vig, vig, vig))

class View:
    """Vista centrada en (lon, lat) con `wdeg` grados de longitud a lo ancho."""
    def __init__(self, lon, lat, wdeg):
        self.lon, self.lat, self.wdeg = lon, lat, wdeg
        self.s = W / (wdeg * K)                            # px de pantalla por grado de latitud
    def P(self, lon, lat): return (W / 2 + (lon - self.lon) * K * self.s, H / 2 + (self.lat - lat) * self.s)
    def pts(self, ring): return [self.P(*p) for p in ring]
    def base(self):
        f = PPD / self.s; bx = (self.lon - LON0) * K * PPD; by = (LAT1 - self.lat) * PPD
        box = (bx - W / 2 * f, by - H / 2 * f, bx + W / 2 * f, by + H / 2 * f)
        return G["base"].transform((W, H), Image.EXTENT, box, Image.BILINEAR)
    def visible(self, ring, m=0.3):
        lo = [p[0] for p in ring]; la = [p[1] for p in ring]
        hw = self.wdeg / 2 * (1 + m); hh = self.wdeg * H / W / K / 2 * (1 + m) + 0.2
        return not (max(lo) < self.lon - hw or min(lo) > self.lon + hw or max(la) < self.lat - hh or min(la) > self.lat + hh)

def mask(view, rings):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for r in rings:
        if view.visible(r): d.polygon(view.pts(r), fill=255)
    return m

def country(name):
    if name == "Crimea": return G["crimea"]
    return G["countries"].get(name, [])

def edge_of(m, w=5):
    return ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(w)))

# ---------------- neón ----------------
class Neon:
    def __init__(self): self.items = []
    def line(self, pts, col, w=6, closed=False, k=1.0): self.items.append(("l", pts, col, w, closed, k))
    def dot(self, xy, col, r, k=1.0): self.items.append(("d", xy, col, r, k))
    def edge(self, m, col, k=1.0): self.items.append(("e", m, col, k))
    def draw(self, can):
        if not self.items: return can
        gl = Image.new("RGB", (W // 2, H // 2)); gd = ImageDraw.Draw(gl)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = list(pts) + [pts[0]] if closed else pts
                gd.line([(x / 2, y / 2) for x, y in p], fill=tuple(int(c * k) for c in col), width=max(3, int(w * 0.9)), joint="curve")
            elif it[0] == "d":
                _, (x, y), col, r, k = it; r2 = r * 1.4 / 2
                gd.ellipse((x / 2 - r2, y / 2 - r2, x / 2 + r2, y / 2 + r2), fill=tuple(int(c * k) for c in col))
            else:
                _, m, col, k = it
                e = edge_of(m, 7).resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.MaxFilter(3))
                gl.paste(tuple(int(c * k) for c in col), mask=e)
        g1 = gl.filter(ImageFilter.GaussianBlur(11)); g2 = gl.filter(ImageFilter.GaussianBlur(3))
        glow = ImageChops.add(ImageChops.add(g1, g1), g2).resize((W, H), Image.BILINEAR)
        can = ImageChops.add(can, glow); d = ImageDraw.Draw(can)
        for it in self.items:
            if it[0] == "l":
                _, pts, col, w, closed, k = it
                if len(pts) < 2: continue
                p = list(pts) + [pts[0]] if closed else pts
                d.line(p, fill=tuple(int(c + (255 - c) * 0.15) for c in col), width=w, joint="curve")
                d.line(p, fill=(255, 240, 230), width=max(1, w // 4), joint="curve")
            elif it[0] == "d":
                _, (x, y), col, r, k = it
                d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=(255, 250, 245))
            else:
                _, m, col, k = it
                e = edge_of(m, 3)
                can.paste(tuple(int(c + (255 - c) * 0.5) for c in col), mask=e.point(lambda v: int(v * min(1, k))))
        return can

# ---------------- render de mapa ----------------
def render(view, fills=(), neon=None, sea=(4, 14, 30), land_k=1.0):
    """fills: lista de (rings, color, alpha 0–1). Devuelve (imagen, neon)."""
    load()
    can = view.base()
    land = Image.new("L", (W, H), 0); d = ImageDraw.Draw(land)
    for name, rings in G["countries"].items():
        for r in rings:
            if view.visible(r): d.polygon(view.pts(r), fill=255)
    for r in G["crimea"]: d.polygon(view.pts(r), fill=255)
    for r in G["lakes"].get("kakhovka", []): d.polygon(view.pts(r), fill=0)
    land = land.filter(ImageFilter.GaussianBlur(0.8))
    seaim = ImageChops.multiply(can, Image.new("RGB", (W, H), (70, 95, 130)))
    seaim = ImageChops.add(seaim, Image.new("RGB", (W, H), sea))
    landim = ImageEnhance.Brightness(can).enhance(0.82 * land_k)
    can = Image.composite(landim, seaim, land)
    for rings, col, a in fills:
        m = mask(view, rings) if not isinstance(rings, Image.Image) else rings
        can = Image.composite(Image.new("RGB", (W, H), col), can, m.point(lambda v: int(v * a)))
    can = ImageChops.multiply(can, G["vig"])
    # costa tenue
    ce = edge_of(land, 3).point(lambda v: int(v * 0.35))
    can.paste((150, 190, 230), mask=ce)
    return can, (neon or Neon())


if __name__=='__main__':
 if '--prep' in sys.argv: prep()

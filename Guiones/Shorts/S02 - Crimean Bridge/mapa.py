"""Mapa simplificado Crimea / estrecho de Kerch / mar de Azov dibujado desde coordenadas reales (estilo pizarra)."""
import math
from PIL import Image, ImageDraw

W, H = 1080, 1920
LON0, LON1, LAT0, LAT1 = 32.2, 39.1, 44.15, 47.95
K = math.cos(math.radians(45.8))
SCALE = W / ((LON1 - LON0) * K)
MAP_H = (LAT1 - LAT0) * SCALE
TOP = 430  # y del borde superior del mapa en el cuadro

def P(lon, lat):
    return ((lon - LON0) * K * SCALE, TOP + (LAT1 - lat) * SCALE)

SEA = (150, 214, 242); LAND = (255, 233, 192); INK = (20, 20, 20)
NORTH = [(32.2, 46.55), (32.45, 46.45), (32.6, 46.1), (33.0, 46.12), (33.45, 46.08), (33.65, 46.2), (34.0, 46.18), (34.4, 46.05),
         (34.82, 46.17), (35.2, 46.4), (35.8, 46.62), (36.6, 46.75), (37.5, 47.05), (38.2, 47.1), (38.9, 47.25), (39.1, 47.25),
         (39.1, 47.95), (32.2, 47.95)]
EAST = [(39.1, 47.2), (38.6, 46.9), (38.3, 46.7), (37.9, 46.3), (37.75, 46.0), (37.95, 45.7), (37.6, 45.5), (37.25, 45.35),
        (36.9, 45.4), (36.72, 45.4), (36.66, 45.3), (36.68, 45.2), (36.8, 45.1), (37.05, 45.05), (37.3, 44.92), (37.8, 44.7),
        (38.4, 44.4), (39.1, 44.15), (39.1, 47.2)]
CRIMEA = [(33.6, 46.2), (34.0, 46.12), (34.45, 45.9), (34.9, 45.75), (35.25, 45.55), (35.45, 45.35), (35.9, 45.45),
          (36.2, 45.47), (36.45, 45.43), (36.6, 45.38), (36.5, 45.28), (36.47, 45.12), (36.15, 45.02), (35.6, 45.05),
          (35.4, 45.04), (35.0, 44.83), (34.45, 44.7), (34.15, 44.49), (33.75, 44.39), (33.45, 44.5), (33.52, 44.63),
          (33.55, 44.85), (33.6, 45.05), (33.35, 45.2), (32.9, 45.35), (32.5, 45.38), (32.7, 45.55), (33.2, 45.85),
          (33.55, 45.97), (33.6, 46.2)]

def smooth(pts, it=3):
    for _ in range(it):
        out = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = out + [out[0]]
    return pts

def poly(d, ll, fill, width=6, sm=True):
    pts = [P(*p) for p in ll]
    if sm: pts = smooth(pts + [pts[0]])
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=INK, width=width, joint="curve")

def draw(out):
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    y0, y1 = TOP, TOP + MAP_H
    d.rounded_rectangle([0, y0, W, y1], 40, fill=SEA)
    poly(d, NORTH, LAND); poly(d, EAST, LAND); poly(d, CRIMEA, LAND)
    # tapar los trazos de los bordes del cuadro (no son costa)
    d.rectangle([0, y0 - 8, W, y0 + 4], fill="white"); d.rectangle([W - 4, y0, W, y1], fill="white")
    d.line([(0, y0 + 2), (W, y0 + 2)], fill=INK, width=6); d.line([(0, y1), (W, y1)], fill=INK, width=6)
    im.save(out)

def crimea_mask(out, rgba):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [P(*p) for p in CRIMEA]; d.polygon(smooth(pts + [pts[0]]), fill=rgba); im.save(out)

if __name__ == "__main__":
    import sys; draw(sys.argv[1]); print(P(36.5, 45.3), P(36.67, 45.25), MAP_H)

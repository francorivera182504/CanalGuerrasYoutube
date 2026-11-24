"""Mapas reales (aprox.) de Finlandia 1939 y la URSS para el video 5, 1920x1080.
Vistas: 'north' (Finlandia entera + URSS) e 'isthmus' (istmo de Carelia / Ladoga).
Uso: from mapa_fi import View; v = View('north'); v.base('out.png'); v.P(lon, lat)
"""
import math
from PIL import Image, ImageDraw

W, H = 1920, 1080
SEA, SU, FI, OTH, LINE = (191, 227, 245), (244, 205, 200), (190, 212, 242), (236, 230, 214), (40, 40, 40)

# ---- costas y fronteras (lon, lat) ----
SWE_FI = [(24.15, 65.85), (23.65, 66.4), (23.9, 67.1), (23.5, 67.6), (22.4, 68.4), (21.0, 69.0), (20.55, 69.06)]
FI_NO = [(20.55, 69.06), (21.2, 69.3), (22.4, 68.7), (23.9, 68.8), (24.9, 68.6), (25.8, 69.0), (26.0, 69.7),
         (27.0, 69.95), (28.0, 70.08), (28.7, 69.7), (29.1, 69.2), (29.6, 69.4), (30.0, 69.65), (30.83, 69.79)]
FI_SU = [(29.95, 60.18), (30.55, 60.45), (31.85, 61.35), (32.0, 61.6), (32.8, 62.3), (31.9, 63.0), (31.0, 63.5),
         (30.6, 64.0), (30.0, 64.5), (30.1, 64.9), (29.7, 65.3), (29.9, 65.7), (30.1, 66.2), (29.6, 66.9),
         (29.1, 67.6), (29.4, 68.1), (28.8, 68.6), (29.6, 69.0), (31.0, 69.45), (32.1, 69.75)]
FI_WEST = [(22.95, 59.82), (22.27, 60.4), (21.4, 60.8), (21.5, 61.13), (21.6, 61.48), (21.37, 62.27), (21.6, 63.1),
           (23.13, 63.84), (24.48, 64.68), (25.47, 65.01), (25.2, 65.5), (24.15, 65.85)]
FI_GULF = [(29.95, 60.18), (29.3, 60.2), (28.6, 60.4), (28.75, 60.7), (27.9, 60.5), (26.9, 60.45), (25.9, 60.3),
           (24.94, 60.15), (24.0, 60.0), (23.3, 59.9), (22.95, 59.82)]
FINLAND = FI_WEST + SWE_FI[1:] + FI_NO[1:] + [(31.4, 69.85)] + FI_SU[::-1][1:] + FI_GULF[1:]

SCAND = ([(12.0, 57.0), (16.6, 57.0), (16.7, 58.4), (17.5, 58.8), (18.1, 59.3), (18.9, 59.8), (18.0, 60.4),
          (17.3, 60.7), (17.2, 61.7), (17.5, 62.4), (18.6, 63.2), (20.3, 63.7), (21.0, 64.3), (21.5, 65.0),
          (22.2, 65.6), (23.5, 65.8)] + SWE_FI + FI_NO[1:] +
         [(30.0, 70.0), (28.5, 70.5), (27.0, 70.95), (25.8, 71.1), (23.6, 70.6), (21.0, 70.2), (19.0, 69.8),
          (17.0, 69.0), (15.5, 68.3), (14.0, 67.2), (13.0, 66.2), (12.3, 65.0), (10.5, 64.0), (8.5, 63.4),
          (7.0, 62.6), (5.0, 61.8), (5.0, 60.0), (5.6, 59.0), (6.5, 58.1), (8.0, 58.1), (9.5, 58.9),
          (10.7, 59.9), (11.2, 59.1), (11.8, 58.4)])
MAIN = ([(21.3, 56.0), (21.4, 57.5), (22.6, 57.75), (23.6, 58.0), (23.5, 58.4), (23.4, 58.9), (23.9, 59.3),
         (24.75, 59.45), (25.9, 59.6), (27.0, 59.45), (28.0, 59.5), (28.8, 59.8), (29.5, 59.9), (30.25, 59.95),
         (30.0, 60.05)] + FI_SU +
        [(33.5, 69.35), (36.0, 69.1), (38.5, 68.5), (40.3, 68.0), (41.8, 68.6), (44.5, 68.6), (46.0, 68.0),
         (60.0, 68.4), (60.0, 50.0), (21.0, 50.0)])
BALTS_W = [(21.3, 56.0), (21.4, 57.5), (22.6, 57.75), (23.6, 58.0), (23.5, 58.4), (23.4, 58.9), (23.9, 59.3),
           (24.75, 59.45), (25.9, 59.6), (27.0, 59.45), (28.0, 59.5), (28.2, 59.0), (27.6, 57.9), (28.2, 56.2), (21.0, 55.8)]
WHITE_SEA = [(32.4, 67.1), (34.0, 66.7), (36.5, 66.25), (39.0, 66.2), (41.2, 66.6), (40.3, 68.0), (41.8, 68.6),
             (44.5, 68.6), (44.0, 67.2), (43.8, 66.4), (42.0, 65.7), (40.5, 64.6), (39.0, 65.0), (37.5, 64.8),
             (37.0, 64.3), (36.0, 64.0), (34.8, 64.5), (34.8, 65.3), (33.5, 66.0)]
LADOGA = [(30.0, 61.05), (30.7, 61.7), (31.5, 61.6), (32.3, 61.3), (32.9, 60.9), (32.6, 60.5), (32.0, 60.2),
          (31.2, 59.95), (30.9, 60.0), (30.5, 60.25), (30.3, 60.6), (30.1, 60.9)]
ONEGA = [(35.3, 62.9), (36.2, 62.6), (36.4, 61.8), (35.8, 61.2), (35.1, 60.9), (34.4, 61.1), (34.6, 61.8), (34.3, 62.4)]
NEW_BORDER = [(27.75, 60.53), (28.4, 60.9), (28.8, 61.15), (29.4, 61.4), (29.85, 61.85), (30.6, 62.15),
              (31.2, 62.5), (31.55, 62.9), (31.0, 63.5)]
CEDED_S = [(27.75, 60.53), (27.9, 60.5), (28.75, 60.7), (28.6, 60.4), (29.3, 60.2), (29.95, 60.18), (30.55, 60.45),
           (31.85, 61.35), (32.0, 61.6), (32.8, 62.3), (31.9, 63.0), (31.0, 63.5)] + NEW_BORDER[::-1][1:]
CEDED_SALLA = [(29.9, 65.7), (30.1, 66.2), (29.6, 66.9), (29.1, 67.0), (28.9, 66.5), (29.4, 65.95)]

CITY = {"HELSINKI": (24.94, 60.17), "VIIPURI": (28.73, 60.71), "LENINGRAD": (30.31, 59.94), "OULU": (25.47, 65.01),
        "SUOMUSSALMI": (28.9, 64.9), "RAATE": (29.75, 64.85), "KOLLAA": (31.6, 62.1), "SUMMA": (29.15, 60.55),
        "HANKO": (22.95, 59.82), "TERIJOKI": (29.7, 60.18), "MAINILA": (30.08, 60.16), "MOSCOW": (37.6, 55.75),
        "KUHMO": (29.5, 64.1), "SALLA": (28.7, 66.85)}

VIEWS = {"north": (4.0, 57.2, 80.0, 64.0), "isthmus": (24.5, 59.4, 360.0, 61.0)}  # lon0, lat0(bottom), px/deg lat, lat de coseno


def smooth(pts, it=2):
    for _ in range(it):
        n = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        pts = n
    return pts


def smooth_open(pts, it=2):
    for _ in range(it):
        n = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            n += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        n.append(pts[-1]); pts = n
    return pts


class View:
    def __init__(self, name):
        self.lon0, self.lat0, self.s, latc = VIEWS[name]
        self.k = math.cos(math.radians(latc)); self.name = name

    def P(self, lon, lat):
        return ((lon - self.lon0) * self.k * self.s, H - (lat - self.lat0) * self.s)

    def poly(self, pts):
        return [self.P(*p) for p in pts]

    def base(self, out, fin_color=FI, lw=4):
        im = Image.new("RGB", (W, H), SEA); d = ImageDraw.Draw(im)
        for pts, col in ((MAIN, SU), (BALTS_W, OTH), (SCAND, OTH), (FINLAND, fin_color)):
            d.polygon(self.poly(smooth(pts)), fill=col, outline=LINE)
        for pts in (FINLAND, SCAND, MAIN):
            d.line(self.poly(smooth(pts)) + [self.poly(smooth(pts))[0]], fill=LINE, width=lw, joint="curve")
        for pts in (WHITE_SEA, LADOGA, ONEGA):
            d.polygon(self.poly(smooth(pts)), fill=SEA)
        for pts in (WHITE_SEA, LADOGA, ONEGA):
            q = self.poly(smooth(pts)); d.line(q + [q[0]], fill=LINE, width=lw - 1, joint="curve")
        im.save(out); return im

    def overlay(self, pts, rgba, out, outline=None, lw=5, lakes=True):
        """Capa transparente con un polígono (p. ej. zona cedida). Recorta los lagos."""
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.polygon(self.poly(smooth(pts)), fill=rgba)
        if lakes:
            for lk in (LADOGA, ONEGA):
                d.polygon(self.poly(smooth(lk)), fill=(0, 0, 0, 0))
        if outline:
            q = self.poly(smooth(pts)); d.line(q + [q[0]], fill=outline, width=lw, joint="curve")
        im.save(out); return im

    def line_layer(self, pts, out, color=(200, 30, 30, 255), lw=8, dash=None):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        q = self.poly(smooth_open(pts))
        if dash:
            acc = 0
            for a, b in zip(q, q[1:]):
                L = math.dist(a, b); n = max(1, int(L / dash))
                for i in range(n):
                    if (acc + i) % 2 == 0:
                        t0, t1 = i / n, (i + 1) / n
                        d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=color, width=lw)
                acc += n
        else:
            d.line(q, fill=color, width=lw, joint="curve")
        im.save(out); return im


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for v in ("north", "isthmus"):
        V = View(v); im = V.base(f"{out}/map_{v}.png").convert("RGBA")
        im.alpha_composite(V.overlay(CEDED_S, (220, 40, 40, 150), f"{out}/_tmp.png"))
        d = ImageDraw.Draw(im)
        for n, (lo, la) in CITY.items():
            x, y = V.P(lo, la)
            if 0 < x < W and 0 < y < H:
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill="black"); d.text((x + 10, y - 8), n, fill="black")
        im.save(f"{out}/check_{v}.png")

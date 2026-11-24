"""Herramientas para Shorts animados en OpenReel (1080x1920).

Idea: cada elemento va en su propio PNG transparente de pantalla completa, colocado en (cx, cy).
En OpenReel se pone anchor=(cx/W, cy/H) y position=(cx-W/2, cy-H/2) + desplazamiento animado,
así escala y rotación ocurren alrededor del centro del elemento (comprobado el 22-nov-2026).
"""
import math, os
from collections import deque
from PIL import Image

W, H = 1080, 1920

# ---------------- recorte y composición ----------------
def cutout(src, thr=238):
    """Quita el fondo blanco conectado a los bordes (deja blancos interiores, p. ej. tanques)."""
    im = Image.open(src).convert("RGBA"); w, h = im.size; px = im.load()
    seen = bytearray(w * h); q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft(); i = y * w + x
        if seen[i]: continue
        seen[i] = 1
        r, g, b, a = px[x, y]
        if r >= thr and g >= thr and b >= thr:
            px[x, y] = (255, 255, 255, 0)
            if x > 0: q.append((x - 1, y))
            if x < w - 1: q.append((x + 1, y))
            if y > 0: q.append((x, y - 1))
            if y < h - 1: q.append((x, y + 1))
    bb = im.getbbox()
    return im.crop(bb) if bb else im

def place(el, cx, cy, width, out, flip=False, rotate=0):
    """Pega el elemento recortado centrado en (cx, cy) con ancho `width` en un lienzo transparente W x H."""
    e = el.transpose(Image.FLIP_LEFT_RIGHT) if flip else el
    r = width / e.width
    e = e.resize((max(1, int(e.width * r)), max(1, int(e.height * r))), Image.LANCZOS)
    if rotate: e = e.rotate(rotate, expand=True, resample=Image.BICUBIC)
    can = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    can.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
    can.save(out)
    return e.size

def bg_full(src, out, top_pad=None):
    """Fondo vertical a 1080 de ancho centrado sobre blanco 1080x1920. Devuelve (escala, offset_y)
    para convertir coordenadas de la imagen original a coordenadas del cuadro."""
    im = Image.open(src).convert("RGB"); r = W / im.width
    im = im.resize((W, int(im.height * r)), Image.LANCZOS)
    oy = (H - im.height) // 2 if top_pad is None else top_pad
    can = Image.new("RGB", (W, H), "white"); can.paste(im, (0, oy)); can.save(out)
    return r, oy

# ---------------- keyframes ----------------
class Anim:
    """Construye keyframes de una capa colocada en (cx, cy). Tiempos relativos al clip."""
    def __init__(self, cx, cy):
        self.cx, self.cy = cx, cy; self.k = []; self.n = 0
    def _add(self, t, prop, v, ez="linear"):
        self.n += 1
        self.k.append({"id": f"k{self.n}", "time": round(max(0, t), 3), "property": prop, "value": round(v, 4), "easing": ez})
    def pos(self, t, dx=0, dy=0, ez="linear"):
        self._add(t, "position.x", self.cx - W / 2 + dx, ez); self._add(t, "position.y", self.cy - H / 2 + dy, ez)
    def scale(self, t, sx, sy=None, ez="linear"):
        self._add(t, "scale.x", sx, ez); self._add(t, "scale.y", sx if sy is None else sy, ez)
    def rot(self, t, a, ez="linear"): self._add(t, "rotation", a, ez)
    def op(self, t, a, ez="linear"): self._add(t, "opacity", a, ez)
    def transform(self):
        return {"anchor": {"x": self.cx / W, "y": self.cy / H},
                "position": {"x": self.cx - W / 2, "y": self.cy - H / 2}, "fitMode": "contain"}

    # ---- recetas ----
    def pop_in(self, t, d=0.35, s=1.0):
        self.scale(t, 0.0, ez="easeOutBack"); self.scale(t + d, s, ez="easeOutBack")
    def pop_out(self, t, d=0.25, s=1.0):
        self.scale(t, s, ez="easeInBack"); self.scale(t + d, 0.0, ez="easeInBack")
    def flicker(self, t0, t1, period=0.16, amp=0.16, s=1.0, wobble=5):
        """Fuego: estira/encoge en vertical alrededor del anclaje y se tambalea."""
        t = t0; i = 0
        while t <= t1:
            up = i % 2 == 0
            self.scale(t, s * (0.94 if up else 1.04), s * (1 + amp if up else 1 - amp * 0.4), "easeInOutSine")
            self.rot(t, wobble if (i // 2) % 2 == 0 else -wobble, "easeInOutSine")
            t += period * (0.85 + 0.3 * ((i * 7) % 5) / 4); i += 1
    def bob(self, t0, t1, amp=10, period=1.6, dx=0, phase=0):
        t = t0; i = phase
        while t <= t1:
            self.pos(t, dx, amp if i % 2 == 0 else -amp, "easeInOutSine"); t += period / 2; i += 1
    def spin(self, t0, t1, a0, a1, ez="easeInOutCubic"):
        self.rot(t0, a0, ez); self.rot(t1, a1, ez)
    def move(self, t0, t1, d0, d1, ez="easeInOutCubic"):
        self.pos(t0, *d0, ez); self.pos(t1, *d1, ez)
    def pulse(self, t0, t1, period=0.7, lo=0.92, hi=1.08):
        t = t0; i = 0
        while t <= t1:
            self.scale(t, hi if i % 2 == 0 else lo, ez="easeInOutSine"); t += period / 2; i += 1
    def shake(self, t0, d=0.5, amp=14, step=0.05):
        t = t0; i = 0
        while t < t0 + d:
            f = 1 - (t - t0) / d
            self.pos(t, amp * f * (1 if i % 2 == 0 else -1), amp * f * (0.6 if i % 3 == 0 else -0.6)); t += step; i += 1
        self.pos(t0 + d, 0, 0)

"""Cuadros de estilo (mapa / 3D / personaje) para que Franco apruebe el look antes de producir."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "..", "..", "..", "Imagenes", "Shorts", "S03", "capas")
OUT = os.path.join(HERE, "..", "..", "..", "Imagenes", "Shorts", "S03", "estilo"); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
FONT = r"C:\Windows\Fonts\ariblk.ttf"

def cutout(path, thr=245):
    """Recorta el fondo blanco por relleno desde los bordes."""
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).copy()
    white = (a[..., :3] >= thr).all(-1)
    lab, _ = ndimage.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(border))
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = np.asarray(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2)))
    a[..., 3] = alpha
    out = Image.fromarray(a); return out.crop(out.getbbox())

def text(can, s, y, size, fill=(255, 255, 255), stroke=10):
    d = ImageDraw.Draw(can); f = ImageFont.truetype(FONT, size)
    bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))

def neon(can, pts, col, width=7, blur=16):
    line = Image.new("RGBA", can.size); d = ImageDraw.Draw(line)
    d.line(pts + [pts[0]], fill=col + (255,), width=width, joint="curve")
    glow = line.filter(ImageFilter.GaussianBlur(blur))
    can = Image.alpha_composite(can, glow); can = Image.alpha_composite(can, glow)
    can = Image.alpha_composite(can, line)
    thin = Image.new("RGBA", can.size); ImageDraw.Draw(thin).line(pts + [pts[0]], fill=(255, 255, 255, 220), width=2, joint="curve")
    return Image.alpha_composite(can, thin)

# ---------- 1) MAPA ----------
T = os.path.join(HERE, "terreno"); meta = json.load(open(os.path.join(T, "meta.json"))); rings = json.load(open(os.path.join(T, "rings.json")))
src = Image.open(os.path.join(T, "color.png")).convert("RGB"); k = src.width / 1024
cx, cy = meta["center_px"]; mpp = meta["mpp"]
# recorte vertical centrado en Alesia: ancho 600 px de terreno (≈7,7 km)
wpx = 600; hpx = wpx * H / W
box = (int((cx - wpx / 2) * k), int((cy - hpx / 2) * k), int((cx + wpx / 2) * k), int((cy + hpx / 2) * k))
pad = Image.new("RGB", (2048 * 2, 2048 * 2), (20, 40, 30)); pad.paste(src, (1024, 1024))
base = pad.crop(tuple(b + 1024 for b in box)).resize((W, H), Image.LANCZOS)
base = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(base).enhance(0.9)).enhance(1.15)).enhance(0.72)
can = base.convert("RGBA")
# viñeta
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse((-300, -200, W + 300, H + 200), fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(160)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 170)); dark.putalpha(Image.eval(vig, lambda v: 170 - int(v * 170 / 255)))
can = Image.alpha_composite(can, dark)
s = W / wpx
def P(x, y): return ((cx + x / mpp - (cx - wpx / 2)) * s, (cy - y / mpp - (cy - hpx / 2)) * s)
# oppidum (galos) en azul translúcido
op = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(op)
ocx, ocy = P(0, 0); d.ellipse((ocx - 150, ocy - 62, ocx + 150, ocy + 62), fill=(70, 150, 255, 90))
can = Image.alpha_composite(can, op)
can = neon(can, [P(*p) for p in rings["inner"]], (255, 70, 40))
can = neon(can, [P(*p) for p in rings["outer"]], (255, 40, 30), width=9, blur=20)
def icon(name, size, xy):
    im = cutout(os.path.join(CAP, name)); im.thumbnail((size, size))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda v: v * 0.5)); sh = sh.filter(ImageFilter.GaussianBlur(8))
    can.alpha_composite(sh, (int(xy[0] - im.width / 2 + 6), int(xy[1] - im.height / 2 + 10)))
    can.alpha_composite(im, (int(xy[0] - im.width / 2), int(xy[1] - im.height / 2)))
if os.path.exists(os.path.join(CAP, "ic_gaul.png")): icon("ic_gaul.png", 150, (ocx, ocy))
if os.path.exists(os.path.join(CAP, "ic_roman.png")):
    ix, iy = P(*rings["inner"][300]); ox, oy = P(*rings["outer"][300])
    icon("ic_roman.png", 120, ((ix + ox) / 2, (iy + oy) / 2))
d = ImageDraw.Draw(can); f = ImageFont.truetype(FONT, 46)
d.rounded_rectangle((40, 60, 250, 140), 18, fill=(0, 0, 0, 150)); d.text((62, 72), "52 BC", font=f, fill=(255, 255, 255))
text(can, "2 WALLS", 230, 150, fill=(255, 214, 40), stroke=12)
text(can, "surrounded", 1380, 92)
can.convert("RGB").save(os.path.join(OUT, "estilo_1_mapa.jpg"), quality=92)

# ---------- 2) 3D ----------
r3 = os.path.join(HERE, "render3d", "still_0150.png")
if os.path.exists(r3):
    c3 = Image.open(r3).convert("RGBA")
    text(c3, "≈15 KM", 230, 170, fill=(255, 214, 40), stroke=12)
    text(c3, "INNER LINE", 430, 80)
    c3.convert("RGB").save(os.path.join(OUT, "estilo_2_3d.jpg"), quality=92)

# ---------- 3) PERSONAJE ----------
bgp = os.path.join(CAP, "bg_relief_army.png")
if not os.path.exists(bgp): bgp = os.path.join(CAP, "bg_rampart.png")
bg = Image.open(bgp).convert("RGB"); bg = bg.resize((W, int(bg.height * W / bg.width)), Image.LANCZOS)
c = Image.new("RGBA", (W, H)); c.paste(bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H)) if bg.height >= H else bg.resize((W, H)))
ch = cutout(os.path.join(CAP, "char_B_worried.png" if os.path.exists(os.path.join(CAP, "char_B_worried.png")) else "char_A_neutral.png"))
ch = ch.resize((int(ch.width * 1250 / ch.height), 1250), Image.LANCZOS)
sh = Image.new("RGBA", (W, H)); ImageDraw.Draw(sh).ellipse((W / 2 - 230, H - 175, W / 2 + 230, H - 95), fill=(0, 0, 0, 110))
c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(18)))
c.alpha_composite(ch, (int(W / 2 - ch.width / 2), H - 130 - ch.height))
text(c, "RELIEF ARMY", 230, 120, fill=(255, 214, 40), stroke=12)
text(c, "was coming", 1500, 92)
c.convert("RGB").save(os.path.join(OUT, "estilo_3_personaje.jpg"), quality=92)
print("ok")

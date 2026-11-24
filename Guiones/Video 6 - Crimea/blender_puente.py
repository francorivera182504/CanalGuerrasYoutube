"""Maqueta 3D del puente de Kerch (tramo del arco navegable) — Video 6 Crimea.
Uso: blender -b -P blender_puente.py -- --shot hook|fly|oct22|nov26 [--frames N] [--fall F] [--still F] [--out carpeta]
1 u = 10 m. El puente va en X; vial en y=0 (lado Azov, norte = +y), ferroviario en y=-3.4.
--fall F: cuadro en que el arco vial cae (hook/nov26). Los cuadros previos ya muestran el arco cediendo.
"""
import bpy, math, os, sys, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
SHOT = arg("--shot", "hook"); NF = int(arg("--frames", 120)); FALL = float(arg("--fall", 27))
OUT = arg("--out", os.path.join(HERE, "render3d", SHOT)); os.makedirs(OUT, exist_ok=True)
RES = float(arg("--res", 1.0))
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = int(1920 * RES), int(1080 * RES)
sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
ee = sc.eevee
for k, v in (("taa_render_samples", 48), ("use_raytracing", True), ("use_shadows", True), ("use_gtao", True)):
    try: setattr(ee, k, v)
    except Exception: pass

# ---------------- materiales ----------------
def mat(name, rgb, rough=0.6, metal=0.0, emit=0.0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*(ecol or rgb), 1); b.inputs["Emission Strength"].default_value = emit
    return m
CONC = mat("Hormigon", (0.42, 0.43, 0.46), 0.85)
DECK = mat("Tablero", (0.16, 0.17, 0.19), 0.7)
STEEL = mat("Acero", (0.62, 0.66, 0.72), 0.35, 0.6)
LAMP = mat("Lampara", (1.0, 0.85, 0.55), 0.5, 0, 9.0)
NEON_ROAD = mat("NeonVial", (1.0, 0.55, 0.15), 0.4, 0, 4.0)
NEON_RAIL = mat("NeonFerro", (0.2, 0.6, 1.0), 0.4, 0, 4.0)
TRUCK = mat("Camion", (0.75, 0.75, 0.72), 0.5)
CAB = [mat("Cab%d" % i, c, 0.45) for i, c in enumerate(((0.7, 0.1, 0.08), (0.1, 0.25, 0.6), (0.85, 0.85, 0.85), (0.15, 0.4, 0.15)))]
TANK = mat("Cisterna", (0.08, 0.08, 0.09), 0.5, 0.3)
LOCO = mat("Locomotora", (0.12, 0.35, 0.22), 0.5)
HEAD = mat("Faro", (1, 0.95, 0.8), 0.5, 0, 12)
TAIL = mat("Piloto", (1, 0.1, 0.05), 0.5, 0, 8)
LAND = mat("Costa", (0.10, 0.12, 0.10), 0.95)

water = bpy.data.materials.new("Agua"); water.use_nodes = True; nt = water.node_tree
b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.01, 0.035, 0.06, 1)
b.inputs["Roughness"].default_value = 0.08
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 2.2; noise.inputs["Detail"].default_value = 8
coord = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 3, 1)
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.05
nt.links.new(coord.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
# las olas se mueven
mp.inputs["Location"].default_value = (0, 0, 0)
mp.inputs["Location"].keyframe_insert("default_value", frame=1)
mp.inputs["Location"].default_value = (0.5, 0.2, NF / 300)
mp.inputs["Location"].keyframe_insert("default_value", frame=NF)

# ---------------- utilidades ----------------
def box(name, loc, size, m, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def cyl(name, p0, p1, r, m, parent=None, verts=12):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object; o.name = name; o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized()); o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def tube(name, pts, r, m, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts): p.co = (*v, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def empty(name, loc):
    o = bpy.data.objects.new(name, None); o.location = loc; sc.collection.objects.link(o); return o

# ---------------- puente ----------------
L = 11.35          # medio vano del arco (227 m)
X0, X1 = -95, 95
def zdeck(x):
    a = abs(x)
    if a <= L: return 3.6
    k = min(1.0, (a - L) / 60.0); return 3.6 - 1.7 * (k * k * (3 - 2 * k))
DECKS = {"road": (0.0, 2.2, NEON_ROAD), "rail": (-3.4, 1.3, NEON_RAIL)}
ARCH = {k: empty("Arco_" + k, (-L, y, 3.6)) for k, (y, w, n) in DECKS.items()}
SPAN22 = empty("Vano2022", (30.0, 0.55, zdeck(30)))          # mitad norte de la calzada, vanos 30–41
SEG = 5.5
xs = [-L] + [-L - SEG * i for i in range(1, 16)] + [L + SEG * i for i in range(1, 16)] + [L]
xs = sorted(set(round(x, 2) for x in xs if X0 <= x <= X1))
for key, (y, w, neon) in DECKS.items():
    for xa, xb in zip(xs, xs[1:]):
        za, zb = zdeck(xa), zdeck(xb); par = None
        if abs(xa + L) < 1e-3 and abs(xb - L) < 1e-3: par = ARCH[key]
        if key == "road" and 30 <= xa < 41: par = SPAN22
        o = box(f"Tab_{key}_{xa}", ((xa + xb) / 2, y, (za + zb) / 2 - 0.18), (xb - xa + 0.02, w, 0.36), DECK)
        o.rotation_euler[1] = -math.atan2(zb - za, xb - xa)
        if par: o.parent = par; o.matrix_parent_inverse = par.matrix_world.inverted()
        for s in (-1, 1):
            n = cyl(f"Neon_{key}_{xa}_{s}", (xa, y + s * (w / 2 - 0.05), za + 0.05), (xb, y + s * (w / 2 - 0.05), zb + 0.05), 0.035, neon, verts=6)
            if par: n.parent = par; n.matrix_parent_inverse = par.matrix_world.inverted()
        if key == "road":
            for xl in (xa + 1.2, xa + (xb - xa) / 2 + 1.2):
                if xl > xb: continue
                zl = za + (zb - za) * (xl - xa) / (xb - xa)
                for s in (-1, 1):
                    p = cyl(f"Poste_{xl}_{s}", (xl, s * 1.05, zl), (xl, s * 1.05, zl + 0.9), 0.025, STEEL, verts=6)
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(xl, s * 0.95, zl + 0.9), segments=8, ring_count=6)
                    lp = bpy.context.object; lp.data.materials.append(LAMP)
                    if par:
                        for q in (p, lp): q.parent = par; q.matrix_parent_inverse = par.matrix_world.inverted()
    # pilas
    for x in xs:
        z = zdeck(x); big = abs(abs(x) - L) < 1e-3
        for s in (-1, 1):
            cyl(f"Pila_{key}_{x}_{s}", (x, y + s * w * 0.28, -3), (x, y + s * w * 0.28, z - 0.36), 0.42 if big else 0.2, CONC)
        box(f"Cabezal_{key}_{x}", (x, y, z - 0.5), (0.9 if big else 0.5, w * 0.95, 0.3), CONC)
        if big: box(f"Encepado_{key}_{x}", (x, y, -0.1), (2.2, w + 1.4, 0.6), CONC)
    # arco: dos costillas parabólicas + péndolas + riostras
    rise = 4.6 if key == "road" else 4.2
    ribs = []
    for s in (-1, 1):
        pts = [(x, y + s * (w / 2 + 0.1), 3.6 + rise * (1 - (x / L) ** 2)) for x in [-L + 2 * L * i / 40 for i in range(41)]]
        t = tube(f"Costilla_{key}_{s}", pts, 0.2, STEEL, ARCH[key]); t.matrix_parent_inverse = ARCH[key].matrix_world.inverted(); ribs.append(pts)
        for i in range(2, 39, 2):
            x, yy, z = pts[i]
            c = cyl(f"Pendola_{key}_{s}_{i}", (x, yy, 3.6), (x, yy, z), 0.03, STEEL, verts=6)
            c.parent = ARCH[key]; c.matrix_parent_inverse = ARCH[key].matrix_world.inverted()
    for i in range(8, 33, 4):
        a, bb = ribs[0][i], ribs[1][i]
        c = cyl(f"Riostra_{key}_{i}", a, bb, 0.08, STEEL, verts=8); c.parent = ARCH[key]; c.matrix_parent_inverse = ARCH[key].matrix_world.inverted()

# ---------------- agua, costas, cielo ----------------
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0)); wtr = bpy.context.object; wtr.data.materials.append(water)
for sx in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(location=(sx * 170, 0, -0.5)); c = bpy.context.object; c.scale = (60, 260, 0.62); c.data.materials.append(LAND)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(78), 0, math.radians(-120)))
sun = bpy.context.object; sun.data.energy = 1.6; sun.data.color = (1.0, 0.7, 0.5); sun.data.angle = math.radians(2)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(40), 0, math.radians(60)))
fill = bpy.context.object; fill.data.energy = 0.35; fill.data.color = (0.5, 0.65, 1.0)
w = bpy.data.worlds.new("Cielo"); sc.world = w; w.use_nodes = True; wn = w.node_tree
sky = wn.nodes.new("ShaderNodeTexSky")
for k, v in (("sky_type", "MULTIPLE_SCATTERING"), ("sky_type", "NISHITA")):
    try: sky.sky_type = v; break
    except Exception: pass
try: sky.sun_elevation = math.radians(1.5); sky.sun_rotation = math.radians(150); sky.sun_size = math.radians(2)
except Exception as e: print("sky", e)
wn.links.new(sky.outputs["Color"], wn.nodes["Background"].inputs["Color"])
wn.nodes["Background"].inputs["Strength"].default_value = float(arg("--sky", 0.12))
# ---------------- vehículos ----------------
TRUCKS = []
for i in range(14):
    lane = random.choice((-0.55, -0.2, 0.2, 0.55)); d = 1 if lane > 0 else -1
    root = empty(f"Camion{i}", (0, lane, 0)); x0 = random.uniform(X0, X1)
    cm = random.choice(CAB)
    b1 = box("tr", (0, 0, 0.17), (0.9, 0.24, 0.28), TRUCK, root); b2 = box("cab", (0.56 * d, 0, 0.14), (0.22, 0.24, 0.22), cm, root)
    box("faro", (0.68 * d, 0, 0.1), (0.02, 0.2, 0.04), HEAD, root); box("pil", (-0.46 * d, 0, 0.1), (0.02, 0.2, 0.04), TAIL, root)
    TRUCKS.append((root, x0, d, random.uniform(0.5, 0.7)))
TRAIN = empty("Tren", (0, -3.4, 0))
box("loco", (0, 0, 0.3), (1.6, 0.32, 0.42), LOCO, TRAIN); box("faroT", (0.81, 0, 0.3), (0.02, 0.2, 0.06), HEAD, TRAIN)
for j in range(1, 16):
    xc = -j * 1.25
    cyl(f"cist{j}", (xc - 0.55, 0, 0.32), (xc + 0.55, 0, 0.32), 0.17, TANK, TRAIN, 14)
    box(f"chasis{j}", (xc, 0, 0.12), (1.15, 0.26, 0.08), TANK, TRAIN)
TRAIN_X0 = {"hook": -40, "fly": -70, "oct22": 47, "nov26": -60}.get(SHOT, -60); TRAIN_V = 0.0 if SHOT == "oct22" else 0.12

def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def on_frame(scn, *a):
    f = scn.frame_current
    for root, x0, d, v in TRUCKS:
        x = x0 + d * v * f
        x = X0 + (x - X0) % (X1 - X0)
        if SHOT in ("hook", "nov26") and -L - 1 < x < L + 1: x = -L - 1.5 if d > 0 else L + 1.5   # nadie sobre el arco
        if SHOT == "oct22" and 29 < x < 42 and root.location.y > 0: x = 28.5
        root.location.x = x; root.location.z = zdeck(x); root.rotation_euler[2] = 0
    TRAIN.location.x = TRAIN_X0 + TRAIN_V * f; TRAIN.location.z = zdeck(TRAIN.location.x) if SHOT != "hook" else zdeck(TRAIN.location.x)
    A = ARCH["road"]
    if SHOT in ("hook", "nov26"):
        pre = 0.3 + 0.7 * smooth(f / FALL); k = smooth((f - FALL + 4) / 26.0)
        sag = 0.45 * pre
        A.location = Vector((-L + 1.5 * k, 0.0 + 0.6 * k, 3.6 - sag - 9.5 * k * k))
        A.rotation_euler = (math.radians(-6 * k), math.radians(4.0 * pre + 14 * k), math.radians(3 * k))
    if SHOT == "oct22":
        k = smooth((f - FALL) / 22.0)
        SPAN22.location = Vector((30.0, 0.55 + 0.3 * k, zdeck(30) - 2.6 * k))
        SPAN22.rotation_euler = (math.radians(-10 * k), math.radians(-11 * k), 0)
bpy.app.handlers.frame_change_pre.append(on_frame)

# ---------------- efectos 3D: agua, fuego, humo ----------------
from mathutils import Matrix
try:
    ee.volumetric_tile_size = "4"; ee.volumetric_samples = 64; ee.volumetric_end = 250
except Exception: pass
sc.render.use_motion_blur = True
try: sc.render.motion_blur_shutter = 0.5
except Exception: pass

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    return m, nt, nt.nodes["Material Output"]

def vol_mat(name, col, dens, emit=0.0, ecol=None, noise_scale=2.5):
    """Volumen suave: densidad = falloff radial × ruido (las instancias son esferas de radio 1)."""
    m, nt, out = node_mat(name); N = nt.nodes.new; Lk = nt.links.new
    pv = N("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    if emit:
        pv.inputs["Emission Strength"].default_value = emit; pv.inputs["Emission Color"].default_value = (*(ecol or col), 1)
    tc = N("ShaderNodeTexCoord"); ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    mr = N("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 1.0; mr.inputs["From Max"].default_value = 0.2
    nz = N("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 6
    m1 = N("ShaderNodeMath"); m1.operation = "MULTIPLY"; m2 = N("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = dens
    pw = N("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
    Lk(tc.outputs["Object"], ln.inputs[0]); Lk(ln.outputs["Value"], mr.inputs["Value"])
    Lk(tc.outputs["Object"], nz.inputs["Vector"]); Lk(nz.outputs["Fac"], pw.inputs[0])
    Lk(mr.outputs["Result"], m1.inputs[0]); Lk(pw.outputs["Value"], m1.inputs[1]); Lk(m1.outputs["Value"], m2.inputs[0])
    fv = N("ShaderNodeValue"); fv.name = "Fade"; fv.outputs[0].default_value = 1.0
    m3 = N("ShaderNodeMath"); m3.operation = "MULTIPLY"; Lk(m2.outputs["Value"], m3.inputs[0]); Lk(fv.outputs[0], m3.inputs[1])
    Lk(m3.outputs["Value"], pv.inputs["Density"]); Lk(pv.outputs["Volume"], out.inputs["Volume"])
    if emit:   # la emisión del Principled Volume no depende de la densidad: hay que multiplicarla
        me = N("ShaderNodeMath"); me.operation = "MULTIPLY"; me.inputs[1].default_value = emit / max(dens, 1e-3)
        Lk(m3.outputs["Value"], me.inputs[0]); Lk(me.outputs[0], pv.inputs["Emission Strength"])
    return m
def fade(m, keys):
    v = m.node_tree.nodes["Fade"].outputs[0]
    for f, x in keys: v.default_value = x; v.keyframe_insert("default_value", frame=f)

SPRAY = mat("Espuma", (0.85, 0.92, 1.0), 0.25, 0, 0.35, (0.75, 0.85, 1.0))
SPRAY.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.35
FLAME = mat("Llama", (1.0, 0.45, 0.08), 0.5, 0, 18.0, (1.0, 0.42, 0.06))
EMBER = mat("Brasa", (1.0, 0.6, 0.2), 0.5, 0, 30.0, (1.0, 0.55, 0.15))
DEBRIS = mat("Escombro", (0.08, 0.08, 0.08), 0.9)
MIST = vol_mat("Bruma", (0.97, 0.98, 1.0), 11.0, 0.18, (0.85, 0.9, 1.0), 2.6)
SMOKE = vol_mat("Humo", (0.06, 0.06, 0.06), 12.0, noise_scale=1.5)
SMOKE_LIT = vol_mat("HumoFuego", (0.1, 0.08, 0.07), 10.0, 0.5, (1.0, 0.35, 0.05), 1.5)

def inst(name, m, kind="ico", sub=2):
    if kind == "ico": bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=(0, 0, -300))
    else: bpy.ops.mesh.primitive_cube_add(size=1.4, location=(0, 0, -300))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    if kind == "ico": bpy.ops.object.shade_smooth()
    return o
I_DROP = inst("Gota", SPRAY, sub=1); I_BLOB = inst("Masa", SPRAY, sub=2); I_MIST = inst("BrumaI", MIST, sub=3)
I_SMOKE = inst("HumoI", SMOKE, sub=3); I_SMOKEF = inst("HumoFI", SMOKE_LIT, sub=3); I_FLAME = inst("LlamaI", FLAME, sub=1)
I_EMBER = inst("BrasaI", EMBER, sub=1); I_DEB = inst("EscombroI", DEBRIS, "cube")
FOAMM = mat("EspumaAgua", (0.62, 0.68, 0.72), 0.6)
I_FOAM = inst("EspumaI", FOAMM, sub=2); I_FOAM.scale = (1, 1, 0.12)
bpy.ops.object.select_all(action="DESELECT"); I_FOAM.select_set(True); bpy.context.view_layer.objects.active = I_FOAM
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def emitter(name, loc, sx, sy, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = (sx, sy, 1)
    o.show_instancer_for_render = False; o.show_instancer_for_viewport = False
    if parent: o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

SEED = [1]
def psys(o, ins, count, f0, f1, life, vel, rnd, size, srand=0.6, grav=1.0, drag=0.0, up=0.0, spin=True, lrand=0.4):
    o.modifiers.new("ps%d" % SEED[0], "PARTICLE_SYSTEM"); p = o.particle_systems[-1]; p.seed = SEED[0]; SEED[0] += 1
    s = p.settings; s.count = int(count); s.frame_start = f0; s.frame_end = max(f0 + 0.01, f1)
    s.lifetime = life; s.lifetime_random = lrand; s.emit_from = "FACE"; s.use_emit_random = True
    s.normal_factor = vel; s.factor_random = rnd; s.object_align_factor = (0, 0, up)
    s.render_type = "OBJECT"; s.instance_object = ins; s.particle_size = size; s.size_random = srand
    s.physics_type = "NEWTON"; s.effector_weights.gravity = grav; s.drag_factor = drag; s.display_method = "DOT"
    if spin:
        s.use_rotations = True; s.rotation_mode = "NONE"; s.phase_factor_random = 2.0
        s.angular_velocity_mode = "RAND"; s.angular_velocity_factor = 4.0
    return s

def flicker_light(loc, col, e0, f0, f1, parent=None, rad=1.5, peak=None):
    bpy.ops.object.light_add(type="POINT", location=loc); L_ = bpy.context.object; L_.data.color = col; L_.data.shadow_soft_size = rad
    if parent: L_.parent = parent; L_.matrix_parent_inverse = parent.matrix_world.inverted()
    rnd = random.Random(int(loc[0] * 100))
    L_.data.energy = 0; L_.data.keyframe_insert("energy", frame=max(1, f0 - 1))
    for f in range(int(f0), int(f1) + 1, 2):
        e = e0 * rnd.uniform(0.6, 1.2)
        if peak and f - f0 < peak[1]: e = peak[0] * (1 - (f - f0) / peak[1]) + e
        L_.data.energy = e; L_.data.keyframe_insert("energy", frame=f)
    return L_

def arch_point(f, lx):
    """Posición mundial del punto local (lx,0,0) del arco vial en el cuadro f (misma fórmula que on_frame)."""
    pre = 0.3 + 0.7 * smooth(f / FALL); k = smooth((f - FALL + 4) / 26.0); sag = 0.45 * pre
    loc = Vector((-L + 1.5 * k, 0.6 * k, 3.6 - sag - 9.5 * k * k))
    rot = (math.radians(-6 * k), math.radians(4.0 * pre + 14 * k), math.radians(3 * k))
    from mathutils import Euler
    return Matrix.LocRotScale(loc, Euler(rot), None) @ Vector((lx, 0, 0))

def mist_domain(c, hx, f0, inten):
    """Un solo volumen de bruma (sin bolas): cubo con densidad = máscara elipsoidal suave × ruido 4D animado."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=c); d = bpy.context.object; d.name = "BrumaVol"
    m, nt, out = node_mat("BrumaVolM"); N = nt.nodes.new; Lk = nt.links.new
    pv = N("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.97, 0.98, 1.0, 1)
    tc = N("ShaderNodeTexCoord"); ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    mr = N("ShaderNodeMath"); mr.operation = "SUBTRACT"; mr.use_clamp = True; mr.inputs[0].default_value = 1.0
    pw = N("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.2
    nz = N("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.6
    gp = N("ShaderNodeMath"); gp.operation = "MULTIPLY_ADD"; gp.use_clamp = True; gp.inputs[1].default_value = 3.0; gp.inputs[2].default_value = -1.26
    m1 = N("ShaderNodeMath"); m1.operation = "MULTIPLY"; m2 = N("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = 12.0 * inten
    fv = N("ShaderNodeValue")
    m3 = N("ShaderNodeMath"); m3.operation = "MULTIPLY"
    cen = N("ShaderNodeVectorMath"); cen.operation = "MULTIPLY_ADD"; cen.inputs[1].default_value = (2, 2, 2); cen.inputs[2].default_value = (-1, -1, -1)
    cen.inputs[1].default_value = (1, 1, 1); cen.inputs[2].default_value = (0, 0, 0)
    Lk(tc.outputs["Object"], cen.inputs[0]); Lk(cen.outputs["Vector"], ln.inputs[0])
    Lk(ln.outputs["Value"], mr.inputs[1]); Lk(mr.outputs[0], pw.inputs[0])
    st_ = N("ShaderNodeVectorMath"); st_.operation = "MULTIPLY"; st_.inputs[1].default_value = (hx / 2.0, 1.4, 2.2)
    Lk(tc.outputs["Object"], st_.inputs[0]); Lk(st_.outputs["Vector"], nz.inputs["Vector"]); Lk(nz.outputs["Fac"], gp.inputs[0])
    Lk(pw.outputs["Value"], m1.inputs[0]); Lk(gp.outputs[0], m1.inputs[1]); Lk(m1.outputs["Value"], m2.inputs[0])
    Lk(m2.outputs["Value"], m3.inputs[0]); Lk(fv.outputs[0], m3.inputs[1]); Lk(m3.outputs["Value"], pv.inputs["Density"])
    Lk(pv.outputs["Volume"], out.inputs["Volume"]); d.data.materials.append(m)
    v = fv.outputs[0]; W_ = nz.inputs["W"]
    for f, val in ((f0 - 1, 0.0), (f0 + 2, 1.0), (f0 + 40, 0.75), (NF + 1, 0.3)): v.default_value = val; v.keyframe_insert("default_value", frame=f)
    W_.default_value = 0.0; W_.keyframe_insert("default_value", frame=f0); W_.default_value = (NF - f0) / 45; W_.keyframe_insert("default_value", frame=NF)
    for f, sz in ((f0 - 1, (hx * 0.8, 1.0, 0.4)), (f0 + 4, (hx, 1.8, 3.4)), (f0 + 14, (hx * 1.05, 2.5, 6.0)), (f0 + 45, (hx * 1.12, 3.4, 6.6)), (NF + 1, (hx * 1.25, 4.4, 6.8))):
        d.scale = sz; d.keyframe_insert("scale", frame=f)
    for fc in d.animation_data.action.fcurves if hasattr(d.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"
    return d

def water_splash(intensity=1.0):
    """Impacto del arco: por tramo, cuando el tablero toca el agua -> chorro, masa blanca, bruma y espuma."""
    NSEG = 8; hits = []
    for i in range(NSEG):
        lx = 2 * L * (i + 0.5) / NSEG
        for f in range(1, NF + 1):
            p = arch_point(f, lx)
            if p.z < 0.35: hits.append((f, p)); break
    print("impactos", [(f, round(p.x, 1)) for f, p in hits])
    f0 = min(f for f, p in hits); xs_ = [p.x for f, p in hits]
    mist_domain(((min(xs_) + max(xs_)) / 2, 0.4, 0.0), (max(xs_) - min(xs_)) / 2 + 2.5, f0, intensity)
    rr = random.Random(11)
    for i, (f, p) in enumerate(hits):
        o = emitter(f"Splash{i}", (p.x, p.y, 0.05), 2 * L / NSEG * 1.1, 2.4)
        q = intensity * rr.uniform(0.6, 1.4) * (1.25 if i >= NSEG // 2 else 1.0); h = rr.uniform(0.8, 1.3)
        psys(o, I_DROP, 3500 * q, f, f + 6, 70, 8.0 * h, 2.5, 0.022, 0.7, 1.0, 0.2)        # gotas finas (con desenfoque)
        psys(o, I_DROP, 1200 * q, f, f + 4, 70, 9.5 * h, 1.5, 0.03, 0.6, 1.0, 0.35)       # columna alta
        psys(o, I_DROP, 900 * q, f + 1, f + 9, 60, 3.5, 4.0, 0.02, 0.6, 1.0, 0.1)          # abanico bajo
        fo = emitter(f"Foam{i}", (p.x, p.y, 0.02), 2 * L / NSEG * 1.5, 3.6)
        psys(fo, I_FOAM, 1400 * q, f + 3, f + 30, 400, 0.0, 0.5, 0.07, 0.8, 0.0, 3.0, spin=False, lrand=0)
    return hits

def vol_shape(name, loc, dens, col, shape="ball", emit=0.0, ecol=(1.0, 0.4, 0.08), taper=(0.5, 0.5), ptop=1.0,
              speed=0.0, nscale=1.2, stretch=(1, 1, 1), dens_keys=None, emit_keys=None, scale_keys=None, parent=None, gate=(0.38, 3.2)):
    """Volumen procedural (Eevee). shape='ball' (elipsoide) o 'column' (columna que se abre o afina con la altura).
    Densidad = máscara × ruido 4D que sube; la emisión se multiplica por la máscara (si no, ilumina toda la caja)."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc); d = bpy.context.object; d.name = name
    if parent: d.parent = parent; d.matrix_parent_inverse = parent.matrix_world.inverted()
    m, nt, out = node_mat(name + "M"); N = nt.nodes.new; Lk = nt.links.new
    def mth(op, a_=None, b_=None, clamp=False, c_=None):
        n = N("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i_, v_ in enumerate((a_, b_, c_)):
            if v_ is None: continue
            if isinstance(v_, (int, float)): n.inputs[i_].default_value = v_
            else: Lk(v_, n.inputs[i_])
        return n.outputs[0]
    tc = N("ShaderNodeTexCoord"); ob = tc.outputs["Object"]
    sp = N("ShaderNodeSeparateXYZ"); Lk(ob, sp.inputs[0]); X, Y, Z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    if shape == "ball":
        ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"; Lk(ob, ln.inputs[0])
        mask = mth("POWER", mth("SUBTRACT", 1.0, ln.outputs["Value"], True), 1.8)
    else:
        h = mth("MULTIPLY_ADD", Z, 0.5, False, 0.5)                      # 0 abajo, 1 arriba
        tap = mth("MULTIPLY_ADD", h, taper[1], False, taper[0])
        r = mth("DIVIDE", mth("SQRT", mth("ADD", mth("MULTIPLY", X, X), mth("MULTIPLY", Y, Y))), tap)
        mr = mth("POWER", mth("SUBTRACT", 1.0, r, True), 1.5)
        top = mth("POWER", mth("SUBTRACT", 1.0, h, True), ptop)
        bot = mth("MULTIPLY", h, 6.0, True)
        mask = mth("MULTIPLY", mth("MULTIPLY", mr, top), bot)
    st_ = N("ShaderNodeVectorMath"); st_.operation = "MULTIPLY"; st_.inputs[1].default_value = stretch; Lk(ob, st_.inputs[0])
    off = N("ShaderNodeVectorMath"); off.operation = "ADD"; Lk(st_.outputs["Vector"], off.inputs[0])
    nz = N("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = nscale
    nz.inputs["Detail"].default_value = 10; nz.inputs["Roughness"].default_value = 0.62; Lk(off.outputs["Vector"], nz.inputs["Vector"])
    g = mth("MULTIPLY_ADD", nz.outputs["Fac"], gate[1], True, -gate[0] * gate[1])
    mg = mth("MULTIPLY", mask, g)
    fv = N("ShaderNodeValue"); dv = mth("MULTIPLY", mth("MULTIPLY", mg, dens), fv.outputs[0])
    pv = N("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1); Lk(dv, pv.inputs["Density"])
    if emit:
        ev_ = N("ShaderNodeValue"); pv.inputs["Emission Color"].default_value = (*ecol, 1)
        Lk(mth("MULTIPLY", mg, ev_.outputs[0]), pv.inputs["Emission Strength"])
        for f, v in (emit_keys or ((1, emit),)): ev_.outputs[0].default_value = v; ev_.outputs[0].keyframe_insert("default_value", frame=f)
    Lk(pv.outputs["Volume"], out.inputs["Volume"]); d.data.materials.append(m)
    for f, v in (dens_keys or ((1, 1.0),)): fv.outputs[0].default_value = v; fv.outputs[0].keyframe_insert("default_value", frame=f)
    off.inputs[1].default_value = (0, 0, 0); off.inputs[1].keyframe_insert("default_value", frame=1)
    off.inputs[1].default_value = (0, 0, -speed * NF / 30); off.inputs[1].keyframe_insert("default_value", frame=NF)
    nz.inputs["W"].default_value = 0; nz.inputs["W"].keyframe_insert("default_value", frame=1)
    nz.inputs["W"].default_value = NF / 30 * 0.8; nz.inputs["W"].keyframe_insert("default_value", frame=NF)
    for f, sz in (scale_keys or ()): d.scale = sz; d.keyframe_insert("scale", frame=f)
    return d

def fire_column(name, loc, w, hgt, f0, f1, parent=None, smoke=True, smoke_h=None, rnd=1.0):
    """Llamas volumétricas + columna de humo negro encima."""
    ek = [(f0 - 1, 0.0), (f0 + 4, 7.0 * rnd), (max(f0 + 5, f1 - 6), 7.0 * rnd), (f1, 0.0)]
    vol_shape(name + "Llama", (loc[0], loc[1], loc[2] + hgt / 2), 1.5, (0.3, 0.08, 0.03), "column", emit=6.0, ecol=(1.0, 0.13, 0.0),
              taper=(1.0, -0.55), ptop=0.9, speed=3.0, nscale=2.8, stretch=(w / 2, 0.8, hgt / 2), emit_keys=ek,
              dens_keys=[(f0 - 1, 0.0), (f0 + 4, 1.0), (max(f0 + 5, f1 - 6), 1.0), (f1, 0.0)],
              scale_keys=[(1, (w / 2, 0.8, hgt / 2))], parent=parent, gate=(0.45, 3.8))
    if smoke:
        sh = smoke_h or hgt * 4
        vol_shape(name + "Humo", (loc[0] - 0.5, loc[1] + 0.5, loc[2] + hgt * 0.6 + sh / 2), 10.0, (0.035, 0.035, 0.04), "column",
                  taper=(0.35, 0.9), ptop=0.6, speed=1.4, nscale=1.1, stretch=(w / 2 + 1, 2, sh / 2),
                  dens_keys=[(f0, 0.0), (f0 + 20, 1.0), (NF, 1.0)], scale_keys=[(1, (w / 2 + 1.2, 2.2, sh / 2))], gate=(0.33, 2.4))

def explosion(loc, f0):
    """Bola de fuego volumétrica que se apaga y se vuelve humo + escombros + chispas + columna de humo."""
    x, y, z = loc
    vol_shape("BolaFuego", loc, 4.0, (0.06, 0.05, 0.045), "ball", emit=14.0, ecol=(1.0, 0.16, 0.0), nscale=1.9, speed=2.0,
              emit_keys=[(f0 - 1, 0), (f0, 22), (f0 + 4, 14), (f0 + 10, 6), (f0 + 18, 1.2), (f0 + 28, 0)],
              dens_keys=[(f0 - 1, 0), (f0, 1.0), (f0 + 30, 1.2), (NF, 0.9)],
              scale_keys=[(f0 - 1, (0.05, 0.05, 0.04)), (f0 + 1, (1.4, 1.4, 1.1)), (f0 + 4, (2.6, 2.4, 2.2)), (f0 + 12, (3.4, 3.0, 3.0)),
                          (f0 + 40, (4.2, 3.6, 4.0)), (NF, (5.0, 4.2, 4.6))], gate=(0.4, 3.2))
    vol_shape("HumoExpl", (x - 1, y + 0.5, z + 7), 5.0, (0.04, 0.04, 0.045), "column", taper=(0.4, 0.9), ptop=0.5, speed=1.6,
              nscale=1.0, stretch=(3, 3, 6), dens_keys=[(f0 + 4, 0), (f0 + 30, 1.0), (NF, 1.0)],
              scale_keys=[(f0 + 4, (2.0, 2.0, 1.0)), (f0 + 40, (3.5, 3.2, 6.0)), (NF, (4.5, 4.0, 7.5))])
    o = emitter("ExplEmit", (x, y, z + 0.2), 2.0, 1.2)
    psys(o, I_DEB, 260, f0, f0 + 3, 80, 7.0, 4.5, 0.07, 0.8, 1.0, 0.2)
    psys(o, I_EMBER, 400, f0, f0 + 4, 30, 9.0, 6.0, 0.025, 0.5, 0.6, 0.6)
    flicker_light((x, y + 2, z + 2), (1.0, 0.5, 0.15), 600, f0, NF, rad=3, peak=(5000, 14))

if SHOT in ("hook", "nov26"):
    hits = water_splash(1.0 if SHOT == "hook" else 1.15)
    fhit = min(f for f, p in hits)
    # el arco ya arde antes de caer (golpes previos); las llamas se apagan al tocar el agua
    fire_column("FuegoArco", (0.5, 0.0, 3.7), 3.4, 2.4, 1, fhit + 2, parent=ARCH["road"], smoke=False)
    vol_shape("HumoArco", (0.5, 0.6, 3.8 + 6), 5.0, (0.035, 0.035, 0.04), "column", taper=(0.3, 0.9), ptop=0.6, speed=1.5,
              nscale=1.0, stretch=(2.5, 2.5, 6), dens_keys=[(1, 1.0), (fhit, 1.0), (NF, 0.6)], scale_keys=[(1, (3.0, 2.6, 6.5))])
    e_ = emitter("BrasasArco", (0.5, 0.0, 3.75), 3.0, 1.4, ARCH["road"]); psys(e_, I_EMBER, 300, 1, fhit, 25, 2.0, 1.5, 0.022, 0.5, -0.1, 0.4)
    flicker_light((0.5, 1.2, 4.6), (1.0, 0.45, 0.12), 700, 1, fhit + 2, ARCH["road"])
if SHOT == "oct22":
    explosion((35.5, 0.55, zdeck(35.5) + 0.6), FALL)
    for j in range(4):   # cisternas ardiendo en el ferroviario
        xc = TRAIN_X0 - 3.0 - j * 4.2
        fire_column(f"FuegoTren{j}", (xc, -3.4, zdeck(xc) + 0.45), 3.4, 2.2 + 0.4 * (j % 2), FALL + 2 + 3 * j, NF + 5, smoke_h=10)
        flicker_light((xc, -2.0, zdeck(xc) + 1.6), (1.0, 0.45, 0.12), 500, FALL + 2 + 3 * j, NF)

# ---------------- cámaras ----------------
tgt = empty("Objetivo", (0, 0, 4))
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.clip_end = 1500
tr = cam.constraints.new("TRACK_TO"); tr.target = tgt; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
SHOTS = {   # (lente, [(cuadro relativo 0–1, cam, objetivo)])
    "hook":  (32, [(0, (17, 21, 6.5), (-1, -1, 5.0)), (1, (11, 16, 5.0), (-1, -1.5, 3.2))]),
    "nov26": (26, [(0, (-26, 14, 2.6), (0, -1, 5.0)), (1, (-21, 11, 2.0), (0, -1, 3.8))]),
    "fly":   (30, [(0, (-58, 34, 22), (-25, -1, 2)), (0.55, (-18, 26, 14), (0, -1, 4)), (1, (14, 22, 10), (6, -1.5, 4))]),
    "oct22": (32, [(0, (46, 14, 6), (34, -1, 2.5)), (1, (42, 11, 4.5), (34, -1.5, 2.0))]),
}
lens, keys = SHOTS[SHOT]; cam.data.lens = lens
for fr, cpos, tpos in keys:
    f = 1 + fr * (NF - 1)
    cam.location = cpos; cam.keyframe_insert("location", frame=f)
    tgt.location = tpos; tgt.keyframe_insert("location", frame=f)

still = arg("--still")
if still:   # --still 40 o --still 30,40,55 (las partículas necesitan avanzar cuadro a cuadro)
    want = sorted(int(x) for x in still.split(","))
    for f in range(1, want[-1] + 1):
        sc.frame_set(f)
        if f in want:
            on_frame(sc); sc.render.filepath = os.path.join(OUT, f"still_{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    sc.frame_start = int(arg("--from", 1)); sc.frame_end = int(arg("--to", NF))
    sc.render.image_settings.file_format = "PNG"; sc.render.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)

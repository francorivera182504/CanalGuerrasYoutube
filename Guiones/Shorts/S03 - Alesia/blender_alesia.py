"""Maqueta 3D de Alesia en Blender (relieve real + línea interior + oppidum) y plano de dron.
Uso: blender -b -P blender_alesia.py -- [--still N] [--from F --to F] [--out carpeta]
1 unidad = 100 m. Relieve exagerado x EXAG.
"""
import bpy, json, math, os, sys, random
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, "terreno")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(k, d=None):
    return argv[argv.index(k) + 1] if k in argv else d
OUT = arg("--out", os.path.join(HERE, "render3d"))
os.makedirs(OUT, exist_ok=True)

EXAG = 2.2
U = 100.0
meta = json.load(open(os.path.join(T, "meta.json")))
H = np.load(os.path.join(T, "height.npy")).astype(float)
S = H.shape[0]; mpp = meta["mpp"]; HMIN = H.min()
cx, cy = meta["center_px"]
rings = json.load(open(os.path.join(T, "rings.json")))

def h_at(px, py):
    px = min(max(px, 0), S - 1.001); py = min(max(py, 0), S - 1.001)
    x0, y0 = int(px), int(py); fx, fy = px - x0, py - y0
    a = H[y0, x0] * (1 - fx) + H[y0, x0 + 1] * fx
    b = H[y0 + 1, x0] * (1 - fx) + H[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy
def world(px, py, dz=0.0):
    return Vector(((px - S / 2) * mpp / U, (S / 2 - py) * mpp / U, (h_at(px, py) - HMIN) * EXAG / U + dz))
def ring_world(key, dz=0.0):
    return [world(cx + x / mpp, cy - y / mpp, dz) for x, y in rings[key]]

# ---------------- escena limpia ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 30
sc.view_settings.view_transform = "Standard"

# ---------------- terreno ----------------
N = 400
bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=S * mpp / U)
ter = bpy.context.object; ter.name = "Terreno"
me = ter.data
co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
half = S * mpp / U / 2
px = (co[:, 0] + half) / (2 * half) * (S - 1); py = (half - co[:, 1]) / (2 * half) * (S - 1)
ix = np.clip(px.astype(int), 0, S - 2); iy = np.clip(py.astype(int), 0, S - 2); fx = px - ix; fy = py - iy
hz = (H[iy, ix] * (1 - fx) * (1 - fy) + H[iy, ix + 1] * fx * (1 - fy) + H[iy + 1, ix] * (1 - fx) * fy + H[iy + 1, ix + 1] * fx * fy)
co[:, 2] = (hz - HMIN) * EXAG / U
me.vertices.foreach_set("co", co.ravel()); me.update()
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("Tierra"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.9
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(os.path.join(T, "color_flat.png"))
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.35; hs.inputs["Value"].default_value = 0.8
nt.links.new(tex.outputs["Color"], hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], bsdf.inputs["Base Color"])
me.materials.append(mat)

def mat_rgb(name, rgb, rough=0.8, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m
WOOD = mat_rgb("Madera", (0.36, 0.22, 0.11))
EARTH = mat_rgb("Terraplen", (0.30, 0.21, 0.11))
NEON_R = mat_rgb("NeonRojo", (1.0, 0.03, 0.02), 0.4, 1.6)
ROOF = mat_rgb("Techo", (0.62, 0.50, 0.28))
WALLM = mat_rgb("Pared", (0.85, 0.80, 0.68))

# ---------------- línea interior: terraplén + empalizada + torres + neón ----------------
def curve_from(points, name, bevel_obj=None, depth=0.0, matl=None, closed=True):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(points) - 1)
    for p, v in zip(sp.points, points): p.co = (*v, 1)
    sp.use_cyclic_u = closed
    if bevel_obj: cu.bevel_mode = "OBJECT"; cu.bevel_object = bevel_obj
    else: cu.bevel_depth = depth
    ob = bpy.data.objects.new(name, cu); sc.collection.objects.link(ob)
    if matl: cu.materials.append(matl)
    return ob

def profile(name, pts):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "2D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts): p.co = (v[0], v[1], 0, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); sc.collection.objects.link(ob); ob.hide_render = True; ob.hide_viewport = True
    return ob

inner = ring_world("inner")
# perfil: terraplén ancho + empalizada fina (estilizado, exagerado para que se lea desde el dron)
bank = profile("PerfilTerraplen", [(-0.35, -0.05), (0.35, -0.05), (0.16, 0.18), (-0.16, 0.18)])
pali = profile("PerfilEmpalizada", [(-0.04, 0.15), (0.04, 0.15), (0.04, 0.45), (-0.04, 0.45)])
for nm, prof, m in (("Terraplen", bank, EARTH), ("Empalizada", pali, WOOD)):
    ob = curve_from(inner, "Interior_" + nm, prof, matl=m)
    ob.data.twist_mode = "Z_UP"
neon = curve_from([v + Vector((0, 0, 0.55)) for v in inner], "Interior_Neon", depth=0.11, matl=NEON_R)
# torres cada ~250 m
acc = 0.0; last = inner[0]; TOWERS = []
for i, v in enumerate(inner):
    acc += (v - last).length; last = v
    if acc >= 2.5:
        acc = 0.0
        bpy.ops.mesh.primitive_cube_add(size=1, location=v + Vector((0, 0, 0.30)))
        t = bpy.context.object; t.scale = (0.09, 0.09, 0.30); t.data.materials.append(WOOD); t["k"] = i / len(inner); TOWERS.append(t)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.10, depth=0.10, location=v + Vector((0, 0, 0.66)))
        r = bpy.context.object; r.rotation_euler[2] = math.pi / 4; r.data.materials.append(ROOF); r["k"] = i / len(inner); TOWERS.append(r)

# animación: la línea se "construye" (bevel_factor_end 0→1) en BUILD_F0..BUILD_F1
BUILD_F0, BUILD_F1 = int(arg("--build0", 1)), int(arg("--build1", 70))
PATHS = {"Interior_Terraplen": inner, "Interior_Empalizada": inner, "Interior_Neon": [v + Vector((0, 0, 0.55)) for v in inner]}
def _build(scene, *a):
    f = scene.frame_current
    k = min(1.0, max(0.0, (f - BUILD_F0) / max(1, BUILD_F1 - BUILD_F0)))
    k = k * k * (3 - 2 * k)
    for nm, pts in PATHS.items():
        cu = bpy.data.objects[nm].data
        n = max(2, int(round(k * len(pts))))
        cu.splines.clear(); sp = cu.splines.new("POLY"); sp.points.add(n - 1)
        for p_, v in zip(sp.points, pts[:n]): p_.co = (*v, 1)
        sp.use_cyclic_u = n >= len(pts)
        bpy.data.objects[nm].hide_render = k < 0.003
    for ob in TOWERS:
        ob.hide_render = ob["k"] > k
bpy.app.handlers.frame_change_pre.append(_build)

# ---------------- oppidum sobre la meseta (casas sencillas) ----------------
random.seed(3)
plateau_z = (h_at(cx, cy) - HMIN) * EXAG / U
placed = 0
for _ in range(4000):
    dx, dy = random.uniform(-110, 110), random.uniform(-45, 45)
    px_, py_ = cx + dx, cy + dy
    if h_at(px_, py_) < h_at(cx, cy) - 12: continue
    p = world(px_, py_)
    s = random.uniform(0.08, 0.13)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=s, depth=s * 0.9, location=p + Vector((0, 0, s * 0.45)))
    bpy.context.object.data.materials.append(WALLM)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=s * 1.15, depth=s * 1.1, location=p + Vector((0, 0, s * 0.9 + s * 0.55)))
    bpy.context.object.data.materials.append(ROOF)
    placed += 1
    if placed >= 140: break
print("casas", placed)

# ---------------- árboles (bosque en laderas, solo cerca del centro) ----------------
FM = np.load(os.path.join(T, "forest.npy"))
LEAF = mat_rgb("Hoja", (0.10, 0.26, 0.08)); TRUNK = mat_rgb("Tronco", (0.25, 0.15, 0.07))
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.12); copa = bpy.context.object; copa.data.materials.append(LEAF)
tree_mesh = copa.data; bpy.data.objects.remove(copa)
random.seed(5); nt_ = 0
col_trees = bpy.data.collections.new("Arboles"); sc.collection.children.link(col_trees)
for _ in range(60000):
    px_, py_ = random.uniform(cx - 330, cx + 330), random.uniform(cy - 330, cy + 330)
    if FM[int(py_), int(px_)] < 0.5 or random.random() > 0.55: continue
    ob = bpy.data.objects.new("arbol", tree_mesh); col_trees.objects.link(ob)
    ob.location = world(px_, py_, 0.08); k = random.uniform(0.7, 1.4); ob.scale = (k, k, k * 1.3)
    nt_ += 1
    if nt_ >= 9000: break
print("arboles", nt_)
# ---------------- luz y cielo ----------------
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-40)))
sun = bpy.context.object; sun.data.energy = 3.2; sun.data.color = (1.0, 0.93, 0.82); sun.data.angle = math.radians(3)
w = bpy.data.worlds.new("Cielo"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.55, 0.72, 0.95, 1); bg.inputs["Strength"].default_value = 0.9
try: sc.eevee.use_shadows = True
except Exception: pass

try:
    ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers"); gl = ng.nodes.new("CompositorNodeGlare")
    try: gl.glare_type = "BLOOM"
    except Exception: gl.glare_type = "FOG_GLOW"
    outn = ng.nodes.new("NodeGroupOutput"); ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs["Image"], outn.inputs[0])
    print("glow ok")
except Exception as e:
    print("sin glow", e)
# ---------------- cámara de dron ----------------
bpy.ops.object.empty_add(location=world(cx, cy, 0.0))
tgt = bpy.context.object; tgt.name = "Objetivo"
bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam; cam.data.lens = 24; cam.data.clip_end = 2000
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
F0, F1 = 1, int(arg("--frames", 196))
sc.frame_start, sc.frame_end = F0, F1
def cam_at(f, ang, dist, alt):
    a = math.radians(ang); base = tgt.location
    cam.location = base + Vector((math.cos(a) * dist, math.sin(a) * dist, alt)); cam.keyframe_insert("location", frame=f)
cam_at(F0, -115, 30, 42)
cam_at(F1, -65, 22, 26)
for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
    for k in fc.keyframe_points: k.interpolation = "SINE"; k.easing = "EASE_IN_OUT"

if "--map" in argv:
    # vista cenital ortográfica para los planos de MAPA (las murallas se dibujan en 2D con neón)
    for nm in ("Interior_Terraplen", "Interior_Empalizada", "Interior_Neon"): bpy.data.objects[nm].hide_render = True
    for o in sc.objects:
        if o.type == "MESH" and o.name.startswith("Cube") or o.name.startswith("Cone") and o.location.z > 0 and False: pass
    cam.constraints.clear(); cam.animation_data_clear()
    cam.data.type = "ORTHO"; cam.data.sensor_fit = "VERTICAL"; cam.data.ortho_scale = S * mpp / U
    cam.location = (0, 0, 60); cam.rotation_euler = (0, 0, 0)
    sc.render.filepath = os.path.join(OUT, "mapa_cenital.png"); bpy.ops.render.render(write_still=True)
    print("LISTO"); raise SystemExit
still = arg("--still")
if still is not None:
    sc.frame_set(int(still)); _build(sc); sc.render.filepath = os.path.join(OUT, f"still_{int(still):04d}.png")
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start = int(arg("--from", F0)); sc.frame_end = int(arg("--to", F1))
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "alesia.blend"))
print("LISTO")

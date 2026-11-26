"""Kit 3D reutilizable WarMap Stick (Blender 5.3, Eevee, 1920x1080, 30 fps).
blender -b -P blender_kit.py -- --shot NOMBRE --out DIR_ABS [--still 40]
Parámetros de cada toma en shots.json (frames y tiempos clave en cuadros).
Tomas: relieve con textura neón (hook_iran, hormuz, levant67, iran_jets) y objetos (fordow, natanz, redsea_ship).
"""
import bpy, bmesh, json, math, os, random, sys
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)); P3 = os.path.join(HERE, "_prep", "3d")
argv = sys.argv[sys.argv.index("--") + 1:]
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
SHOT = arg("--shot"); OUT = arg("--out"); STILL = arg("--still")
CFG = json.load(open(os.path.join(HERE, "shots.json")))[SHOT]; NF = CFG["frames"]
rnd = random.Random(7)

# ---------------- escena base ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
sc.render.image_settings.file_format = "PNG"
try: sc.eevee.taa_render_samples = 24
except Exception: pass
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.01, 0.015, 0.03, 1); bg.inputs[1].default_value = 1.0

def mat(name, col, emit=0.0, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def obj_from(mesh, name, m=None):
    o = bpy.data.objects.new(name, mesh); sc.collection.objects.link(o)
    if m: o.data.materials.append(m)
    return o

def box(name, size, loc, m, rot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj_from(me, name, m); o.scale = size; o.location = loc; o.rotation_euler = rot; return o

def cyl(name, r, h, loc, m, seg=24):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj_from(me, name, m); o.location = loc; return o

def sun(energy=3.0, rot=(math.radians(50), 0, math.radians(-40)), col=(1, 0.95, 0.9)):
    l = bpy.data.lights.new("sun", "SUN"); l.energy = energy; l.color = col; o = bpy.data.objects.new("sun", l); sc.collection.objects.link(o); o.rotation_euler = rot; return o

def camera(lens=30):
    c = bpy.data.cameras.new("cam"); c.lens = lens; c.clip_end = 500; o = bpy.data.objects.new("cam", c); sc.collection.objects.link(o); sc.camera = o
    tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
    tc = o.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    return o, tgt

def keys(o, attr, frames_vals):
    for f, v in frames_vals:
        setattr(o, attr, v); o.keyframe_insert(attr, frame=f)
    if o.animation_data and o.animation_data.action:
        try:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "EASE_IN_OUT"
        except Exception: pass

# ---------------- relieve ----------------
TER = {}
def terrain(area, exag=20.0, dark=1.0, emit=0.55):
    info = json.load(open(os.path.join(P3, "areas.json")))[area]; d = np.load(os.path.join(P3, f"{area}_dem.npy"))
    lon0, lon1, lat0, lat1 = info["bbox"]; gh, gw = d.shape; SX, SY = 19.2, 10.8
    zscale = SY / ((lat1 - lat0) * 111000.0) * exag
    me = bpy.data.meshes.new("ter"); verts = []; faces = []
    for j in range(gh):
        for i in range(gw):
            verts.append(((i / (gw - 1) - 0.5) * SX, (0.5 - j / (gh - 1)) * SY, max(0.0, float(d[j, i])) * zscale))
    for j in range(gh - 1):
        for i in range(gw - 1):
            a = j * gw + i; faces.append((a, a + gw, a + gw + 1, a + 1))
    me.from_pydata(verts, [], faces); me.update()
    uv = me.uv_layers.new();
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; i, j = vi % gw, vi // gw; uv.data[li].uv = (i / (gw - 1), 1 - j / (gh - 1))
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new("term"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(os.path.join(P3, f"{area}_tex.png")); tex.interpolation = "Cubic"
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs[0], mul.inputs[6]); mul.inputs[7].default_value = (dark, dark, dark, 1)
    nt.links.new(mul.outputs[2], b.inputs["Base Color"]); nt.links.new(mul.outputs[2], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = emit; b.inputs["Roughness"].default_value = 0.9
    o = obj_from(me, "terrain", m)
    TER.update(bbox=(lon0, lon1, lat0, lat1), d=d, zscale=zscale, SX=SX, SY=SY)
    return o

def ll(lon, lat, up=0.0):
    lon0, lon1, lat0, lat1 = TER["bbox"]; d = TER["d"]; gh, gw = d.shape
    u = (lon - lon0) / (lon1 - lon0); v = (lat1 - lat) / (lat1 - lat0)
    h = float(d[min(gh - 1, max(0, int(v * (gh - 1)))), min(gw - 1, max(0, int(u * (gw - 1))))])
    return Vector(((u - 0.5) * TER["SX"], (0.5 - v) * TER["SY"], max(0, h) * TER["zscale"] + up))

# ---------------- arcos de misil (crecen con handler) ----------------
ARCS = []
def arc(p0, p1, f0, f1, col=(1, 0.35, 0.1), height=1.6, r=0.012, tail=0.35, npts=48):
    cu = bpy.data.curves.new("arc", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(npts - 1)
    o = obj_from(cu, "arc", mat("arcm", col, emit=2.2)); pts = []
    for k in range(npts):
        u = k / (npts - 1); p = p0.lerp(p1, u); p.z += math.sin(math.pi * u) * height; pts.append(p)
    ARCS.append((sp, pts, f0, f1, tail)); return o

def upd_arcs(scene, *_):
    f = scene.frame_current
    for sp, pts, f0, f1, tail in ARCS:
        u = (f - f0) / max(1, f1 - f0); head = min(1.0, max(0.0, u)); t0 = min(1.0, max(0.0, u - tail)) if u < 1 + tail else 1.0
        n = len(pts)
        for k in range(n):
            uk = k / (n - 1); q = pts[int(round(min(max(uk, t0), head) * (n - 1)))]
            if head <= 0 or t0 >= 1.0: q = pts[0] if head <= 0 else pts[-1]
            sp.points[k].co = (q.x, q.y, q.z, 1)
bpy.app.handlers.frame_change_pre.append(upd_arcs)

def flash(loc, f, size=0.35, col=(1, 0.6, 0.2), energy=4000):
    s = bpy.data.meshes.new("fl"); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0); bm.to_mesh(s); bm.free()
    o = obj_from(s, "flash", mat("flm", col, emit=4.0)); o.location = loc
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f, (size * 0.4,) * 3), (f + 6, (size,) * 3), (f + 16, (0.001,) * 3)])
    l = bpy.data.lights.new("fll", "POINT"); l.color = col; lo = bpy.data.objects.new("fll", l); sc.collection.objects.link(lo); lo.location = loc + Vector((0, 0, 0.3))
    for ff, e in ((f - 1, 0), (f + 2, energy), (f + 18, 0)): l.energy = e; l.keyframe_insert("energy", frame=ff)

def marker(loc, f0, col=(1, 0.8, 0.2)):
    o = cyl("mk", 0.12, 0.02, loc + Vector((0, 0, 0.02)), mat("mkm", col, emit=2.5), 32)
    keys(o, "scale", [(f0 - 1, (0.01, 0.01, 1)), (f0 + 6, (1, 1, 1)), (f0 + 20, (1.6, 1.6, 1)), (f0 + 34, (1, 1, 1)), (NF, (1.3, 1.3, 1))])

def jet(name, m):
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((0.5, 0, 0), (-0.35, 0.05, 0), (-0.35, -0.05, 0), (-0.2, 0.32, 0), (-0.2, -0.32, 0), (-0.4, 0, 0.12))]
    bm.faces.new((v[0], v[3], v[1])); bm.faces.new((v[0], v[2], v[4])); bm.faces.new((v[0], v[1], v[2])); bm.faces.new((v[1], v[5], v[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = obj_from(me, name, m); return o

def tanker(name, loc, heading, scale=0.12):
    hull = mat("hull", (0.45, 0.1, 0.08), rough=0.5); deck = mat("deck", (0.25, 0.28, 0.3)); brg = mat("brg", (0.92, 0.92, 0.9))
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, heading); root.scale = (scale,) * 3
    for o in (box("h", (3.0, 0.55, 0.35), (0, 0, 0.0), hull), box("d", (2.9, 0.5, 0.06), (0, 0, 0.2), deck), box("b", (0.35, 0.45, 0.45), (-1.2, 0, 0.45), brg)):
        o.parent = root
    return root

def light_beacon(o, f0):
    return

# ---------------- tomas ----------------
def shot_hook_iran():
    terrain("iran", exag=10, dark=1.0, emit=0.9); sun(1.6, (math.radians(70), 0, math.radians(120)), (0.6, 0.7, 1.0))
    cam, tgt = camera(28); teh = ll(51.39, 35.69)
    keys(cam, "location", [(1, teh + Vector((-6.5, -5.5, 4.6))), (NF, teh + Vector((-3.2, -2.9, 2.2)))]); keys(tgt, "location", [(1, teh + Vector((0.4, 0, 0))), (NF, teh)])
    imp = CFG["impact"]
    for k in range(16):
        src = ll(44.0 + rnd.uniform(0, 1.5), 29.5 + rnd.uniform(0, 6)); dst = teh + Vector((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.3, 0.3), 0))
        f1 = imp - rnd.randint(-6, 14); arc(src, dst, f1 - 40, f1, (1, 0.45, 0.15), 2.0)
        if k % 3 == 0: flash(dst, f1, 0.25)
    flash(teh, imp, 0.45, energy=2500)
    cyl("city", 0.35, 0.01, teh + Vector((0, 0, 0.02)), mat("citym", (1, 0.75, 0.4), emit=3.0), 32)

def shot_hormuz():
    terrain("hormuz", exag=4, dark=0.8, emit=0.45); sun(3.0, (math.radians(55), 0, math.radians(-60)), (1, 0.85, 0.7))
    cam, tgt = camera(32); c = ll(56.45, 26.4)
    keys(cam, "location", [(1, c + Vector((-5.5, -4.5, 3.0))), (NF, c + Vector((-1.5, -4.2, 2.2)))]); keys(tgt, "location", [(1, c), (NF, c + Vector((0.8, 0.3, 0)))])
    lane = [(55.2, 26.05), (55.9, 26.35), (56.35, 26.5), (56.75, 26.3), (57.2, 25.9), (57.6, 25.4)]
    stop = CFG.get("stop", 90)
    for k in range(11):
        u = k / 10; i = min(len(lane) - 2, int(u * (len(lane) - 1))); f = u * (len(lane) - 1) - i
        a = Vector(lane[i]); b = Vector(lane[i + 1]); p = a.lerp(b, f); hd = math.atan2((b - a).y, (b - a).x)
        t = tanker(f"t{k}", ll(p.x, p.y, 0.01), hd)
        dv = (b - a).normalized() * 0.25
        keys(t, "location", [(1, ll(p.x - dv.x, p.y - dv.y, 0.01)), (stop, ll(p.x, p.y, 0.01))])
    for p in ((56.1, 26.75), (56.9, 26.7), (56.3, 26.95)):
        marker(ll(*p), 20 + rnd.randint(0, 40), (1, 0.25, 0.15))

def shot_levant67():
    terrain("levant", exag=18, dark=0.85, emit=0.5); sun(3.2, (math.radians(50), 0, math.radians(-30)))
    cam, tgt = camera(30); c = ll(34.9, 31.0)
    keys(cam, "location", [(1, c + Vector((-4.5, -6.5, 4.5))), (NF, c + Vector((3.8, -6.0, 4.0)))]); keys(tgt, "location", [(1, c), (NF, c + Vector((0.3, 0.6, 0)))])

def shot_iran_jets():
    terrain("iran", exag=10, dark=1.0, emit=0.45); sun(3.5, (math.radians(45), 0, math.radians(-50)))
    cam, tgt = camera(30); m = mat("jetm", (0.55, 0.58, 0.62), rough=0.4, metal=0.3)
    sites = [ll(51.92, 33.72), ll(50.99, 34.88), ll(51.67, 32.65)]
    c = ll(49.5, 33.6)
    keys(cam, "location", [(1, c + Vector((-6.0, -5.0, 3.6))), (NF, c + Vector((-1.0, -4.6, 2.8)))]); keys(tgt, "location", [(1, c), (NF, sites[0])])
    for k in range(7):
        j = jet(f"j{k}", m); j.scale = (0.45,) * 3; off = Vector(((k % 3) * -0.35, (k - 3) * 0.28, 0))
        a = ll(44.5, 32.5 + (k - 3) * 0.25, 1.0) + off; b = sites[k % 3] + Vector((0, 0, 0.9)) + off * 0.3
        j.rotation_euler = (0, 0, math.atan2((b - a).y, (b - a).x))
        keys(j, "location", [(1, a), (NF, b)])
    for i, s in enumerate(sites): marker(s, CFG.get("mark", 60) + i * 12, (1, 0.75, 0.2))

def mountain(m):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=120, y_segments=60, size=1.0)
    for v in bm.verts:
        x, y = v.co.x * 6, (v.co.y + 1) * 1.5; h = 2.6 * math.exp(-((x / 3.2) ** 2 + (y / 2.2) ** 2)) + 0.25 * math.sin(x * 2.1 + y) * math.exp(-(x / 4) ** 2)
        v.co = Vector((x, y, max(0, h)))
    me = bpy.data.meshes.new("mt"); bm.to_mesh(me); bm.free(); o = obj_from(me, "mountain", m)
    for p in me.polygons: p.use_smooth = True
    return o

def shot_fordow():
    sky = sun(3.0, (math.radians(55), 0, math.radians(-35)), (1, 0.92, 0.85))
    bg.inputs[0].default_value = (0.25, 0.35, 0.5, 1)
    rock = mat("rock", (0.3, 0.24, 0.18), rough=0.95); cut = mat("cut", (0.78, 0.6, 0.4), rough=1.0, emit=0.15)
    mt = mountain(rock)
    # corte: media montaña con cara frontal (sección) en y=0
    box("ground", (14, 8, 0.1), (0, 1.5, -0.05), mat("gnd", (0.5, 0.42, 0.3)))
    sec = bpy.data.meshes.new("sec"); xs = [i / 40 * 12 - 6 for i in range(41)]
    vs = [(x, 0.0, 0.0) for x in xs] + [(x, 0.0, max(0, 2.6 * math.exp(-((x / 3.2) ** 2)) + 0.25 * math.sin(x * 2.1) * math.exp(-(x / 4) ** 2))) for x in xs]
    fs = [(i, i + 1, 42 + i, 41 + i) for i in range(40)]; sec.from_pydata(vs, [], fs); obj_from(sec, "section", cut)
    hall = box("hall", (2.6, 0.2, 0.45), (0, -0.02, 0.55), mat("hallm", (0.03, 0.04, 0.06)))
    hl = bpy.data.lights.new("hl", "POINT"); hl.energy = 12; hl.color = (0.6, 0.8, 1); hlo = bpy.data.objects.new("hl", hl); sc.collection.objects.link(hlo); hlo.location = (0, -0.4, 0.7)
    cm = mat("cent", (0.85, 0.88, 0.9), rough=0.3, metal=0.4)
    for i in range(9): cyl(f"c{i}", 0.06, 0.34, (-1.1 + i * 0.27, -0.06, 0.55), cm)
    cam, tgt = camera(35); keys(cam, "location", [(1, Vector((-5.5, -8.0, 5.5))), (NF, Vector((-2.0, -6.0, 3.6)))]); keys(tgt, "location", [(1, Vector((0, 0.8, 1.0))), (NF, Vector((0, 0.3, 0.7)))])
    bm_ = mat("bomb", (0.3, 0.32, 0.3), metal=0.5, rough=0.4); imp = CFG["impact"]
    for k, x in enumerate((-0.6, 0.0, 0.6)):
        b = cyl(f"b{k}", 0.06, 0.7, (x, 0.6, 6), bm_); b.rotation_euler = (math.radians(-8), 0, 0)
        f1 = imp + k * 5; keys(b, "location", [(1, Vector((x, 0.6, 9))), (f1 - 25, Vector((x, 0.5, 4.5))), (f1, Vector((x, 0.25, 0.9)))])
        keys(b, "scale", [(f1, (1, 1, 1)), (f1 + 1, (0.001,) * 3)])
        flash(Vector((x, -0.05, 0.6)), f1 + 1, 0.16, energy=600)

def shot_natanz():
    bg.inputs[0].default_value = (0.005, 0.008, 0.012, 1)
    floor = box("floor", (14, 14, 0.1), (0, 0, -0.05), mat("fl", (0.07, 0.08, 0.1), rough=0.35))
    for x in (-7, 7): box("wall", (0.1, 14, 4), (x, 0, 2), mat("wl", (0.12, 0.13, 0.15)))
    for k in range(6):
        l = bpy.data.lights.new("ar", "AREA"); l.energy = 110; l.size = 2; lo = bpy.data.objects.new("ar", l); sc.collection.objects.link(lo); lo.location = (0, -6 + k * 2.4, 3.8)
    cm = mat("cent", (0.82, 0.85, 0.88), rough=0.25, metal=0.6); band = mat("band", (0.2, 0.45, 0.9), emit=1.5)
    wob = CFG["wobble"]; cs = []
    for i in range(10):
        for j in range(6):
            c = cyl(f"c{i}_{j}", 0.16, 1.9, (-4.5 + i, -5 + j * 1.6, 0.95), cm); b = cyl(f"cb{i}_{j}", 0.165, 0.06, (0, 0, 0.6), band); b.parent = c
            c.rotation_mode = "XYZ"; cs.append(c)
            if rnd.random() < 0.35:
                fr = []
                for f in range(wob, NF + 1, 3): a = math.radians(5 * math.sin((f - wob) * 0.9 + i)) * min(1, (f - wob) / 30); fr.append((f, (a, a * 0.6, 0)))
                keys(c, "rotation_euler", [(1, (0, 0, 0)), (wob, (0, 0, 0))] + fr)
    code = mat("code", (0.1, 1, 0.3), emit=10.0)
    for k in range(40):
        o = box(f"bit{k}", (0.06, 0.06, 0.06), (0, 0, 0), code); y0 = -7 + rnd.uniform(-0.5, 0.5); x0 = rnd.uniform(-4.5, 4.5); f0 = CFG["code"] + rnd.randint(0, 40)
        keys(o, "location", [(1, (x0, -9, 0.15)), (f0, (x0, -9, 0.15)), (f0 + 60, (x0 + rnd.uniform(-0.5, 0.5), rnd.uniform(-5, 3), 0.15 + rnd.random()))])
    cam, tgt = camera(26); keys(cam, "location", [(1, Vector((-5.5, -9.0, 2.6))), (NF, Vector((-2.0, -6.5, 1.7)))]); keys(tgt, "location", [(1, Vector((0, 0, 1))), (NF, Vector((0.5, -2, 0.9)))])

def shot_redsea_ship():
    bg.inputs[0].default_value = (0.55, 0.62, 0.75, 1); sun(3.5, (math.radians(65), 0, math.radians(-120)), (1, 0.8, 0.6))
    sea = box("sea", (80, 80, 0.02), (0, 0, 0), mat("seam", (0.05, 0.18, 0.3), rough=0.15))
    root = bpy.data.objects.new("ship", None); sc.collection.objects.link(root)
    hull = mat("hull", (0.12, 0.14, 0.2), rough=0.5); red = mat("red", (0.55, 0.1, 0.08))
    for o in (box("h", (6.0, 1.0, 0.6), (0, 0, 0.1), hull), box("hb", (6.0, 1.0, 0.2), (0, 0, -0.25), red), box("bridge", (0.6, 0.95, 0.9), (-2.4, 0, 0.85), mat("w", (0.92, 0.92, 0.9)))):
        o.parent = root
    cols = [(0.8, 0.2, 0.15), (0.15, 0.4, 0.75), (0.9, 0.6, 0.1), (0.2, 0.6, 0.35), (0.85, 0.85, 0.85)]
    for i in range(9):
        for j in range(3):
            for k in range(rnd.randint(1, 3)):
                box("ct", (0.48, 0.28, 0.24), (-1.8 + i * 0.5, -0.3 + j * 0.3, 0.52 + k * 0.25), mat("ctm", rnd.choice(cols), rough=0.6)).parent = root
    keys(root, "location", [(1, Vector((0, 0, 0))), (NF, Vector((3.5, 3.0, 0)))])
    keys(root, "rotation_euler", [(1, (0, 0, math.radians(80))), (CFG["turn"], (0, 0, math.radians(80))), (CFG["turn"] + 90, (0, 0, math.radians(215)))])
    cam, tgt = camera(30); keys(cam, "location", [(1, Vector((-9, -8, 3.5))), (NF, Vector((-6, -9, 9)))]); keys(tgt, "location", [(1, Vector((0, 0, 0.5))), (NF, Vector((2.5, 2.5, 0.3)))])

globals()["shot_" + SHOT]()
os.makedirs(OUT, exist_ok=True)
if STILL:
    for f in [int(x) for x in STILL.split(",")]:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, f"still_{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUT, "f_"); bpy.ops.render.render(animation=True)
print("FIN", SHOT)

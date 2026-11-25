"""S06 Dazzle. Carguero WW1 con camuflaje dazzle en mar abierto. 1 u = 10 m, proa hacia +X.
blender -b -P blender_dazzle.py -- --shot scope|aim|turn|miss --out ABS [--still 1,60] [--res .5] [--grey]
"""
import bpy, math, os, sys, random
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
COUNTS = {'scope': 204, 'aim': 169, 'turn': 182, 'miss': 86}
SHOT = arg('--shot', 'scope'); NF = int(arg('--frames', COUNTS[SHOT])); OUT = arg('--out')
assert OUT and os.path.isabs(OUT), 'pasar --out absoluto'
os.makedirs(OUT, exist_ok=True); RES = float(arg('--res', 1)); GREY = '--grey' in argv; random.seed(6)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = int(1080 * RES); sc.render.resolution_y = int(1920 * RES)
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = NF
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
ee = sc.eevee; ee.taa_render_samples = int(arg('--samples', 24)); ee.volumetric_end = 200; ee.volumetric_samples = 32

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    return m, nt, nt.nodes['Material Output']
def mat(name, rgb, rough=.6, metal=0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m
def box(name, loc, size, m, parent):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name
    o.scale = tuple(x / 2 for x in size); o.data.materials.append(m); o.parent = parent; return o
def cyl(name, p0, p1, r, m, parent, verts=16):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object; o.name = name; o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized()); o.data.materials.append(m); o.parent = parent; return o
def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; return o

SHIP = empty('steamer')
def dazzle_mat():
    m, nt, out = node_mat('dazzle paint'); N = nt.nodes.new; L = nt.links.new
    b = N('ShaderNodeBsdfPrincipled'); b.inputs['Roughness'].default_value = .62
    tc = N('ShaderNodeTexCoord'); tc.object = SHIP; sp = N('ShaderNodeSeparateXYZ'); cb = N('ShaderNodeCombineXYZ')
    mx = N('ShaderNodeMapRange'); mx.inputs['From Min'].default_value = -6.2; mx.inputs['From Max'].default_value = 6.2
    mz = N('ShaderNodeMapRange'); mz.inputs['From Min'].default_value = -.6; mz.inputs['From Max'].default_value = 2.4
    img = N('ShaderNodeTexImage'); img.image = bpy.data.images.load(os.path.join(HERE, 'dazzle.png')); img.extension = 'EXTEND'
    L(tc.outputs['Object'], sp.inputs[0]); L(sp.outputs['X'], mx.inputs['Value']); L(sp.outputs['Z'], mz.inputs['Value'])
    L(mx.outputs['Result'], cb.inputs['X']); L(mz.outputs['Result'], cb.inputs['Y']); L(cb.outputs[0], img.inputs['Vector'])
    L(img.outputs['Color'], b.inputs['Base Color']); L(b.outputs[0], out.inputs['Surface']); return m
PAINT = mat('war grey', (.34, .37, .40), .6) if GREY else dazzle_mat()
DECK = mat('wood deck', (.30, .22, .15), .8); BLACK = mat('black', (.02, .02, .025), .5); RUST = mat('boot topping', (.25, .06, .04), .7)
GLASS = mat('glass', (.05, .09, .12), .2); MAST = mat('mast', (.55, .50, .42), .6)

# casco por estaciones: francobordo ~1.0 con arrufo, calado 0.55
st = [(-6, .25), (-5.6, .62), (-4.6, .78), (-2, .80), (2.5, .80), (4.4, .66), (5.5, .32), (6.05, .03)]
vs = []; fs = []
for x, w in st:
    sheer = .95 + .10 * (abs(x) / 6) ** 2
    vs.extend([(x, -w, sheer), (x, w, sheer), (x, w * .8, -.55), (x, -w * .8, -.55)])
for j in range(len(st) - 1):
    for k in range(4): fs.append((j * 4 + k, j * 4 + (k + 1) % 4, (j + 1) * 4 + (k + 1) % 4, (j + 1) * 4 + k))
fs += [(0, 3, 2, 1), (28, 29, 30, 31)]
me = bpy.data.meshes.new('hull'); me.from_pydata(vs, [], fs); me.update()
hull = bpy.data.objects.new('hull', me); sc.collection.objects.link(hull); hull.parent = SHIP; hull.data.materials.append(PAINT)
box('deck', (0, 0, 1.0), (10.8, 1.5, .05), DECK, SHIP)
box('forecastle', (4.6, 0, 1.18), (2.2, 1.25, .4), PAINT, SHIP)
box('poop', (-5.0, 0, 1.18), (1.8, 1.2, .4), PAINT, SHIP)
box('bridge house', (.6, 0, 1.35), (2.6, 1.3, .75), PAINT, SHIP)
box('bridge top', (1.2, 0, 1.95), (1.1, 1.4, .45), PAINT, SHIP)
for y in (-.71, .71):
    for x in (.9, 1.2, 1.5): box('window', (x, y, 2.0), (.18, .02, .16), GLASS, SHIP)
cyl('funnel', (-.3, 0, 1.6), (-.5, 0, 3.1), .32, PAINT, SHIP, 24); cyl('funnel top', (-.5, 0, 3.05), (-.52, 0, 3.22), .33, BLACK, SHIP, 24)
for x in (3.2, -3.3):
    cyl('mast', (x, 0, 1), (x, 0, 4.4), .05, MAST, SHIP, 10)
    cyl('boom', (x, 0, 1.6), (x + (-1.6 if x > 0 else 1.6), 0, 1.15), .03, MAST, SHIP, 8)
    for xx in (x + .9, x - .9): box('hatch', (xx, 0, 1.1), (.8, .8, .15), DECK, SHIP)
for x in (-1.7, 2.4): cyl('ventilator', (x, .45, 1), (x, .45, 1.55), .07, PAINT, SHIP, 10)

# mar
seam = mat('sea', (.02, .07, .10), .12); nt = seam.node_tree; b = nt.nodes['Principled BSDF']
tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); nz = nt.nodes.new('ShaderNodeTexNoise')
nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 8
bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = .55; bu.inputs['Distance'].default_value = .2
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
nt.links.new(nz.outputs['Fac'], bu.inputs['Height']); nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
for f, v in ((1, (0, 0, 0)), (NF, (.5, .9, .3))):
    mp.inputs['Location'].default_value = v; mp.inputs['Location'].keyframe_insert('default_value', frame=f)
bpy.ops.mesh.primitive_plane_add(size=600); sea = bpy.context.object; sea.data.materials.append(seam)
OCEAN = None
try:
    oc = sea.modifiers.new('ocean', 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.size = 1; oc.spatial_size = 60
    oc.repeat_x = oc.repeat_y = 6; oc.resolution = 12; oc.wave_scale = .35; oc.choppiness = .7; oc.wind_velocity = 12
    sea.location = (-180, -180, 0); OCEAN = oc
except Exception as e:
    print('ocean fallback', e)

def foam_mat(name, alpha=.9, scale=6):
    m, nt, out = node_mat(name); N = nt.nodes.new; L = nt.links.new
    b = N('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (.85, .9, .92, 1); b.inputs['Roughness'].default_value = .9
    tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    gr = N('ShaderNodeTexGradient'); gr.gradient_type = 'QUADRATIC_SPHERE'
    sm = N('ShaderNodeMath'); sm.operation = 'SUBTRACT'; sm.inputs[1].default_value = .35; sm.use_clamp = True
    cr = N('ShaderNodeMath'); cr.operation = 'MULTIPLY'; m2 = N('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = alpha * 2.2; m2.use_clamp = True
    L(tc.outputs['Object'], nz.inputs['Vector']); L(tc.outputs['Object'], gr.inputs['Vector'])
    L(nz.outputs['Fac'], sm.inputs[0]); L(sm.outputs[0], cr.inputs[0]); L(gr.outputs['Fac'], cr.inputs[1]); L(cr.outputs[0], m2.inputs[0])
    tr = N('ShaderNodeBsdfTransparent'); mix = N('ShaderNodeMixShader')
    L(m2.outputs[0], mix.inputs[0]); L(tr.outputs[0], mix.inputs[1]); L(b.outputs[0], mix.inputs[2]); L(mix.outputs[0], out.inputs['Surface'])
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    return m
FOAM = foam_mat('foam')
def foam(name, loc, sx, sy, parent=None, rot=0, m=None):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc); o = bpy.context.object; o.name = name
    o.scale = (sx, sy, 1); o.rotation_euler.z = rot; o.data.materials.append(m or FOAM)
    if parent: o.parent = parent
    return o
foam('bow wave L', (5.7, -.6, .12), 1.1, .5, SHIP, .5); foam('bow wave R', (5.7, .6, .12), 1.1, .5, SHIP, -.5)
foam('stern wake', (-9, 0, .1), 4.5, .9, SHIP)
for y in (-.86, .86): foam('side wash', (0, y, .1), 5.5, .25, SHIP)

def vol_mat(name, col, dens):
    m, nt, out = node_mat(name); N = nt.nodes.new; L = nt.links.new
    pv = N('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (*col, 1)
    tc = N('ShaderNodeTexCoord'); ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1; mr.inputs['From Max'].default_value = .2
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 5
    m1 = N('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m2 = N('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = dens
    L(tc.outputs['Object'], ln.inputs[0]); L(ln.outputs['Value'], mr.inputs['Value']); L(tc.outputs['Object'], nz.inputs['Vector'])
    L(mr.outputs['Result'], m1.inputs[0]); L(nz.outputs['Fac'], m1.inputs[1]); L(m1.outputs[0], m2.inputs[0])
    L(m2.outputs[0], pv.inputs['Density']); L(pv.outputs['Volume'], out.inputs['Volume'])
    return m
SMOKE = vol_mat('coal smoke', (.08, .08, .09), 9)
PUFFS = []
for i in range(12):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1); o = bpy.context.object; o.data.materials.append(SMOKE); PUFFS.append(o)

TORP = empty('torpedo'); tm = mat('torpedo steel', (.4, .42, .44), .35, .7)
cyl('torp body', (-.35, 0, 0), (.3, 0, 0), .03, tm, TORP)
TW = foam('torpedo wake', (0, 0, .1), 1, .12, m=foam_mat('torp foam', 1.0, 14))

world = bpy.data.worlds.new('sky'); sc.world = world; world.use_nodes = True; wn = world.node_tree
tcw = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ'); rmp = wn.nodes.new('ShaderNodeValToRGB')
wn.links.new(tcw.outputs['Generated'], sep.inputs[0]); wn.links.new(sep.outputs['Z'], rmp.inputs[0])
rmp.color_ramp.elements[0].color = (.62, .66, .70, 1); rmp.color_ramp.elements[1].color = (.20, .33, .50, 1)
rmp.color_ramp.elements[0].position = .5; rmp.color_ramp.elements[1].position = .62
wn.nodes['Background'].inputs['Color'].default_value = (.56, .62, .70, 1); wn.nodes['Background'].inputs['Strength'].default_value = 1.0
bpy.ops.object.light_add(type='SUN', rotation=(.9, .2, -.6)); sun = bpy.context.object
sun.data.energy = 3.2; sun.data.angle = .15; sun.data.color = (1, .93, .82)

cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'HORIZONTAL'; cd.clip_end = 800
tgt = empty('target'); tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def ship_pose(f, x0, speed, yaw=0.0):
    t = f / 30
    SHIP.location = (x0 + speed * t * math.cos(yaw), speed * t * math.sin(yaw), .02 * math.sin(t * 1.7))
    SHIP.rotation_euler = (.012 * math.sin(t * 1.3), .010 * math.sin(t * 1.1 + 1), yaw)
def place_puffs(f):
    t = f / 30; bpy.context.view_layer.update(); base = SHIP.matrix_world @ Vector((-.52, 0, 3.25))
    for i, o in enumerate(PUFFS):
        age = (t * 1.6 + i / len(PUFFS) * 3) % 3
        o.location = base + Vector((-1.1 * age, .25 * age, .55 * age + .1 * math.sin(i)))
        r = .28 + .38 * age; o.scale = (r, r, r * .8)
def torpedo(f, p0, p1, f0, f1, show=True):
    k = max(0, min(1, (f - f0) / max(1, f1 - f0))); hide = (not show) or f < f0
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; ang = math.atan2(d.y, d.x); head = p0 + d * k
    TORP.location = (head.x, head.y, .2); TORP.rotation_euler = (0, 0, ang)
    L = max(.01, d.length * k); mid = p0 + d.normalized() * (L / 2)
    TW.location = (mid.x, mid.y, .32); TW.scale = (L / 2, .55, 1); TW.rotation_euler = (0, 0, ang)
    for o in [TORP] + list(TORP.children) + [TW]: o.hide_render = hide
def on_frame(s, *a):
    f = s.frame_current; q = (f - 1) / max(1, NF - 1)
    if OCEAN: OCEAN.time = 1 + f / 30
    if SHOT == 'scope':
        ship_pose(f, -2.0, .55); torpedo(f, (0, 0, 0), (1, 0, 0), 9999, 9999, False)
        z = smooth((f - 66) / 40)   # "zebra" 2,42 s: se abre el plano
        cd.lens = lerp(140, 48, z); bob = .10 * math.sin(f * .21) + .04 * math.sin(f * .53)
        cam.location = (SHIP.location.x * .6 - 1.5, -16, .95 + bob)
        tgt.location = (SHIP.location.x + lerp(-.3, 0, z), 0, lerp(1.55, 1.45, z) + bob * .5)
    elif SHOT == 'aim':
        ship_pose(f, -4.5, .9); torpedo(f, (-3, -17, 0), (3.6, 0, 0), 40, NF + 150)
        cd.lens = 30; cam.location = (-5 + 2 * q, -13, 6.5 - .8 * q); tgt.location = (-.5 + 1.6 * q, -3.2, .3)
    elif SHOT == 'turn':
        yaw = .42 * smooth(q * 1.1); ship_pose(f, 0, .25, yaw); torpedo(f, (0, 0, 0), (1, 0, 0), 9999, 9999, False)
        cd.lens = 32; a = -.95 + .55 * q
        cam.location = (SHIP.location.x + 3 + 5.2 * math.cos(a), SHIP.location.y + 5.2 * math.sin(a), 1.1 + .4 * q)
        tgt.location = (SHIP.location.x + 1.2, SHIP.location.y, 1.4)
    elif SHOT == 'miss':
        ship_pose(f, 0, .9); torpedo(f, (-12, -9, 0), (-6.5, 9, 0), 1, NF - 6)
        cd.lens = 24; cam.location = (-10 + 1.2 * q, -7, 3.6); tgt.location = (-5 + 1.2 * q, .5, .6)
    place_puffs(f)
bpy.app.handlers.frame_change_pre.append(on_frame)
still = arg('--still'); want = sorted(int(x) for x in still.split(',')) if still else None
frm = int(arg('--from', 1)); to = int(arg('--to', NF))
for f in range(frm, (want[-1] if want else to) + 1):
    if want and f not in want: continue
    sc.frame_set(f); on_frame(sc)
    sc.render.filepath = os.path.join(OUT, ('still_' if want else 'f_') + f'{f:04d}.png')
    bpy.ops.render.render(write_still=True)
print('COMPLETE', SHOT, flush=True)

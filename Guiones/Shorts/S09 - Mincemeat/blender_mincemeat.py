"""S09 Mincemeat. Noche, mar frente a Huelva: submarino, figura con chaleco y maletín encadenado. 1 u = 1 m.
blender -b -P blender_mincemeat.py -- --shot hook|release --out ABS [--still 1,40] [--res .5] [--samples 24]
"""
import bpy, math, os, sys, random
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
COUNTS = {'hook': 203, 'release': 87}
SHOT = arg('--shot', 'hook'); NF = int(arg('--frames', COUNTS[SHOT])); OUT = arg('--out')
assert OUT and os.path.isabs(OUT), 'pasar --out absoluto'
os.makedirs(OUT, exist_ok=True); RES = float(arg('--res', 1)); random.seed(9)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = int(1080 * RES); sc.render.resolution_y = int(1920 * RES)
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = NF
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.eevee.taa_render_samples = int(arg('--samples', 24))
FOOL = 38 if SHOT == "hook" else 2   # "fooled" 1,26 s

def mat(name, rgb, rough=.55, metal=0, emit=0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = (*(ecol or rgb), 1); b.inputs['Emission Strength'].default_value = emit
    return m
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o
def prim(kind, name, loc, scale, m, parent=None, rot=(0, 0, 0), smooth=False, **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=loc, rotation=rot, **kw); o = bpy.context.object; o.name = name
    o.scale = scale; o.data.materials.append(m); o.parent = parent
    if smooth: bpy.ops.object.shade_smooth()
    return o

# --- cielo nocturno, luna, costa
w = bpy.data.worlds.new('night'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
bg = nt.nodes['Background']; tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); cr = N('ShaderNodeValToRGB')
L(tc.outputs['Generated'], sp.inputs[0]); L(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = 0; cr.color_ramp.elements[0].color = (.05, .07, .12, 1)
cr.color_ramp.elements[1].position = .45; cr.color_ramp.elements[1].color = (.004, .008, .025, 1)
L(cr.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1
md = bpy.data.lights.new('moon', 'SUN'); md.energy = 2.2; md.color = (.6, .72, 1); md.angle = .02
moon = bpy.data.objects.new('moon', md); sc.collection.objects.link(moon); moon.rotation_euler = (math.radians(70), 0, math.radians(160))
prim('uv_sphere', 'moondisc', (-220, 420, 120), (9, 9, 9), mat('moonm', (1, 1, 1), emit=6, ecol=(.85, .9, 1)), smooth=True)
for i in range(40):
    s = random.uniform(.6, 1.6); prim('uv_sphere', 'star%d' % i, (random.uniform(-500, 500), 700, random.uniform(80, 420)), (s, s, s), mat('st%d' % i, (1, 1, 1), emit=4), segments=6, ring_count=4)
LIGHTM = mat('coast', (1, .75, .4), emit=30, ecol=(1, .7, .35))
for i in range(36):
    prim('uv_sphere', 'cl%d' % i, (random.uniform(-260, 260), 520 + random.uniform(-10, 10), .6 + random.uniform(0, 1.5)), (.7, .7, .7), LIGHTM, segments=6, ring_count=4)
prim('cube', 'coastline', (0, 540, 0), (600, 12, 4), mat('land', (.01, .012, .015), .9))

# --- mar
seam = mat('sea', (.004, .012, .025), .12)
bpy.ops.mesh.primitive_plane_add(size=600); sea = bpy.context.object; sea.data.materials.append(seam)
oc = sea.modifiers.new('ocean', 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.size = 1; oc.spatial_size = 60
oc.repeat_x = oc.repeat_y = 8; oc.resolution = 12; oc.wave_scale = .3; oc.choppiness = .8; oc.wind_velocity = 9
sea.location = (-240, -240, 0)

# --- submarino (proa hacia +X)
SUB = empty('sub'); hullm = mat('hull', (.13, .14, .15), .35, .4)
prim('uv_sphere', 'hull', (0, 0, -.6), (34, 3.2, 2.6), hullm, SUB, smooth=True, segments=32, ring_count=16)
prim('cube', 'deck', (0, 0, 1.6), (26, 1.4, .12), hullm, SUB)
prim('uv_sphere', 'tower', (2, 0, 3.2), (4.2, 1.5, 2.4), hullm, SUB, smooth=True)
prim('cube', 'towertop', (2, 0, 5.2), (3.6, 1.3, .9), hullm, SUB)
prim('cylinder', 'scope', (3, 0, 7.2), (.12, .12, 1.8), hullm, SUB)
prim('cylinder', 'gun', (-6, 0, 2.2), (.18, .18, 2.2), hullm, SUB, rot=(0, math.pi / 2, 0))
for i in range(3):
    prim('uv_sphere', 'crew%d' % i, (1.2 + i * .9, .2, 6.4), (.35, .35, .35), mat('crew', (.85, .85, .8), .6), SUB, smooth=True)
SPOTM = mat('lamp', (1, .95, .8), emit=40)
LAMP = prim('cylinder', 'lamp', (4.4, 0, 6.2), (.4, .4, .5), SPOTM, SUB, rot=(0, math.pi / 2, 0)); LAMP.visible_shadow = False
SUB.location = (22, 9, 0); SUB.rotation_euler = (0, 0, math.radians(75))

# --- figura con chaleco (boca abajo, estilizada) + maletín encadenado
FIG = empty('fig'); uni = mat('uniform', (.18, .16, .1), .8); vest = mat('vest', (.85, .45, .05), .6)
prim('uv_sphere', 'torso', (0, 0, 0), (.9, .42, .25), uni, FIG, smooth=True)
prim('cube', 'vest', (.25, 0, .12), (.55, .5, .16), vest, FIG)
prim('uv_sphere', 'head', (1.15, 0, .08), (.24, .22, .22), mat('hair', (.05, .04, .03), .7), FIG, smooth=True)
for s in (-1, 1):
    prim('cylinder', 'leg', (-1.25, s * .18, -.05), (.13, .13, .5), uni, FIG, rot=(0, math.pi / 2, 0))
    prim('cylinder', 'arm', (.3, s * .7, -.05), (.1, .1, .4), uni, FIG, rot=(math.pi / 2, 0, s * .4))
CASE = empty('case'); leather = mat('leather', (.25, .12, .05), .5)
prim('cube', 'box', (0, 0, 0), (.45, .12, .32), leather, CASE)
prim('torus', 'handle', (0, 0, .36), (.12, .12, .12), mat('brass', (.8, .6, .2), .3, .9), CASE, rot=(math.pi / 2, 0, 0), major_radius=1, minor_radius=.25)
prim('cube', 'clasp', (.2, -.13, .15), (.05, .02, .04), mat('brass2', (.9, .7, .25), .3, .9), CASE)
CHAIN = [prim('torus', 'link%d' % i, (0, 0, 0), (.06, .06, .06), mat('steel', (.7, .72, .75), .25, 1), rot=(0, 0, 0), major_radius=1, minor_radius=.3) for i in range(10)]
spd = bpy.data.lights.new('spot', 'SPOT'); spd.spot_size = math.radians(14); spd.spot_blend = .35; spd.color = (1, .95, .8); spd.shadow_soft_size = .2
SPOT = bpy.data.objects.new('spot', spd); sc.collection.objects.link(SPOT)
for f, v in ((1, 40000), (FOOL - 1, 40000), (FOOL, 220000), (FOOL + 5, 110000), (NF + 1, 110000)): spd.energy = v; spd.keyframe_insert('energy', frame=f)
for f, v in ((FOOL - 1, 25), (FOOL, 90), (FOOL + 4, 45)): SPOTM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = v; SPOTM.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
s2 = bpy.data.lights.new('hit', 'SPOT'); s2.spot_size = math.radians(22); s2.spot_blend = .4; s2.color = (1, .93, .78); s2.shadow_soft_size = .3
HIT = bpy.data.objects.new('hit', s2); sc.collection.objects.link(HIT)
for f, v in ((1, 0), (FOOL - 1, 0), (FOOL, 9000), (FOOL + 6, 4500), (NF + 1, 4500)): s2.energy = v; s2.keyframe_insert('energy', frame=f)
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'HORIZONTAL'; cd.clip_end = 2000
tgt = empty('target'); tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def vlerp(a, b, k): return Vector(a).lerp(Vector(b), k)

def on_frame(s, *a):
    f = s.frame_current; t = f / 30; q = (f - 1) / max(1, NF - 1)
    oc.time = 1 + t
    drift = Vector((.03 * f, .05 * f, 0)) if SHOT == 'release' else Vector((.008 * f, .012 * f, 0))
    base = Vector((0, 0, 0)) if SHOT == 'hook' else Vector((-4, 18, 0))
    FIG.location = base + drift + Vector((0, 0, .05 + .14 * math.sin(t * 1.6)))
    FIG.rotation_euler = (.06 * math.sin(t * 1.3), .05 * math.sin(t * 1.1 + 1), math.radians(35))
    CASE.location = FIG.location + Vector((-.2, -1.6, .05 + .12 * math.sin(t * 1.6 + .8)))
    CASE.rotation_euler = (.12 * math.sin(t * 1.4), .1 * math.sin(t * 1.2 + .5), math.radians(20) + .1 * math.sin(t * .7))
    bpy.context.view_layer.update()
    wrist = FIG.matrix_world @ Vector((.3, -.95, -.05)); handle = CASE.matrix_world @ Vector((0, 0, .36))
    for i, o in enumerate(CHAIN):
        k = (i + .5) / len(CHAIN); p = wrist.lerp(handle, k); p.z -= .18 * math.sin(math.pi * k)
        o.location = p; o.rotation_euler = (math.pi / 2 * (i % 2), 0, math.atan2(handle.y - wrist.y, handle.x - wrist.x))
    SUB.location.z = .1 * math.sin(t * .9)
    lamp = SUB.matrix_world @ Vector((4.4, 0, 6.2)); SPOT.location = lamp + (CASE.location - lamp).normalized() * 1.2
    sweep = Vector((0, 0, 0)) if f >= FOOL else Vector((5 * math.cos(t * 2.4), 4 * math.sin(t * 2.4) + 3, 0)) * (1 - f / FOOL) ** .5
    d = (CASE.location + sweep - lamp).normalized(); SPOT.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    HIT.location = CASE.location + Vector((5, -5, 6)); HIT.rotation_euler = (CASE.location - HIT.location).normalized().to_track_quat('-Z', 'Y').to_euler()
    if SHOT == 'hook':
        k = smooth((f - 60) / 120)
        cd.lens = 42 - 16 * k
        cam.location = CASE.location + vlerp((2.2, -2.2, .6), (-9, -16, 5), k)
        tgt.location = CASE.location + vlerp((.4, .8, .2), (7, 7, 1.5), k)
    else:
        cd.lens = 28
        cam.location = Vector((-30, -10, 6)) + Vector((4 * q, 0, -.5 * q)); tgt.location = Vector((6, 16, 1.5))
bpy.app.handlers.frame_change_pre.append(on_frame)
still = arg('--still'); want = sorted(int(x) for x in still.split(',')) if still else None
for f in range(1, (want[-1] if want else NF) + 1):
    if want and f not in want: continue
    sc.frame_set(f); on_frame(sc)
    sc.render.filepath = os.path.join(OUT, ('still_' if want else 'f_') + f'{f:04d}.png')
    bpy.ops.render.render(write_still=True)
print('COMPLETE', SHOT, flush=True)

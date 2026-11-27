"""S10 Doss. Hook 3D: Doss arriba del acantilado baja a un herido con una cuerda mientras explotan granadas.
blender -b -P blender_doss.py -- --shot hook --out ABS [--still 1,24] [--res .5] [--samples 24]
"""
import bpy, math, os, sys, random
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
COUNTS = {'hook': 236}
SHOT = arg('--shot', 'hook'); NF = int(arg('--frames', COUNTS[SHOT])); OUT = arg('--out')
assert OUT and os.path.isabs(OUT), 'pasar --out absoluto'
os.makedirs(OUT, exist_ok=True); RES = float(arg('--res', 1)); random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = int(1080 * RES); sc.render.resolution_y = int(1920 * RES)
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = NF
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.eevee.taa_render_samples = int(arg('--samples', 24))
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .35

def mat(name, rgb, rough=.6, emit=0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*(ecol or rgb), 1); b.inputs['Emission Strength'].default_value = emit
    return m
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o
def prim(kind, name, loc, scale, m, parent=None, rot=(0, 0, 0), smooth=False, **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=loc, rotation=rot, **kw); o = bpy.context.object; o.name = name
    o.scale = scale; o.data.materials.append(m); o.parent = parent
    if smooth: bpy.ops.object.shade_smooth()
    return o

# --- cielo de atardecer con humo
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
bg = nt.nodes['Background']; tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); cr = N('ShaderNodeValToRGB')
L(tc.outputs['Generated'], sp.inputs[0]); L(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = .45; cr.color_ramp.elements[0].color = (.95, .42, .12, 1)
cr.color_ramp.elements[1].position = .72; cr.color_ramp.elements[1].color = (.08, .06, .12, 1)
L(cr.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = .9
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 1.5; sd.color = (1, .6, .35); sd.angle = .08
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(70), 0, math.radians(-35))
fd = bpy.data.lights.new('fill', 'SUN'); fd.energy = .6; fd.color = (.5, .6, 1)
fill = bpy.data.objects.new('fill', fd); sc.collection.objects.link(fill); fill.rotation_euler = (math.radians(60), 0, math.radians(160))

# --- acantilado: cara en y=0 mirando a -Y, cima a z=H
H = 8
ROCK = mat('rock', (.12, .1, .09), .95); ROCK2 = mat('rock2', (.17, .14, .12), .95); TOP = mat('top', (.22, .2, .12), .95); GROUND = mat('ground', (.16, .14, .1), .95)
cliff = prim('cube', 'cliff', (0, 6, H / 2), (40, 6, H / 2), ROCK)
tx = bpy.data.textures.new('rk', 'CLOUDS'); tx.noise_scale = 1.6
for i in range(26):   # estratos y salientes de la pared
    prim('cube', 'r%d' % i, (random.uniform(-12, 12), -.1, random.uniform(.5, H - .4)), (random.uniform(1, 4), random.uniform(.15, .45), random.uniform(.15, .6)), ROCK2 if i % 2 else ROCK, rot=(0, random.uniform(-.15, .15), 0))
prim('plane', 'plateau', (0, 6, H + .05), (40, 6, 1), TOP)
prim('plane', 'ground', (0, -20, 0), (60, 30, 1), GROUND)

# --- stickmen 3D (cabeza redonda blanca, ojos de punto)
WHITE = mat('white', (.95, .95, .93), .5); BLACK = mat('black', (.01, .01, .01), .4)
OLIVE = mat('olive', (.25, .27, .13), .7); RED = mat('red', (.8, .05, .04), .5)
def stick(name, helmet=True, cross=False, eyes_closed=False):
    R = empty(name)
    prim('uv_sphere', name + 'body', (0, 0, .75), (.26, .2, .42), OLIVE, R, smooth=True, segments=16, ring_count=8)
    prim('uv_sphere', name + 'head', (0, 0, 1.42), (.3,) * 3, WHITE, R, smooth=True, segments=20, ring_count=10)
    for s in (-1, 1):
        prim('uv_sphere', name + 'eye', (s * .1, -.29, 1.46), (.05, .035, .06 if not eyes_closed else .015), BLACK, R, segments=8, ring_count=6)
    if helmet:
        prim('uv_sphere', name + 'helm', (0, 0, 1.55), (.34, .34, .22), OLIVE, R, smooth=True, segments=16, ring_count=8)
        if cross:
            prim('cylinder', name + 'disc', (0, -.3, 1.66), (.11, .11, .01), WHITE, R, rot=(math.pi / 2 - .5, 0, 0), vertices=16)
            for sx, sz in ((.075, .02), (.02, .075)):
                prim('cube', name + 'x', (0, -.315, 1.66), (sx, .01, sz), RED, R, rot=(-.5, 0, 0))
    arms = []
    for s in (-1, 1):
        sh = empty(name + 'sh', (s * .27, 0, 1.0), R); arms.append(sh)
        prim('cylinder', name + 'arm', (0, 0, -.28), (.07, .07, .28), OLIVE, sh, vertices=8)
    legs = []
    for s in (-1, 1):
        hp = empty(name + 'hp', (s * .12, 0, .4), R); legs.append(hp)
        prim('cylinder', name + 'leg', (0, 0, -.25), (.08, .08, .25), OLIVE, hp, vertices=8)
    return R, arms, legs

DOSS, DARMS, DLEGS = stick('doss', cross=True)
DOSS.location = (0, .35, H); DOSS.scale = (2,) * 3
for a in DARMS: a.rotation_euler = (1.9, 0, 0)          # brazos hacia adelante, sujetando la cuerda
for l in DLEGS: l.rotation_euler = (1.3, 0, 0)          # de rodillas
MAN, MARMS, MLEGS = stick('man', eyes_closed=True)
MAN.scale = (2,) * 3
prim('cube', 'bandage', (0, -.05, 1.64), (.31, .31, .06), WHITE, MAN)
ROPE_M = mat('rope', (.62, .5, .3), .9)
ROPE = prim('cylinder', 'rope', (0, 0, 0), (.045, .045, 1), ROPE_M, vertices=8)

# --- explosiones cartoon (como S08) y trazadoras
EXPL = []
def explode(loc, f0, big=1.0):
    rnd = random.Random(f0); A = empty('ex%d' % f0, loc)
    FM = [mat('fy%d' % f0, (1, .55, .03), emit=.8, ecol=(1, .4, 0)), mat('fo%d' % f0, (.95, .2, 0), emit=.6, ecol=(1, .16, 0))]
    SMK = mat('sm%d' % f0, (.14, .13, .13), .95)
    for j in range(8):
        off = Vector((rnd.uniform(-1.2, 1.2), rnd.uniform(-1, 1), rnd.uniform(0, 1.8))) * big; r = rnd.uniform(1, 2) * big
        o = prim('ico_sphere', 'fb', off, (.01,) * 3, FM[j % 2], A, smooth=True, subdivisions=2); d0 = f0 + rnd.randint(0, 2)
        for f, k in ((d0 - 1, .01), (d0 + 2, r), (d0 + 7, r * 1.2), (d0 + 15, r * .6), (d0 + 20, .01)): o.scale = (k,) * 3; o.keyframe_insert('scale', frame=f)
    for j in range(7):
        off = Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1, 1), rnd.uniform(.5, 3))) * big; r = rnd.uniform(1.3, 2.4) * big
        o = prim('ico_sphere', 'sk', off, (.01,) * 3, SMK, A, smooth=True, subdivisions=2); o.visible_shadow = False; d0 = f0 + 5 + rnd.randint(0, 5)
        for f, k in ((d0 - 1, .01), (d0 + 6, r), (d0 + 45, r * 1.4), (d0 + 100, r * .5), (d0 + 120, .01)): o.scale = (k,) * 3; o.keyframe_insert('scale', frame=f)
    ld = bpy.data.lights.new('exl', 'POINT'); ld.color = (1, .55, .2); ld.shadow_soft_size = 3
    lo = bpy.data.objects.new('exl', ld); sc.collection.objects.link(lo); lo.parent = A; lo.location = (0, 0, 1.5)
    for f, v in ((f0 - 1, 0), (f0, 15000 * big), (f0 + 6, 6000 * big), (f0 + 20, 3000), (f0 + 30, 0)): ld.energy = v; ld.keyframe_insert('energy', frame=f)
    EXPL.append(A)
# frames: impacto en f4, "Without a gun" f98, "cliff" f154, "One by one" f191
for loc, f0, b in (((-3.3, -.9, H + .1), 1, 1.15), ((2.8, .8, H + .2), 98, 1.0), ((-3.6, .5, H + .2), 154, 1.0), ((3.4, .6, H + .2), 191, .9), ((2.6, -.6, H - 4), 60, .6)):
    explode(loc, f0, b)
TRM = mat('tracer', (1, .7, .25), emit=40, ecol=(1, .62, .18))
TRACERS = [(prim('cylinder', 'tr%d' % i, (0, 0, -99), (.07, .07, 1.8), TRM, vertices=6), random.uniform(0, 230), random.uniform(H + 1.5, H + 6), random.uniform(1.5, 6), random.choice((-1, 1))) for i in range(18)]

cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'HORIZONTAL'; cd.clip_end = 500
tgt = empty('target'); tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def vlerp(a, b, k): return Vector(a).lerp(Vector(b), k)

def on_frame(s, *a):
    f = s.frame_current; t = f / 30; q = (f - 1) / max(1, NF - 1)
    # el herido baja de la cima casi hasta el suelo, con balanceo
    z = H - 3.6 - (H - 5.5) * smooth(q * 1.05)
    MAN.location = (.25 * math.sin(t * 2.1), -.9, z); MAN.rotation_euler = (.35 + .08 * math.sin(t * 2.6), .12 * math.sin(t * 2.1), 0)
    for i, l in enumerate(MLEGS): l.rotation_euler = (.6 + .1 * math.sin(t * 3 + i), 0, 0)
    for i, a_ in enumerate(MARMS): a_.rotation_euler = (.3, 0, (-1) ** i * .4)
    DOSS.rotation_euler = (.3 + .06 * math.sin(t * 5), 0, 0)   # tirando hacia atrás
    hands = Vector((0, -.6, H + 1.3)); knot = MAN.location + Vector((0, 0, 2.7))
    d = knot - hands; ROPE.location = (hands + knot) / 2; ROPE.scale = (.045, .045, d.length / 2)
    ROPE.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    k = smooth(q)
    cd.lens = 27 + 4 * k
    shake = Vector((0, 0, 0))
    for f0 in (2, 98, 154, 191):
        if 0 <= f - f0 < 10: shake += Vector((random.uniform(-1, 1), 0, random.uniform(-1, 1))) * .12 * (1 - (f - f0) / 10)
    cam.location = vlerp((2.2, -9.5, 3.2), (1.6, -8.0, 3.4), k) + shake
    tgt.location = Vector((0, 0, (H + 2 + MAN.location.z) / 2 + .3))
    for o, ph, zz, sp_, dr in TRACERS:
        u = (f + ph) % 40 / 40
        o.location = (dr * (-16 + 32 * u), sp_, zz); o.rotation_euler = (0, math.pi / 2, 0)
bpy.app.handlers.frame_change_pre.append(on_frame)
still = arg('--still'); want = sorted(int(x) for x in still.split(',')) if still else None
frm = int(arg('--from', 1)); to = int(arg('--to', NF))
for f in range(1, (want[-1] if want else to) + 1):
    sc.frame_set(f); on_frame(sc)
    if want and f not in want: continue
    if not want and f < frm: continue
    sc.render.filepath = os.path.join(OUT, ('still_' if want else 'f_') + f'{f:04d}.png')
    bpy.ops.render.render(write_still=True)
print('COMPLETE', SHOT, flush=True)

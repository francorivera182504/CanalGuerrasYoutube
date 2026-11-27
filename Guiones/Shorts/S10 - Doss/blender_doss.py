"""S10 Doss v2. Hook 3D de PERFIL: meseta a la izquierda (x<0), pared vertical en x=0, vacío a la derecha.
Doss de rodillas en el borde baja con una cuerda a un herido; explosiones detrás de él sobre la meseta.
blender -b -P blender_doss.py -- --shot hook --out ABS [--still 1,24] [--res .5] [--samples 24] [--from N]
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
sc.view_settings.view_transform = 'Standard'
sc.eevee.taa_render_samples = int(arg('--samples', 24))
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .3

def mat(name, rgb, rough=.7, emit=0, ecol=None):
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

# --- cielo de atardecer claro (contraste con las siluetas)
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
bg = nt.nodes['Background']; tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); cr = N('ShaderNodeValToRGB')
L(tc.outputs['Generated'], sp.inputs[0]); L(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = .44; cr.color_ramp.elements[0].color = (1.0, .62, .3, 1)
cr.color_ramp.elements[1].position = .56; cr.color_ramp.elements[1].color = (.2, .16, .38, 1)
L(cr.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
def sun(name, e, col, rot):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = e; d.color = col; d.angle = .1
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
sun('key', 2.2, (1, .82, .62), (55, 0, -50))
sun('rim', 3.0, (1, .6, .3), (70, 0, 150))
sun('fill', .5, (.6, .7, 1), (40, 0, 20))

# --- acantilado: bloque x∈[-30,0], y∈[-6,40], z∈[0,H]; la cara y=-6 es el perfil que ve la cámara
H = 9
WALL = mat('wall', (.36, .28, .2), .95); STRATA = mat('strata', (.25, .19, .14), .95); TOPM = mat('top', (.2, .26, .1), .95)
GROUND = mat('ground', (.24, .2, .14), .95); HILL = mat('hill', (.42, .3, .28), .95)
prim('cube', 'cliff', (-15, 17, H / 2), (15, 23, H / 2), WALL)
for i in range(16):
    z = .3 + i * H / 16 + random.uniform(-.1, .1)
    wd = random.uniform(2, 6); prim('cube', 's%d' % i, (-wd - random.uniform(.1, 1.5), -6.05, z), (wd, .08, random.uniform(.06, .16)), STRATA)
for i in range(14):
    prim('cube', 'w%d' % i, (.05, random.uniform(-5.5, 10), random.uniform(.5, H - .6)), (.22, random.uniform(.4, 1.6), random.uniform(.12, .4)), STRATA)
prim('cube', 'turf', (-15, 17, H + .06), (15.02, 23.02, .08), TOPM)
GRASS = mat('grass', (.25, .35, .1), .9)
for i in range(40):
    prim('cone', 'g', (random.uniform(-9, -.3), random.uniform(-5.9, 0), H + .2), (.07, .07, random.uniform(.15, .35)), GRASS, vertices=5)
prim('plane', 'ground', (30, 17, 0), (30, 40, 1), GROUND)
for i in range(6):
    prim('uv_sphere', 'h%d' % i, (random.uniform(-10, 40), 140 + i * 10, -6), (random.uniform(18, 30), 6, random.uniform(9, 16)), HILL, smooth=True)

# --- stickmen 3D
WHITE = mat('white', (.97, .97, .95), .5); BLACK = mat('black', (.01, .01, .01), .4)
OLIVE = mat('olive', (.38, .4, .2), .7); RED = mat('red', (.85, .05, .04), .5); BAND = mat('band', (.97, .97, .95), .6)
def stick(name, cross=False, eyes_closed=False):
    R = empty(name)
    prim('uv_sphere', name + 'body', (0, 0, .75), (.26, .2, .42), OLIVE, R, smooth=True, segments=16, ring_count=8)
    prim('uv_sphere', name + 'head', (0, 0, 1.42), (.3,) * 3, WHITE, R, smooth=True, segments=20, ring_count=10)
    for s in (-1, 1):
        prim('uv_sphere', name + 'eye', (s * .1, -.29, 1.44), (.05, .035, .065 if not eyes_closed else .016), BLACK, R, segments=8, ring_count=6)
    prim('uv_sphere', name + 'helm', (0, 0, 1.56), (.34, .34, .22), OLIVE, R, smooth=True, segments=16, ring_count=8)
    if cross:
        prim('cylinder', name + 'disc', (0, -.28, 1.66), (.14, .14, .012), WHITE, R, rot=(math.pi / 2 - .45, 0, 0), vertices=20)
        for sx, sz in ((.1, .028), (.028, .1)):
            prim('cube', name + 'x', (0, -.297, 1.66), (sx, .012, sz), RED, R, rot=(-.45, 0, 0))
        prim('cylinder', name + 'arm_band', (.27, 0, .82), (.085, .085, .06), BAND, R, vertices=10)
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
DOSS.location = (-.75, -5.2, H + .1); DOSS.scale = (1.25,) * 3
for l in DLEGS: l.rotation_euler = (1.4, 0, 0)
MAN, MARMS, MLEGS = stick('man', eyes_closed=True)
MAN.scale = (1.15,) * 3
prim('cube', 'bandage', (0, -.02, 1.36), (.31, .31, .07), WHITE, MAN)
ROPEM = mat('rope', (.85, .7, .45), .9)
ROPE = prim('cylinder', 'rope', (0, 0, 0), (.035, .035, 1), ROPEM, vertices=8)
prim('torus', 'loop', (0, 0, .95), (.33, .28, .5), ROPEM, MAN, major_radius=1, minor_radius=.12)

# --- explosiones cartoon detrás de Doss
FIREY = mat('fy', (1, .5, 0), emit=1.1, ecol=(1, .42, 0)); FIREO = mat('fo', (.95, .15, 0), emit=1.0, ecol=(1, .12, 0))
SMK = mat('smk', (.22, .21, .21), .95)
def explode(loc, f0, big=1.0):
    rnd = random.Random(f0); A = empty('ex%d' % f0, loc)
    for j in range(7):
        off = Vector((rnd.uniform(-.8, .8), rnd.uniform(-.6, .6), rnd.uniform(0, 1.2))) * big; r = rnd.uniform(.5, .9) * big
        o = prim('ico_sphere', 'fb', off, (.01,) * 3, (FIREY, FIREO)[j % 2], A, smooth=True, subdivisions=2); d0 = f0 + rnd.randint(0, 2)
        for f, k in ((d0 - 1, .01), (d0 + 2, r), (d0 + 6, r * 1.15), (d0 + 12, r * .5), (d0 + 16, .01)): o.scale = (k,) * 3; o.keyframe_insert('scale', frame=f)
    for j in range(6):
        o = prim('ico_sphere', 'sk', (rnd.uniform(-.3, .3), rnd.uniform(-.3, .3), .6), (.01,) * 3, SMK, A, smooth=True, subdivisions=2); o.visible_shadow = False
        d0 = f0 + 4 + j * 2; r = (.5 + .08 * j) * big
        for f, k, z in ((d0 - 1, .01, .6), (d0 + 6, r, 1 + j * .45 * big), (d0 + 60, r * 1.3, 2.5 + j * .7 * big), (d0 + 110, .01, 4 + j * big)):
            o.scale = (k,) * 3; o.location.z = z; o.keyframe_insert('scale', frame=f); o.keyframe_insert('location', frame=f)
    for j in range(8):
        o = prim('ico_sphere', 'dirt', (0, 0, -5), (.09,) * 3, STRATA, A, subdivisions=1); v = Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1, 1), rnd.uniform(2, 4)))
        o.keyframe_insert('location', frame=f0 - 1)
        for n in (0, 4, 8, 12, 16):
            o.location = v * n / 15 + Vector((0, 0, -9.8 * (n / 15) ** 2)); o.keyframe_insert('location', frame=f0 + n)
        o.location = (0, 0, -5); o.keyframe_insert('location', frame=f0 + 17)
    ld = bpy.data.lights.new('exl', 'POINT'); ld.color = (1, .55, .2); ld.shadow_soft_size = 1.5
    lo = bpy.data.objects.new('exl', ld); sc.collection.objects.link(lo); lo.parent = A; lo.location = (0, 0, 1)
    for f, v in ((f0 - 1, 0), (f0, 4000 * big), (f0 + 6, 1500 * big), (f0 + 16, 0)): ld.energy = v; ld.keyframe_insert('energy', frame=f)
BOOMS = [((-2.6, -3.4, H), 1, 1.45), ((-6.5, -2.5, H), 98, 1.1), ((-2.8, -1.5, H), 154, .9), ((-5.2, -4.2, H), 191, 1.0)]
for loc, f0, b in BOOMS: explode(loc, f0, b)
TRM = mat('tracer', (1, .75, .3), emit=25, ecol=(1, .65, .2))
TRACERS = [(prim('cylinder', 'tr%d' % i, (0, 0, -99), (.035, .035, .9), TRM, vertices=6), random.uniform(0, 236), random.uniform(H + 1.2, H + 5), random.uniform(-4, 3)) for i in range(10)]
PEB = [prim('ico_sphere', 'pb%d' % i, (0, 0, -99), (.08,) * 3, STRATA, subdivisions=1) for i in range(8)]

cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'HORIZONTAL'; cd.clip_end = 600
tgt = empty('target'); tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def on_frame(s, *a):
    f = s.frame_current; t = f / 30; q = (f - 1) / max(1, NF - 1)
    z = H - 3.0 - (H - 5.6) * smooth(q)
    MAN.location = (.75 + .1 * math.sin(t * 2.2), -5.2, z); MAN.rotation_euler = (0, .1 * math.sin(t * 2.2), 0)
    for i, l in enumerate(MLEGS): l.rotation_euler = (.25 + .1 * math.sin(t * 3 + i), 0, 0)
    for i, a_ in enumerate(MARMS): a_.rotation_euler = (0, 0, (-1) ** i * .5)
    pull = math.sin(t * 5)
    DOSS.rotation_euler = (0, -.25 - .06 * pull, 0)
    for a_ in DARMS: a_.rotation_euler = (0, -1.5 - .15 * pull, 0)
    bpy.context.view_layer.update()
    hands = DOSS.matrix_world @ Vector((.55, 0, .75)); knot = MAN.location + Vector((0, 0, 1.75))
    d = knot - hands; ROPE.location = (hands + knot) / 2; ROPE.scale = (.035, .035, d.length / 2)
    ROPE.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    k = smooth(q); shake = Vector((0, 0, 0))
    for _, f0, b in BOOMS:
        if 0 <= f - f0 < 8: shake += Vector((random.uniform(-1, 1), 0, random.uniform(-1, 1))) * .06 * (1 - (f - f0) / 8)
    cd.lens = 80 + 10 * k
    cam.location = Vector((1.2, -24, H * .52)) + shake
    tgt.location = Vector((-.1, -5.2, (H + 1.6 + MAN.location.z) / 2 - .9))
    for o, ph, zz, y in TRACERS:
        u = (f + ph) % 24 / 24; o.location = (-12 + 22 * u, y - 4, zz); o.rotation_euler = (0, math.pi / 2, 0)
    for i, o in enumerate(PEB):
        u = ((f + i * 29) % 45) / 45; o.location = (.25 + .2 * (i % 3), -5.4 + .15 * (i % 2), H - 9.8 * (u * 1.5) ** 2 * 1.2)
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

"""S08 Howard. P-51 contra cazas alemanes sobre nubes. 1 u = 1 m, los aviones vuelan hacia +X.
Marco relativo: los aviones casi quietos, las nubes se desplazan hacia -X (sensación de velocidad).
blender -b -P blender_howard.py -- --shot hook|dive --out ABS [--still 1,24] [--res .5] [--samples 24]
"""
import bpy, math, os, sys, random
from mathutils import Vector, Euler
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None): return argv[argv.index(k) + 1] if k in argv else d
COUNTS = {'hook': 204, 'dive': 172}
SHOT = arg('--shot', 'hook'); NF = int(arg('--frames', COUNTS[SHOT])); OUT = arg('--out')
assert OUT and os.path.isabs(OUT), 'pasar --out absoluto'
os.makedirs(OUT, exist_ok=True); RES = float(arg('--res', 1)); random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = int(1080 * RES); sc.render.resolution_y = int(1920 * RES)
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = NF
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
ee = sc.eevee; ee.taa_render_samples = int(arg('--samples', 24)); ee.volumetric_end = 260; ee.volumetric_samples = 32
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .35

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    return m, nt, nt.nodes['Material Output']
def mat(name, rgb, rough=.55, metal=0, emit=0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = (*(ecol or rgb), 1); b.inputs['Emission Strength'].default_value = emit
    return m
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); sc.collection.objects.link(o); o.location = loc; o.parent = parent; return o
def prim(kind, name, loc, scale, m, parent, rot=(0, 0, 0), smooth=False, **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=loc, rotation=rot, **kw); o = bpy.context.object; o.name = name
    o.scale = scale; o.data.materials.append(m); o.parent = parent
    if smooth: bpy.ops.object.shade_smooth()
    return o

GLASS = mat('glass', (.08, .12, .16), .1, .3); DARK = mat('dark', (.03, .03, .035), .5); METAL = mat('metal', (.5, .5, .52), .35, .8)
def aircraft(name, top, nose, length=9.8, span=11.3, belly=None, scoop=False, engines=None):
    """Avión de primitivas, morro hacia +X. Devuelve (raíz, hélices, piezas, cañones locales)."""
    R = empty(name); body = mat(name + 'body', top, .55); nm = mat(name + 'nose', nose, .5)
    parts = [prim('uv_sphere', name + 'fus', (0, 0, 0), (length / 2, length * .072, length * .085), body, R, smooth=True, segments=24, ring_count=12)]
    if belly: parts.append(prim('uv_sphere', name + 'belly', (0, 0, -length * .03), (length * .48, length * .068, length * .06), mat(name + 'b', belly, .6), R, smooth=True))
    parts.append(prim('cone', name + 'spin', (length / 2 + .2, 0, 0), (length * .05, length * .05, .55), nm, R, rot=(0, math.pi / 2, 0), vertices=20, radius1=1, depth=1))
    parts.append(prim('cube', name + 'wing', (length * .06, 0, -length * .045), (length * .1, span / 2, .09), body, R))
    parts.append(prim('cube', name + 'hstab', (-length * .44, 0, length * .02), (length * .055, span * .19, .06), body, R))
    parts.append(prim('cube', name + 'fin', (-length * .44, 0, length * .1), (length * .065, .06, length * .085), body, R, rot=(0, -.25, 0)))
    parts.append(prim('uv_sphere', name + 'canopy', (length * .06, 0, length * .075), (length * .12, length * .04, length * .045), GLASS, R, smooth=True))
    if scoop: parts.append(prim('cube', name + 'scoop', (-length * .08, 0, -length * .1), (length * .1, length * .03, length * .03), body, R))
    props = []
    for (px, py, pz) in (engines or [(length / 2 + .15, 0, 0)]):
        hub = empty(name + 'hub', (px, py, pz), R); props.append(hub)
        for k in range(3):
            parts.append(prim('cube', name + 'blade', (0, 0, 0), (.06, .14, length * .155), DARK, hub, rot=(k * 2 * math.pi / 3, 0, 0)))
    if engines:
        for (px, py, pz) in engines:
            parts.append(prim('cylinder', name + 'nac', (px - 1.2, py, pz), (.55, .55, 1.3), body, R, rot=(0, math.pi / 2, 0), vertices=16))
    guns = [Vector((length * .14, s * d, -length * .045)) for s in (-1, 1) for d in (span * .2, span * .25)]
    return R, props, parts, guns

OLIVE, GREYB = (.21, .23, .12), (.42, .44, .45)
P51, P51P, _, GUNS = aircraft('p51', OLIVE, (.75, .75, .72), belly=GREYB, scoop=True)
FIGHTERS = []
def fighter(loc, scale=1.0):
    R, props, parts, _ = aircraft('bf%d' % len(FIGHTERS), (.30, .34, .27), (.95, .78, .10), length=8.9, span=9.9, belly=(.55, .6, .62))
    R.scale = (scale,) * 3
    FIGHTERS.append(dict(R=R, props=props, parts=parts, base=Vector(loc), ph=random.uniform(0, 6), dead=None)); return FIGHTERS[-1]
BOMBERS = []
if SHOT == 'dive':
    for loc in ((38, 4, -16), (58, 22, -19), (70, -14, -21)):
        e = [(22 * .5 * .2, y, -.3) for y in (-5.2, -9.5, 5.2, 9.5)]
        R, props, parts, _ = aircraft('b17_%d' % len(BOMBERS), OLIVE, (.55, .55, .5), length=22.6, span=31.6, belly=GREYB, engines=e)
        BOMBERS.append(dict(R=R, props=props, base=Vector(loc), ph=random.uniform(0, 6)))

# --- cielo, sol y nubes
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
bg = nt.nodes['Background']; tc = N('ShaderNodeTexCoord'); sp = N('ShaderNodeSeparateXYZ'); cr = N('ShaderNodeValToRGB')
L(tc.outputs['Generated'], sp.inputs[0]); L(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = .0; cr.color_ramp.elements[0].color = (.55, .68, .82, 1)
cr.color_ramp.elements[1].position = .5; cr.color_ramp.elements[1].color = (.04, .14, .42, 1)
L(cr.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.0; sd.color = (1, .93, .82); sd.angle = .05
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(30))
CLOUD = mat('cloud', (.8, .83, .88), .9); CLOUDS = []
deck_m, dnt, dout = node_mat('deck'); b = dnt.nodes.new('ShaderNodeBsdfPrincipled'); nz = dnt.nodes.new('ShaderNodeTexNoise'); ramp = dnt.nodes.new('ShaderNodeValToRGB')
nz.inputs['Scale'].default_value = 300; nz.inputs['Detail'].default_value = 8; dnt.links.new(nz.outputs['Fac'], ramp.inputs[0])
ramp.color_ramp.elements[0].position = .4; ramp.color_ramp.elements[0].color = (.18, .26, .36, 1); ramp.color_ramp.elements[1].position = .6; ramp.color_ramp.elements[1].color = (.7, .74, .8, 1)
tcd = dnt.nodes.new('ShaderNodeTexCoord'); dnt.links.new(tcd.outputs['Object'], nz.inputs['Vector'])
dnt.links.new(ramp.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .95; dnt.links.new(b.outputs[0], dout.inputs['Surface'])
DECK = prim('plane', 'deck', (0, 0, -60), (2000, 2000, 1), deck_m, None)
for i in range(22):
    r = random.uniform(6, 18)
    o = prim('ico_sphere', 'cl%d' % i, (random.uniform(-150, 450), random.uniform(-160, 160), random.uniform(-48, -26)), (r * 2.2, r * 1.3, r * .35), CLOUD, None, smooth=True, subdivisions=3)
    o.visible_shadow = False; CLOUDS.append((o, o.location.copy()))

# --- trazadoras y fogonazos
TRACER = mat('tracer', (1, .7, .25), emit=40, ecol=(1, .62, .18)); FLASH = mat('flash', (1, .8, .4), emit=60, ecol=(1, .7, .3))
POOL = [prim('cylinder', 'tr%d' % i, (0, 0, -999), (.13, .13, 3.2), TRACER, None, vertices=6) for i in range(56)]
FL = [prim('uv_sphere', 'fl%d' % i, (0, 0, 0), (.4, .25, .25), FLASH, P51, segments=8, ring_count=6) for i in range(4)]
for i, o in enumerate(FL): o.location = GUNS[i] + Vector((1.3, 0, 0))
BURSTS = []   # (frame inicial, frame final, índice del caza objetivo)

# --- explosión en el aire (volumen procedural, como S04)
def vol_ball(name, parent, dens, col, emit, ecol, emit_keys, dens_keys, scale_keys, nscale=2.2):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0)); d = bpy.context.object; d.name = name; d.parent = parent
    m, nt, out = node_mat(name + 'M'); N = nt.nodes.new; Lk = nt.links.new
    tcn = N('ShaderNodeTexCoord'); ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; Lk(tcn.outputs['Object'], ln.inputs[0])
    def mth(op, a, b):
        n = N('ShaderNodeMath'); n.operation = op; n.use_clamp = True
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: Lk(v, n.inputs[i])
        return n.outputs[0]
    mask = mth('POWER', mth('SUBTRACT', 1.0, ln.outputs['Value']), 1.6)
    nzn = N('ShaderNodeTexNoise'); nzn.noise_dimensions = '4D'; nzn.inputs['Scale'].default_value = nscale; nzn.inputs['Detail'].default_value = 8
    Lk(tcn.outputs['Object'], nzn.inputs['Vector'])
    g = mth('SUBTRACT', mth('MULTIPLY', nzn.outputs['Fac'], 3.2), 1.2); mg = mth('MULTIPLY', mask, g)
    fv = N('ShaderNodeValue'); ev = N('ShaderNodeValue'); pv = N('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (*col, 1)
    dn = N('ShaderNodeMath'); dn.operation = 'MULTIPLY'; Lk(mg, dn.inputs[0]); dn.inputs[1].default_value = dens
    dn2 = N('ShaderNodeMath'); dn2.operation = 'MULTIPLY'; Lk(dn.outputs[0], dn2.inputs[0]); Lk(fv.outputs[0], dn2.inputs[1]); Lk(dn2.outputs[0], pv.inputs['Density'])
    if emit:
        pv.inputs['Emission Color'].default_value = (*ecol, 1); em = N('ShaderNodeMath'); em.operation = 'MULTIPLY'
        Lk(mg, em.inputs[0]); Lk(ev.outputs[0], em.inputs[1]); Lk(em.outputs[0], pv.inputs['Emission Strength'])
        for f, v in emit_keys: ev.outputs[0].default_value = v; ev.outputs[0].keyframe_insert('default_value', frame=f)
    for f, v in dens_keys: fv.outputs[0].default_value = v; fv.outputs[0].keyframe_insert('default_value', frame=f)
    nzn.inputs['W'].default_value = 0; nzn.inputs['W'].keyframe_insert('default_value', frame=1)
    nzn.inputs['W'].default_value = NF / 30; nzn.inputs['W'].keyframe_insert('default_value', frame=NF)
    for f, s in scale_keys: d.scale = s; d.keyframe_insert('scale', frame=f)
    Lk(pv.outputs['Volume'], out.inputs['Volume']); d.data.materials.append(m); return d
EXPL = []
def explode(fi, f0):
    """El caza fi revienta en f0: bola de fuego, humo negro, piezas sueltas, luz."""
    F = FIGHTERS[fi]; F['dead'] = f0; anchor = empty('ex%d' % fi); EXPL.append((anchor, fi, f0))
    # explosión cartoon: bolas emisivas que crecen y se apagan + humo gris que se expande (estilo Stick)
    rnd = random.Random(fi)
    FIREM = [mat('fy%d' % fi, (1, .8, .1), emit=6, ecol=(1, .55, 0)), mat('fo%d' % fi, (1, .3, 0), emit=5, ecol=(1, .16, 0))]
    SMK = mat('sm%d' % fi, (.16, .15, .15), .95)
    for j in range(9):
        off = Vector((rnd.uniform(-1.6, 1.6), rnd.uniform(-1.6, 1.6), rnd.uniform(-1.2, 1.6))); r = rnd.uniform(1.4, 2.6)
        o = prim('ico_sphere', 'fb%d_%d' % (fi, j), off, (.01,) * 3, FIREM[j % 2], anchor, smooth=True, subdivisions=2)
        d0 = f0 + rnd.randint(0, 3)
        for f, k in ((d0 - 1, .01), (d0 + 2, r), (d0 + 7, r * 1.25), (d0 + 16, r * .7), (d0 + 22, .01)):
            o.scale = (k,) * 3; o.keyframe_insert('scale', frame=f)
    for j in range(8):
        off = Vector((rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-1, 2.5))); r = rnd.uniform(1.6, 2.8)
        o = prim('ico_sphere', 'sk%d_%d' % (fi, j), off, (.01,) * 3, SMK, anchor, smooth=True, subdivisions=2); o.visible_shadow = False
        d0 = f0 + 6 + rnd.randint(0, 6)
        for f, k in ((d0 - 1, .01), (d0 + 6, r), (d0 + 40, r * 1.3), (d0 + 90, r * .4), (d0 + 110, .01)):
            o.scale = (k,) * 3; o.keyframe_insert('scale', frame=f)
    ld = bpy.data.lights.new('exl%d' % fi, 'POINT'); ld.color = (1, .55, .2); ld.shadow_soft_size = 3
    lo = bpy.data.objects.new('exl%d' % fi, ld); sc.collection.objects.link(lo); lo.parent = anchor
    for f, v in ((f0 - 1, 0), (f0, 90000), (f0 + 6, 40000), (f0 + 20, 5000), (f0 + 30, 0)): ld.energy = v; ld.keyframe_insert('energy', frame=f)
    F['vel'] = [Vector((random.uniform(-.25, .1), random.uniform(-.35, .35), random.uniform(-.1, .35))) for _ in F['parts']]
    F['spin'] = [Vector((random.uniform(-.3, .3), random.uniform(-.3, .3), random.uniform(-.3, .3))) for _ in F['parts']]
    F['rest'] = [(p.location.copy(), p.rotation_euler.copy()) for p in F['parts']]

# --- reparto por toma
if SHOT == 'hook':
    for loc in ((19, 1.5, .9), (25, -5, 3.2), (31, 6, 4.5), (36, -2, -2.5), (42, 8, 1.5), (47, -9, 6), (53, 12, -1), (60, 0, 7), (66, -14, 3)):
        fighter(loc)
    for i in range(16): fighter((random.uniform(75, 150), random.uniform(-35, 35), random.uniform(-8, 16)))
    BURSTS += [(8, 26, 0), (68, 92, 1)]; explode(0, 25); explode(1, 91)
else:
    for loc in ((44, 14, -9), (30, -6, -11), (52, -2, -12), (64, 10, -14), (76, -8, -15), (84, 18, -12), (60, 30, -10), (90, 0, -17)):
        fighter(loc)
    for i in range(10): fighter((random.uniform(100, 170), random.uniform(-40, 40), random.uniform(-25, 0)))
    BURSTS += [(70, 100, 0), (128, 150, 2)]; explode(0, 99); explode(2, 149)

cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = 'HORIZONTAL'; cd.clip_end = 3000
tgt = empty('target'); tr = cam.constraints.new('TRACK_TO'); tr.target = tgt; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def vlerp(a, b, k): return Vector(a).lerp(Vector(b), k)
SPEED = 2.2   # m por cuadro de las nubes hacia atrás

def fpos(F, f):
    t = f / 30; p = F['base'] + Vector((1.2 * math.sin(t * .9 + F['ph']), 1.5 * math.sin(t * .6 + F['ph']), .8 * math.sin(t * 1.3 + F['ph'])))
    return p
def on_frame(s, *a):
    f = s.frame_current; t = f / 30; q = (f - 1) / max(1, NF - 1)
    for o, base in CLOUDS: o.location = (base.x - SPEED * f, base.y, base.z)
    DECK.location = (-SPEED * f * .6, 0, -60)
    if SHOT == 'hook':
        P51.location = (0, .6 * math.sin(t * .8), .4 * math.sin(t * 1.1)); P51.rotation_euler = (.12 * math.sin(t * .7), -.03, 0)
        k = smooth((f - 30) / 140)
        cd.lens = lerp(32, 26, k)
        cam.location = vlerp((-10, -3.2, -4.5), (2, -16, -5.5), k) + Vector((0, 0, .08 * math.sin(f * .37)))
        tgt.location = vlerp((9, 0, 4.5), (5, 0, 4.0), k)
    else:
        k = smooth(q * 1.05)
        P51.location = vlerp((-20, 0, 18), (34, 2, -7), smooth(q)); P51.rotation_euler = (.45 * math.sin(t * 1.3), lerp(.42, .15, k), .05)
        cd.lens = 24
        cam.location = P51.location + vlerp((-6, -13, 6), (-10, -16, 2), k)
        tgt.location = P51.location + Vector((16, 4, -6 * (1 - k)))
        for B in BOMBERS:
            B['R'].location = B['base'] + Vector((0, .6 * math.sin(t + B['ph']), .4 * math.sin(t * 1.3 + B['ph'])))
            for h in B['props']: h.rotation_euler = (f * 1.1, 0, 0)
    for h in P51P: h.rotation_euler = (f * 1.3, 0, 0)
    for i, F in enumerate(FIGHTERS):
        F['R'].location = fpos(F, f); F['R'].rotation_euler = (.25 * math.sin(t * 1.1 + F['ph']), 0, .08 * math.sin(t * .7 + F['ph']))
        for h in F['props']: h.rotation_euler = (f * 1.2, 0, 0)
        if F['dead'] and f >= F['dead']:
            if 'frozen' not in F: F['frozen'] = fpos(F, F['dead'])
            F['R'].location = F['frozen'] + Vector((-.15 * (f - F['dead']), 0, -.05 * (f - F['dead']) ** 1.3))
            for p, v, w_, (l0, r0) in zip(F['parts'], F['vel'], F['spin'], F['rest']):
                n = f - F['dead']; p.location = l0 + v * n * 1.6; p.rotation_euler = Euler((r0.x + w_.x * n, r0.y + w_.y * n, r0.z + w_.z * n))
    for anchor, fi, f0 in EXPL:
        F = FIGHTERS[fi]; base = F.get('frozen') or fpos(F, f0)
        anchor.location = base + Vector((-.12 * max(0, f - f0), 0, .015 * max(0, f - f0)))
    bpy.context.view_layer.update()
    # disparos: ráfagas de las 4 ametralladoras hacia el caza objetivo
    firing = [(b0, b1, fi) for b0, b1, fi in BURSTS if b0 <= f <= b1 + 10]
    for o in FL: o.hide_render = True
    for o in POOL: o.location = (0, 0, -999)
    slot = 0
    for b0, b1, fi in firing:
        if f <= b1:
            for o in FL:
                o.hide_render = random.random() < .35; sz = random.uniform(.5, 1.1); o.scale = (.6 * sz, .3 * sz, .3 * sz)
        for fb in range(max(b0, f - 9), min(f, b1) + 1, 2):
            for gi, g in enumerate(GUNS):
                if slot >= len(POOL): break
                o = POOL[slot]; slot += 1
                gw = P51.matrix_world @ g; aim = fpos(FIGHTERS[fi], fb) if fb < (FIGHTERS[fi]['dead'] or 1e9) else FIGHTERS[fi].get('frozen', fpos(FIGHTERS[fi], fb))
                rnd = random.Random(fb * 7 + gi); d = (aim - gw).normalized() + Vector((0, rnd.uniform(-.02, .02), rnd.uniform(-.02, .02)))
                p = gw + d * 7.5 * (f - fb + .5)
                if (p - gw).length > (aim - gw).length + 3: continue
                o.location = p; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
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

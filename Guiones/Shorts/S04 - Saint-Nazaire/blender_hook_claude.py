"""Saint-Nazaire animated reconstruction. Adapted from Video 6 Eevee FX.
1 unit = 10 metres. +X is bow/dock direction. Legacy particles step sequentially.
blender -b -P blender_nazaire.py -- --shot hook|ram|blast|night --still 1,25,32,65
"""
import bpy, math, os, sys, random
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def arg(k,d=None): return argv[argv.index(k)+1] if k in argv else d
SHOT=arg('--shot','hook'); NF=int(arg('--frames',{'hook':113,'ram':115,'blast':64,'night':1}[SHOT]))
FALL=int(arg('--fall',{'hook':26,'ram':82,'blast':34,'night':999}[SHOT]))
OUT=arg('--out',os.path.join(HERE,'render3d',SHOT)); os.makedirs(OUT,exist_ok=True)
RES=float(arg('--res',1)); EXK=(0.3 if SHOT in ('hook','blast') else 1.0); random.seed(24)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=int(1080*RES); sc.render.resolution_y=int(1920*RES); sc.render.resolution_percentage=100
sc.render.fps=30; sc.frame_start=1; sc.frame_end=NF
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'; sc.render.image_settings.compression=15
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
ee=sc.eevee; ee.taa_render_samples=int(arg('--samples',32)); ee.use_raytracing=False
ee.volumetric_tile_size='8'; ee.volumetric_samples=40; ee.volumetric_end=120
sc.render.use_motion_blur=True; sc.render.motion_blur_shutter=0.4
def mat(name,rgb,rough=.6,metal=0,emit=0,ecol=None):
 m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
 b.inputs['Base Color'].default_value=(*rgb,1); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
 if emit: b.inputs['Emission Color'].default_value=(*(ecol or rgb),1); b.inputs['Emission Strength'].default_value=emit
 return m
def box(name,loc,size,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=tuple(x/2 for x in size); o.data.materials.append(m)
 if parent: o.parent=parent
 return o
def cyl(name,p0,p1,r,m,parent=None,verts=12):
 p0,p1=Vector(p0),Vector(p1); d=p1-p0
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d.length,location=(p0+p1)/2)
 o=bpy.context.object; o.name=name; o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized()); o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def empty(name,loc=(0,0,0)):
 o=bpy.data.objects.new(name,None); sc.collection.objects.link(o); o.location=loc; return o
STEEL=mat('naval grey',(.31,.36,.39),.46,.6); DARK=mat('deck charcoal',(.12,.15,.16)); EDGE=mat('weathered lighter steel',(.48,.51,.51),.55,.5)
STONE=mat('dock granite',(.30,.32,.31),.9); LAND=mat('quays',(.22,.24,.23),.9); BRICK=mat('dock warehouses',(.33,.29,.25),.9)
BLACK=mat('funnel interiors',(.025,.03,.035)); GLASS=mat('bridge windows',(.06,.13,.16),.25,.4); ROOF=mat('slate roofs',(.14,.17,.18))
water=mat('harbour water',(.045,.12,.15),.19,.48); nt=water.node_tree; b=nt.nodes['Principled BSDF']
tc=nt.nodes.new('ShaderNodeTexCoord'); mp=nt.nodes.new('ShaderNodeMapping'); nz=nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=5; nz.inputs['Detail'].default_value=4
bu=nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=.4; bu.inputs['Distance'].default_value=.055
nt.links.new(tc.outputs['Object'],mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'],nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'],bu.inputs['Height']); nt.links.new(bu.outputs['Normal'],b.inputs['Normal'])
for f,v in ((1,(0,0,0)),(NF,(1.4,.4,.2))):mp.inputs['Location'].default_value=v; mp.inputs['Location'].keyframe_insert('default_value',frame=f)
bpy.ops.mesh.primitive_plane_add(size=250); bpy.context.object.data.materials.append(water)
# Normandie dock: box caisson across the entrance, continuous masonry walls.
for y in (-8,8):
 box('quayside',(19,y,-.05),(29,9,1.4),LAND)
 box('granite dock wall',(19,3.2*(1 if y>0 else -1),.6),(29,.65,2.4),STONE)
 for x in (8,12,16,20,24,28,32):
  box('wall coping',(x,3.2*(1 if y>0 else -1),1.84),(3.9,.85,.15),EDGE)
  cyl('bollard',(x,4*(1 if y>0 else -1),1.3),(x,4*(1 if y>0 else -1),1.7),.1,BLACK)
 for x in (12,20,28):
  box('warehouse',(x,y,2.4),(5,3.8,3.5),BRICK); box('roof',(x,y,4.2),(5.3,4.1,.3),ROOF)
  for dx in (-1.5,0,1.5):box('warehouse window',(x+dx,y-1.93*(1 if y>0 else -1),2.7),(.6,.035,.75),GLASS)
 for x in (8,25):
  yy=5.3*(1 if y>0 else -1)
  cyl('crane mast',(x,yy,1.3),(x,yy,8),.10,EDGE)
  cyl('crane boom',(x,yy,7.6),(x-2,yy-2*(1 if y>0 else -1),8.4),.09,STEEL)
  cyl('crane stay',(x,yy,8),(x-2,yy-2*(1 if y>0 else -1),8.4),.035,BLACK)
  cyl('crane cable',(x-2,yy-2*(1 if y>0 else -1),8.4),(x-2,yy-2*(1 if y>0 else -1),3.5),.018,BLACK)
GATES=[]
for j in range(8):
 y=-2.8+(j+.5)*.7; root=empty('caisson panel',(5.25,y,.0)); GATES.append(root)
 box('steel caisson box',(0,0,1.25),(.65,.68,3.6),STEEL,root)
 for z in (.2,.9,1.6,2.3,2.95):box('horizontal caisson rib',(-.37,0,z),(.16,.66,.10),EDGE,root)
 for yy in (-.27,.27):box('vertical caisson rib',(-.38,yy,1.5),(.13,.085,3.3),EDGE,root)
# Campbeltown: long ex-US flush-deck destroyer, two removed funnels, two raked/cut funnels retained.
SHIP=empty('HMS Campbeltown')
stations=[(-5,.13),(-4.7,.40),(-3.5,.53),(-1,.55),(1.8,.54),(3.5,.47),(4.4,.29),(5,0.025)]
vs=[]
for x,w in stations:vs.extend([(x,-w,.52),(x,w,.52),(x,w*.75,-.32),(x,-w*.75,-.32)])
fs=[]
for j in range(len(stations)-1):
 for k in range(4):fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
fs.extend([(0,3,2,1),(28,29,30,31)])
mesh=bpy.data.meshes.new('destroyer shaped hull'); mesh.from_pydata(vs,[],fs); mesh.update()
hull=bpy.data.objects.new('narrow grey hull',mesh); sc.collection.objects.link(hull); hull.parent=SHIP; hull.data.materials.append(STEEL)
hull.shape_key_add(name='Basis'); crush=hull.shape_key_add(name='crushed bow')
for i,v in enumerate(vs):
 if v[0]>3:
  k=(v[0]-3)/2; crush.data[i].co.x-=.9*k; crush.data[i].co.y+=(-1 if v[1]<0 else 1)*.36*k; crush.data[i].co.z+=.25*k*(1 if i%2 else -1)
box('flush deck',(-.1,0,.53),(8.1,1,.12),DARK,SHIP)
box('bridge lower',(.65,0,.89),(1.45,.95,.62),STEEL,SHIP); box('bridge upper',(.95,0,1.3),(1,.83,.45),EDGE,SHIP)
for yy in (-.43,.43):
 for x in (.63,.95,1.27):box('bridge glazing',(x,yy,1.36),(.22,.025,.18),GLASS,SHIP)
box('bridge roof',(.95,0,1.57),(1.15,.98,.09),DARK,SHIP)
for x in (-.5,-1.85):
 cyl('two raked funnels',(x,0,.65),(x-.18,0,1.85),.19,STEEL,SHIP,20)
 cyl('angled black funnel mouth',(x-.18,0,1.80),(x-.23,0,1.93),.20,BLACK,SHIP,20)
cyl('mainmast',(.05,0,.65),(-.05,0,2.9),.034,EDGE,SHIP)
cyl('mast yard',(-.05,-.65,2.35),(-.05,.65,2.35),.023,EDGE,SHIP)
for yy in (-.47,.47):
 for x in (-4,-3,-2,-1,0,1,2,3):cyl('rail post',(x,yy,.6),(x,yy,.82),.009,EDGE,SHIP,6)
 cyl('guard rail',(-4,yy,.8),(3.1,yy,.8),.009,EDGE,SHIP,6)
for x in (2.55,-3.8):
 cyl('gun pedestal',(x,0,.59),(x,0,.85),.18,STEEL,SHIP)
 box('gun shield',(x+.04,0,.98),(.3,.45,.4),EDGE,SHIP); cyl('gun barrel',(x,0,1.04),(x+.75,0,1.14),.045,BLACK,SHIP)
for x in (-2.9,-3.4):box('deck fittings',(x,0,.76),(.33,.52,.28),EDGE,SHIP)
CRACK=[]
for yy in (-.45,.45):
 for j in range(4):
  o=box('opening tear in bow plating',(3.5+j*.14,yy,.27+j*.055),(.10,.035,.20),BLACK,SHIP); o.rotation_euler.y=(-.4 if j%2 else .4); CRACK.append(o)
# Overcast day / moonlit raid, intentionally readable night exposure.
NIGHT=SHOT in ('ram','night')
world=bpy.data.worlds.new('overcast sky'); sc.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.38,.48,.60,1) if NIGHT else (.65,.71,.76,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18 if NIGHT else .65
bpy.ops.object.light_add(type='SUN',rotation=(.45,-.5,-.5)); sun=bpy.context.object; sun.data.energy=.65 if NIGHT else 2; sun.data.angle=.4
sun.data.color=(.45,.65,1) if NIGHT else (.86,.93,1)
bpy.ops.object.light_add(type='AREA',location=(-4,-5,12)); bpy.context.object.data.energy=2000 if NIGHT else 1800; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=15
bpy.context.object.data.color=(.4,.6,1) if NIGHT else (.78,.87,1)
SEARCH=[]; BEAMS=[]
if NIGHT:
 for x,y in ((7,-4),(12,4)):
  bpy.ops.object.light_add(type='SPOT',location=(x,y,5)); o=bpy.context.object; o.data.energy=2600; o.data.color=(.75,.85,1); o.data.spot_size=.28; o.data.spot_blend=.5; SEARCH.append(o)
  cyl('searchlight pedestal',(x,y,1.5),(x,y,5),.08,STEEL)
  beamMat=bpy.data.materials.new('visible searchlight beam'); beamMat.use_nodes=True; bn=beamMat.node_tree; bn.nodes.remove(bn.nodes['Principled BSDF']); pv=bn.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value=.012; pv.inputs['Color'].default_value=(.6,.75,1,1); pv.inputs['Emission Color'].default_value=(.4,.6,1,1); pv.inputs['Emission Strength'].default_value=.12; bn.links.new(pv.outputs['Volume'],bn.nodes['Material Output'].inputs['Volume'])
  bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.03,radius2=.7,depth=1); beam=bpy.context.object; beam.data.materials.append(beamMat); BEAMS.append(beam)

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
    vol_shape("BolaFuego", loc, 4.0, (0.06, 0.05, 0.045), "ball", emit=14.0, ecol=((1.0,0.38,0.04) if SHOT in ("hook","blast") else (1.0, 0.16, 0.0)), nscale=1.9, speed=2.0,
              emit_keys=[(f0 - 1, 0), (f0, 220*EXK), (f0 + 4, 180*EXK), (f0 + 10, 95*EXK), (f0 + 18, 20), (f0 + 28, 0)],
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



# Water spray, sparks and fire are entirely in 3D. No screen-space effects.
if SHOT in ('hook','blast'):
 explosion((4.4,0,.8),FALL)
 for j,(x,y,z) in enumerate(((3.9,-.6,1.4),(4.8,.4,1.9),(4.2,-.2,2.8))):
  vol_shape('fireball lobe'+str(j),(x,y,z),1.6,(.15,.035,.01),'ball',emit=150,ecol=((1,.33,.02) if SHOT in ('hook','blast') else (1,.08,.001)),nscale=3.4,speed=2,
    emit_keys=[(FALL-1,0),(FALL+2,180*EXK),(FALL+9,110*EXK),(FALL+19,5),(FALL+30,0)],
    dens_keys=[(FALL-1,0),(FALL+2,1),(FALL+18,.8),(FALL+35,0)],
    scale_keys=[(FALL-1,(.01,.01,.01)),(FALL+4,(1.6,1.5,1.6)),(FALL+12,(2.4,2.1,2.4)),(FALL+30,(3,2.5,3))],gate=(.32,3.8))
 if SHOT in ('hook','blast'):
  for j,(x,y,z) in enumerate(((4.6,-.3,3.6),(4.0,.3,4.6),(4.9,0,5.6),(4.4,-.6,2.2))):
   vol_shape('big lobe'+str(j),(x,y,z),1.6,(.15,.035,.01),'ball',emit=150,ecol=(1,.33,.02),nscale=3.0,speed=2.2,
    emit_keys=[(FALL-1,0),(FALL+1+j,45),(FALL+10+j,28),(FALL+22,4),(FALL+34,0)],
    dens_keys=[(FALL-1,0),(FALL+1+j,1),(FALL+20,.8),(FALL+40,.3)],
    scale_keys=[(FALL-1,(.01,.01,.01)),(FALL+3+j,(1.8,1.7,1.8)),(FALL+12,(2.6,2.3,2.6)),(FALL+34,(3.2,2.8,3.2))],gate=(.32,3.8))
 fire_column('bow fire',(4.4,0,.4),2.2,2.1,FALL+8,NF+10,smoke=False)
 mist_domain((4.1,0,.1),2.7,FALL,0.38)
 e=emitter('explosion water surge',(4.4,0,.03),1.8,1.8)
 psys(e,I_DROP,2600,FALL,FALL+7,55,5.5,3.5,.025,.8,1,.3)
 psys(e,I_FOAM,600,FALL,FALL+14,160,.05,1.6,.055,.6,0,1.5,spin=False)
 # Large steel fragments have legible silhouette and deterministic ballistic motion.
 DEB=[]
 rr=random.Random(5)
 for j in range(15):
  o=box('large torn bow plate',(4.3,0,.8),(rr.uniform(.15,.55),rr.uniform(.12,.4),.055),STEEL)
  DEB.append((o,Vector((rr.uniform(-4,4),rr.uniform(-5,5),rr.uniform(4,8)))))
else:DEB=[]
if SHOT=='ram':
 e=emitter('impact sparks',(4.85,0,1.0),.8,.6,rot=(0,-1.0,0)); psys(e,I_EMBER,320,FALL,FALL+8,18,5,4,.018,.6,.4,.2)
 mist_domain((4.5,0,.0),1.5,FALL,.13)
# Continuous moving wake exists on the very first hook frame.
e=emitter('wake emitter',(0,0,-.015),7.5,.9,parent=SHIP)
psys(e,I_FOAM,850,-25,NF,28,.1,.45,.05,.65,0,.5,spin=False,lrand=.1)
e=emitter('bow wave',(4.2,0,.015),.65,1.1,parent=SHIP)
psys(e,I_DROP,850,-18,NF,20,.75,.85,.018,.65,.3,.4,spin=False)
tgt=empty('camera target'); bpy.ops.object.camera_add(); cam=bpy.context.object; sc.camera=cam; cam.data.lens=(22 if SHOT in ('hook','blast') else 36); cam.data.clip_end=500
cam.data.sensor_fit='HORIZONTAL'
tr=cam.constraints.new('TRACK_TO'); tr.target=tgt; tr.track_axis='TRACK_NEGATIVE_Z'; tr.up_axis='UP_Y'
def smooth(x):x=min(1,max(0,x)); return x*x*(3-2*x)
def on_frame(s,*a):
 f=s.frame_current; k=smooth((f-FALL)/12); q=(f-1)/max(1,NF-1)
 if SHOT=='ram':
  move=min(1,(f-1)/max(1,FALL-1)); SHIP.location.x=-7.0*(1-move)+.2*k
  crush.value=.95*k
  cam.location=(-6+2*q,-9+1*q,1.65+.7*q); tgt.location=(SHIP.location.x+1.9,0,1.0)
 elif SHOT=='night':
  SHIP.location.x=-.2; crush.value=.05; cam.location=(-10,-13,10); tgt.location=(1.7,0,1.1)
 else:
  pre=.08+.2*min(1,f/FALL); crush.value=min(1,pre+.7*k); SHIP.location.x=.12
  if f<FALL:SHIP.location.x+=.025*math.sin(f*.9); SHIP.rotation_euler.z=.003*math.sin(f*.7)
  for j,o in enumerate(CRACK):o.scale.x=.05+.015*math.sin(f*.45+j)+.06*min(1,f/FALL)
  if SHOT=='hook':
   # Claude: close low 3/4 camera on the bow; slow push before the blast, pull-up after
   kk=smooth((f-FALL)/40)
   sh=(.06*math.exp(-max(0,f-FALL)/5) if f>=FALL else 0)
   cam.location=(-0.8-0.5*min(1,f/FALL)-2.0*kk+sh*math.sin(f*7),-5.4+0.3*min(1,f/FALL)-2.4*kk,2.6+1.6*kk+sh*math.cos(f*9)); tgt.location=(3.4,0,0.9+2.0*kk)
  else:
   kk=smooth((f-FALL)/30); sh=(.07*math.exp(-max(0,f-FALL)/5) if f>=FALL else 0)
   cam.location=(0.4-1.8*kk+sh*math.sin(f*7),6.2+2.2*kk,2.3+2.0*kk+sh*math.cos(f*9)); tgt.location=(3.8,0,1.1+2.0*kk)
  for o,v in DEB:
   dt=max(0,(f-FALL)/30); o.hide_render=f<FALL; o.location=Vector((4.3,0,.8))+v*dt+Vector((0,0,-4.9*dt*dt)); o.rotation_euler=(dt*3,dt*2,dt*4)
 for j,o in enumerate(GATES):
  centre=max(0,1-abs(j-3.5)/4); push=k*(1.25 if SHOT in ('hook','blast') else .25)*centre
  o.location.x=5.25+push; o.rotation_euler.y=.30*push; o.rotation_euler.z=.14*push*(1 if j>3 else -1)
 for j,o in enumerate(SEARCH):
  dest=Vector((SHIP.location.x+1+math.sin(f*.035+j),0,.5)); delta=dest-o.location; o.rotation_euler=delta.to_track_quat('-Z','Y').to_euler()
  beam=BEAMS[j]; beam.location=(dest+o.location)/2; beam.rotation_euler=delta.to_track_quat('Z','Y').to_euler(); beam.scale=(1,1,delta.length)
bpy.app.handlers.frame_change_pre.append(on_frame)
# Eevee compositor glow comes only from rendered 3D emission.
# Blender 5.3 renders the volume emission directly; no 2D compositor FX.
still=arg('--still'); want=sorted(int(x) for x in still.split(',')) if still else None
# Pre-roll ensures legacy water particles are already alive at frame 1.
for f in range(-30,1):sc.frame_set(f)
for f in range(1,(want[-1] if want else NF)+1):
 sc.frame_set(f); on_frame(sc)
 if (want and f in want) or (not want):
  sc.render.filepath=os.path.join(OUT,('still_' if want else 'f_')+f'{f:04d}.png')
  bpy.ops.render.render(write_still=True)
print('COMPLETE',SHOT,flush=True)

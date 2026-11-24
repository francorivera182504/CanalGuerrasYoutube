"""S05 Mark I male reconstruction. Metres; +X forward. Blender 5.3 Eevee.
All dirt, exhaust and wire are actual 3D objects, particles or volumes.
Use an ABSOLUTE --out path. --still 1,36,91 checks framing before sequences.
"""
import bpy, math, os, sys, random, json
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def arg(k,d=None):return argv[argv.index(k)+1] if k in argv else d
SHOT=arg('--shot','hook'); COUNTS={'hook':165,'cross':122,'stall':71,'crew':103,'loop':180}
NF=int(arg('--frames',COUNTS[SHOT])); OUT=arg('--out')
TL=json.load(open(os.path.join(HERE,'timeline.json'),encoding='utf8'))
CROSS_HIT=next(w['s'] for w in TL['words'] if w['scene']=='04' and w['w']=='smash')-next(s['start'] for s in TL['timeline'] if s['id']=='04')
if not OUT or not os.path.isabs(OUT):raise ValueError('--out must be ABSOLUTE')
os.makedirs(OUT,exist_ok=True); RES=float(arg('--res','1'));random.seed(505)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=int(1080*RES);sc.render.resolution_y=int(1920*RES);sc.render.resolution_percentage=100
sc.render.fps=30;sc.frame_start=1;sc.frame_end=NF
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=15
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.eevee.taa_render_samples=int(arg('--samples','32'));sc.eevee.use_raytracing=False
sc.eevee.volumetric_tile_size='8';sc.eevee.volumetric_samples=32;sc.eevee.volumetric_end=65
sc.render.use_motion_blur=True;sc.render.motion_blur_shutter=.32
def mat(name,rgb,rough=.7,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
 b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
def empty(name,loc=(0,0,0)):
 o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.location=loc;return o
def box(name,loc,size,m,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def cyl(name,p0,p1,r,m,parent=None,verts=12):
 p0,p1=Vector(p0),Vector(p1);d=p1-p0;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d.length,location=(p0+p1)/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized());o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def ball(name,loc,r,m,parent=None,sub=2):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def prism(name,poly,y0,y1,m,parent=None):
 vs=[(x,y,z) for y in (y0,y1) for x,z in poly];n=len(poly)
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def curve(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,cu);sc.collection.objects.link(o);o.data.materials.append(m);return o
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
def mix(a,b,k):return Vector(a).lerp(Vector(b),k)
KHAKI=mat('dark British khaki brown',(.15,.124,.060),.87,.32);PLATE=mat('worn khaki panels',(.20,.165,.080),.84,.32)
TRACK=mat('blackened steel track',(.060,.065,.049),.76,.62);EDGE=mat('worn raised steel grousers',(.25,.24,.17),.6,.65)
RIVET=mat('rivets',(.29,.25,.13),.72,.55);BLACK=mat('recess charcoal',(.016,.020,.014));WOOD=mat('broken rough wood',(.19,.105,.044),.95)
WIRE=mat('steel barbed wire',(.46,.43,.34),.47,.75);MUD=mat('wet mud',(.075,.049,.025),.56,.05);DIRT=mat('flying wet earth',(.17,.095,.038),.9)
INNER=mat('sooted olive brown interior',(.052,.044,.024),.96,.12)
WHITE=mat('Stick round white heads',(.92,.92,.83),.8);CLOTH=mat('crew khaki',(.32,.28,.14),.9)
# Procedural mud normal and subtle mottled armour. No photographic plates.
for m,scale,strength,dist in ((MUD,4,.65,.14),(KHAKI,9,.38,.032),(PLATE,11,.34,.028),(TRACK,16,.3,.025)):
 nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=4
 tc=nt.nodes.new('ShaderNodeTexCoord');b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=dist
 nt.links.new(tc.outputs['Object'],n.inputs['Vector']);nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])
 ramp=nt.nodes.new('ShaderNodeValToRGB');base=m.diffuse_color[:3]
 ramp.color_ramp.elements[0].position=.23;ramp.color_ramp.elements[0].color=(*(v*.55 for v in base),1)
 ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(*(v*1.3 for v in base),1)
 nt.links.new(n.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],nt.nodes['Principled BSDF'].inputs['Base Color'])
 rough=nt.nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.64;rough.inputs['To Max'].default_value=.96
 nt.links.new(n.outputs['Fac'],rough.inputs[0]);nt.links.new(rough.outputs[0],nt.nodes['Principled BSDF'].inputs['Roughness'])
TANK=empty('Mark I male - 8 m - no turret')
OUTLINE=[(-4.02,1.30),(-2.70,2.76),(2.55,2.76),(4.03,1.78),(2.72,.22),(-2.84,.22)]
HULL=prism('angular central armoured hull',[(-3.25,.55),(-3.2,2.23),(-2.2,2.5),(2.6,2.5),(3.40,1.78),(2.7,.55)],-1.14,1.14,KHAKI,TANK)
bevel=HULL.modifiers.new('slight worn plate edges','BEVEL');bevel.width=.025;bevel.segments=1
TRACKS=[];PERIM=[];length=0
for i,p in enumerate(OUTLINE):
 q=OUTLINE[(i+1)%len(OUTLINE)];d=math.dist(p,q);PERIM.append((length,d,p,q));length+=d
def path(s):
 s=s%length
 for off,d,p,q in PERIM:
  if s<=off+d:
   k=(s-off)/d;return p[0]+(q[0]-p[0])*k,p[1]+(q[1]-p[1])*k,math.atan2(q[1]-p[1],q[0]-p[0])
for side in (-1,1):
 # Continuous enclosing rhomboid plates and distinct moving full-perimeter shoes.
 prism('rhomboid side armour',[(x*.94,1.48+(z-1.48)*.85) for x,z in OUTLINE],side*1.13,side*1.40,PLATE,TANK)
 for j in range(90):
  o=box('moving track shoe',(0,0,0),(.185,.66,.13),TRACK,TANK)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  g=box('raised transverse grouser',(0,0,.07),(.055,.65,.055),EDGE,o)
  TRACKS.append((o,j*length/90,side))
  if j%4==0:
   clod=ball('mud packed into track shoe',(.035,random.uniform(-.22,.22),.09),random.uniform(.07,.13),MUD,o,1);clod.scale=(1.4,1,.55)
 for x in (-2.7,-1.8,-.9,0,.9,1.8,2.65):
  cyl('side plate seam',(x,side*1.415,.61),(x,side*1.415,2.36),.013,BLACK,TANK,6)
  for z in (.65,.93,1.21,1.49,1.77,2.05,2.3):ball('rivet',(x+.07,side*1.43,z),.042,RIVET,TANK,1)
 for j in range(66):
  x,z,ang=path(j*length/66);ball('perimeter rivet',(x*.91,side*1.45,1.48+(z-1.48)*.80),.042,RIVET,TANK,1)
 lip=curve('worn rhomboid rim',[(x*.96,side*1.44,1.48+(z-1.48)*.90) for x,z in OUTLINE+[OUTLINE[0]]],.025,EDGE);lip.parent=TANK
 for j in range(34):
  x=random.uniform(-2.8,2.8);z=random.uniform(.38,.72)
  clod=ball('lower hull mud crust',(x,side*1.46,z),random.uniform(.07,.16),MUD,TANK,1);clod.scale=(1.5,.33,.65)
 # Male side sponsons; two short 6-pounder barrels, no rotating turret.
 prism('projecting angular gun sponson',[(-.65,.77),(-.65,1.95),(.65,2.02),(1.25,1.55),(.95,.77)],side*1.35,side*2.05,KHAKI,TANK)
 cyl('side gun mounting',(.63,side*2.02,1.52),(.74,side*2.14,1.52),.22,PLATE,TANK,16)
 cyl('short male 6 pounder barrel',(.69,side*2.13,1.54),(1.40,side*2.55,1.54),.085,EDGE,TANK,16)
 cyl('dark gun muzzle',(1.40,side*2.55,1.54),(1.414,side*2.558,1.54),.063,BLACK,TANK,16)
 for x,z in ((-.45,.94),(-.45,1.75),(.5,1.85),(.84,.96)):ball('sponson rivet',(x,side*2.07,z),.034,RIVET,TANK,1)
 for x in (-.4,-.1,.2,.5):ball('gun shield rivet',(x,side*2.065,1.86),.04,RIVET,TANK,1)
# Small fixed forward driver's cabin; long hull remains turretless.
box('fixed driver vision cabin',(2.25,0,2.54),(.75,1.05,.32),KHAKI,TANK)
for y in (-.30,.30):box('driver vision slit',(2.636,y,2.57),(.016,.22,.047),BLACK,TANK)
for x in (-1.7,-1.35,-1.0,-.65,-.3):box('engine roof louvres',(x,0,2.515),(.18,1.02,.035),BLACK,TANK)
cyl('exhaust pipe',(-1.7,.7,2.45),(-1.7,.7,3.02),.075,TRACK,TANK)
cyl('exhaust rear outlet',(-1.7,.7,3),(-2.2,.7,3),.075,TRACK,TANK)
HATCH=empty('hinged crew hatch',(1.1,-.5,2.52));HATCH.parent=TANK
box('hatch lid',(0,.5,0),(1.12,1,.10),PLATE,HATCH)
cyl('hatch handle',(-.2,.45,.08),(.2,.45,.08),.045,TRACK,HATCH)
# Large terrain mesh with one genuine trench gap across the path.
rr=random.Random(51)
for xmin,xmax in ((-24,-.9),(.9,28)) if SHOT=='cross' else ((-24,28),):
 vs=[];fs=[];nx=65;ny=45
 for i in range(nx):
  x=xmin+(xmax-xmin)*i/(nx-1)
  for j in range(ny):
   y=-18+36*j/(ny-1);z=-.055+rr.uniform(-.055,.055)
   for cx,cy in ((-7,6),(7,6),(10,-6),(-9,-6)):z-=.6*math.exp(-((x-cx)**2+(y-cy)**2)/3)
   vs.append((x,y,z))
 for i in range(nx-1):
  for j in range(ny-1):a=i*ny+j;fs.append((a,a+1,a+ny+1,a+ny))
 me=bpy.data.meshes.new('mud craters');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('muddy no mans land',me);sc.collection.objects.link(o);o.data.materials.append(MUD)
if SHOT=='cross':
 box('trench dark floor',(0,0,-1.2),(1.8,35,.3),BLACK)
 for x in (-.94,.94):
  box('trench earth face',(x,0,-.64),(.12,35,1.35),DIRT)
  for y in range(-12,13):box('trench timber revetment',(x*.96,y,-.6),(.08,.13,1.1),WOOD)
# Uneven timber stakes and two strands of actual 3D barbed-wire.
POSTS=[];WIRES=[];BARBS=[]
for x in (3.72,4.65,8.8):
 fore=x==4.65
 for y in ((-5.8,-3.8,-1.45,0,1.35,3.9) if fore else (-3.8,-1.45,0,1.35,3.9)):
  # A permanent stump and a separately hinged upper section make a real break.
  cyl('snapped stake stump',(x,y,.01),(x,y,.28),.087,WOOD,verts=8)
  e=empty('splintering stake',(x,y,.28));cyl('breaking upper stake',(0,0,0),(.08,.02,.45 if fore else 1.02),.078,WOOD,e,8);POSTS.append((e,x,y))
 for layer in range(4):
  z=(.37 if fore else .62) if layer<2 else (.26 if layer==2 else (.60 if fore else 1.04))
  if layer<2:
   radius=.31 if fore else .46
   pts=[(x+(layer-.5)*.30+radius*math.cos(j*math.tau*13/390),(-6.4 if fore else -4.4)+j*(10.8 if fore else 8.8)/390,z+radius*math.sin(j*math.tau*13/390)) for j in range(391)]
  else:pts=[(x+.05*math.sin(j*.6),(-6.4 if fore else -4.4)+j*(10.8 if fore else 8.8)/140,z-.12*abs(math.sin(j*.10))) for j in range(141)]
  o=curve('concertina coil' if layer<2 else 'tensioned wire strand',pts,.023 if layer<2 else .025,WIRE);WIRES.append((o,x,z,pts))
  for j in range(3,len(pts)-2,10 if layer<2 else 7):
   xx,yy,zz=pts[j]
   for v in (-1,1):
    barb=curve('sharp barb',[(xx-.11,yy-.07,zz-v*.14),(xx+.11,yy+.07,zz+v*.14)],.012,WIRE);BARBS.append((barb,x,yy,zz))
# A background wire line gives depth and cannot be mistaken for people.
for x in range(-15,20,3):cyl('distant fence post',(x,9,0),(x+.15,9,1),.05,WOOD)
curve('distant sagging wire',[(x/4,9,.7+.1*math.sin(x*.7)) for x in range(-60,81)],.011,WIRE)
world=bpy.data.worlds.new('overcast');sc.world=world;world.use_nodes=True
nt=world.node_tree;tc=nt.nodes.new('ShaderNodeTexCoord');cloud=nt.nodes.new('ShaderNodeTexNoise');cloud.inputs['Scale'].default_value=3.2;cloud.inputs['Detail'].default_value=3;cloud.inputs['Roughness'].default_value=.7
mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1.1,1.1,3.3)
nt.links.new(tc.outputs['Normal'],mapping.inputs[0]);nt.links.new(mapping.outputs[0],cloud.inputs['Vector'])
cr=nt.nodes.new('ShaderNodeValToRGB');cr.color_ramp.elements[0].position=.28;cr.color_ramp.elements[0].color=(.14,.17,.19,1);cr.color_ramp.elements[1].position=.72;cr.color_ramp.elements[1].color=(.52,.55,.56,1)
nt.links.new(cloud.outputs['Fac'],cr.inputs[0]);nt.links.new(cr.outputs[0],nt.nodes['Background'].inputs['Color']);nt.nodes['Background'].inputs['Strength'].default_value=.45 if SHOT!='crew' else .13
bpy.ops.object.light_add(type='SUN',rotation=(.35,-.45,-.6));bpy.context.object.data.energy=.9 if SHOT!='crew' else .17;bpy.context.object.data.angle=.8
bpy.ops.object.light_add(type='AREA',location=(3,-7,10));bpy.context.object.data.energy=1550 if SHOT!='crew' else 180;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=10
# FX helpers copied from S04: Object coordinates; density-masked volume emission.
import tank_fx
tank_fx.NF=NF
from tank_fx import emitter,psys,vol_shape
if SHOT!='crew':vol_shape('low battlefield haze',(0,15,1.6),.12,(.27,.30,.31),speed=.08,nscale=1.8,scale_keys=[(1,(35,8,2.4)),(NF,(35,8,2.4))])
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(0,0,-200));DROP=bpy.context.object;DROP.name='particle earth clod';DROP.scale=(1,.7,.65);DROP.data.materials.append(DIRT)
if SHOT in ('hook','loop','cross'):
 e=emitter('continuous track mud',(2.75,-1.25,.13),.5,2.8,parent=TANK);psys(e,DROP,180,-12,NF,19,.6,1.5,.045,.7,1,.15)
 if SHOT=='hook':
  e=emitter('crushes mud burst',(3.72,-1.35,.25),.65,2.2);psys(e,DROP,330,33.5,35.5,27,5.2,3.1,.12,.72,1,.2)
  e=emitter('far track earth fan',(3.72,1.3,.25),.55,1.1);psys(e,DROP,110,33.5,35.5,24,4.2,2.5,.10,.7,1,.2)
  splinter=box('flying snapped wood',(0,0,-200),(.07,.06,.28),WOOD)
  e=emitter('breaking stake splinters',(3.72,-1.45,.8),.3,.35);psys(e,splinter,26,34,35.5,25,2.8,2,.8,.7,1,.12)
 elif SHOT=='cross':
  e=emitter('trench climb mud spray',(.95,-1,.03),.5,2.3);psys(e,DROP,190,54,72,24,2.2,2,.055,.75,1,.2)
if SHOT!='crew':
 smoke=vol_shape('engine exhaust',(-2.35,.72,3.3),8,(.065,.06,.05),'ball',speed=.75,nscale=2.2,
  dens_keys=[(1,.45),(14,.5),(24,2.8),(38,2.3),(59,.5),(NF,.45)] if SHOT=='stall' else [(1,.38),(NF,.38)],
  scale_keys=[(1,(1.2,.8,1.6)),(NF,(.55,.42,.7))] if SHOT=='loop' else [(1,(.55,.42,.7)),(26,(1.2,.8,1.6)),(NF,(1.5,1,2))],parent=TANK)
CREW=[];CREW_ARMS=[];FLYWHEEL=None
if SHOT=='crew':
 # Remove only the near wall; retain BOTH complete enclosing rhomboid tracks.
 for o in list(TANK.children):
  if o.name.startswith(('angular central','engine roof')):o.hide_render=True
 for o in list(TANK.children):
  if o.name.startswith(('rhomboid side','side plate seam','rivet','sponson rivet','gun shield','projecting angular','side gun','short male','dark gun','lower hull','perimeter rivet')):
   if o.location.y<-.9 or (o.type=='MESH' and all(v.co.y<-.9 for v in o.data.vertices)):o.hide_render=True
 prism('rhomboid internal floor',[(-3.7,.65),(-2.8,.26),(2.72,.26),(3.47,1.14),(2.70,.57),(-2.8,.57)],-1.12,1.12,INNER,TANK)
 prism('dark far rhomboid inner wall',[(x*.92,1.48+(z-1.48)*.83) for x,z in OUTLINE],.99,1.13,INNER,TANK)
 prism('enclosing sloped stern',[(-3.78,1.30),(-2.7,2.62),(-2.52,2.62),(-3.56,1.30),(-2.7,.42),(-2.86,.30)],-1.1,1.1,KHAKI,TANK)
 prism('enclosing sloped nose',[(2.62,2.62),(3.87,1.78),(2.67,.30),(2.53,.44),(3.62,1.78),(2.50,2.46)],-1.1,1.1,KHAKI,TANK)
 box('near cutaway dark lower sill',(0,-1.10,.67),(5.7,.14,.32),INNER,TANK)
 box('roof over stern',(-2.5,0,2.48),(.73,2.2,.13),KHAKI,TANK)
 box('roof over driving position',(2.56,0,2.48),(.76,2.2,.13),KHAKI,TANK)
 # Retain the roof skin as well: the side wall is the only open hull surface.
 box('roof near longitudinal panel',(0,-.54,2.49),(5.5,1.12,.12),KHAKI,TANK)
 box('roof left of hatch',(-1.60,.54,2.49),(2.18,1.02,.12),KHAKI,TANK)
 box('roof right of hatch',(1.66,.54,2.49),(2.10,1.02,.12),KHAKI,TANK)
 box('roof far longitudinal lip',(0,1.075,2.49),(5.5,.11,.12),KHAKI,TANK)
 for x in (-1.9,1.15):box('roof crossbeam',(x,0,2.45),(.10,2.12,.12),INNER,TANK)
 for x in (-2.1,-.9,.3,1.5):box('inner far wall stiffener',(x,.97,1.5),(.07,.09,1.7),TRACK,TANK)
 box('large central exposed engine',(-.35,0,1.08),(2.45,.93,1.04),TRACK,TANK)
 for x in (-1.32,-.87,-.42,.03,.48):
  cyl('engine cylinder',(x,0,1.3),(x,0,1.90),.21,TRACK,TANK)
  for z in (1.48,1.63,1.78):cyl('cylinder cooling rib',(x,0,z),(x,0,z+.035),.229,EDGE,TANK)
 FLYWHEEL=empty('turning engine flywheel',(.55,-.55,1.12));FLYWHEEL.parent=TANK
 cyl('flywheel hub',(0,.02,0),(0,-.12,0),.27,TRACK,FLYWHEEL,24)
 for j in range(6):
  ang=j*math.pi/3;cyl('flywheel spoke',(0,-.13,0),(.24*math.cos(ang),-.13,.24*math.sin(ang)),.023,EDGE,FLYWHEEL,8)
 cyl('hot exhaust manifold',(-1.4,.55,1.5),(.7,.55,1.5),.09,WOOD,TANK)
 for i,(x,y) in enumerate([(-2.55,-.70),(-1.63,-.70),(1.13,-.70),(2.13,-.70),(-2.25,.68),(-1.20,.68),(1.35,.68),(2.35,.68)]):
  p=empty('Stick crew %d'%(i+1),(x,y,.55+(.14 if i>=4 else 0)));p.parent=TANK;CREW.append(p)
  box('cramped seat',(0,0,.32),(.43,.44,.13),WOOD,p)
  box('seat back',(0,.20,.61),(.43,.07,.57),WOOD,p)
  box('khaki torso',(0,0,.67),(.30,.24,.54),CLOTH,p)
  ball('round white head',(0,-.015,1.12),.205,WHITE,p,3)
  for dx in (-.065,.065):ball('dot eye',(dx,-.205,1.15),.026,BLACK,p,2)
  for side in (-1,1):
   cyl('seated Stick thigh',(side*.10,0,.42),(side*.14,-.27,.36),.045,BLACK,p)
   cyl('seated Stick shin',(side*.14,-.27,.36),(side*.14,-.31,.06),.045,BLACK,p)
   arm=cyl('gesturing Stick forearm',(side*.18,0,.84),(side*.23,-.27,.64),.04,BLACK,p)
   CREW_ARMS.append((arm,i,side,Vector((side*.18,0,.84))))
 # Hatch and cutaway upper edge remain readable without hiding the eight heads.
 box('upper hatch frame',(.05,.48,2.43),(1.25,1.05,.10),KHAKI,TANK)
 HATCH.location=(.05,.02,2.51)
 for x in (-1.9,1.6):
  bpy.ops.object.light_add(type='POINT',location=(x,.25,2.14));lamp=bpy.context.object;lamp.data.energy=52;lamp.data.shadow_soft_size=.65;lamp.data.color=(1,.59,.25)
  ball('warm cabin lamp',(x,.7,2.15),.065,RIVET,TANK,2)
 bpy.ops.object.light_add(type='AREA',location=(0,-2.5,3.3));bpy.context.object.data.energy=95;bpy.context.object.data.size=4;bpy.context.object.data.color=(1,.71,.4)
 vol_shape('engine fumes trapped in cabin',(-.4,.05,1.55),.7,(.20,.16,.10),speed=.12,nscale=2.3,scale_keys=[(1,(2.9,.9,1.0)),(NF,(2.9,.9,1.0))])
target=empty('camera target');bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.lens=26;cam.data.sensor_fit='HORIZONTAL';cam.data.clip_end=150
tr=cam.constraints.new('TRACK_TO');tr.target=target;tr.track_axis='TRACK_NEGATIVE_Z';tr.up_axis='UP_Y'
def on_frame(s,*args):
 f=s.frame_current;t=(f-1)/30;q=t/max(.01,(NF-1)/30)
 if SHOT=='hook':
  TANK.location.x=.85*t;TANK.rotation_euler.y=.009*math.sin(t*5)+.035*math.exp(-((t-1.20)/.12)**2)
  k=smooth((t-1.5)/3.9)
  follow=.25*min(t,1.5)+.85*max(0,t-1.5)
  cam.location=mix((6.2,-5.7,1.03),(5.7,-6.0,2.25),k)+Vector((follow,0,0))
  target.location=mix((.40,0,1.35),(.15,0,1.20),k)+Vector((TANK.location.x,0,0))
  cam.data.shift_x=.045;cam.data.shift_y=-.30;distance=.85*t
 elif SHOT=='loop':
  # Advance gently into the opening pose. Wire stays intact until the next play.
  TANK.location.x=-.70*(1-q);TANK.rotation_euler.y=.007*math.sin(t*3)*(1-q)
  k=smooth(q);cam.location=mix((5.0,-6.4,2.15),(6.2,-5.7,1.03),k)+TANK.location
  target.location=mix((.15,0,1.20),(.40,0,1.35),k)+TANK.location
  cam.data.shift_x=.045;cam.data.shift_y=-.30;distance=.7*(q-1)
 elif SHOT=='cross':
  TANK.location.x=-2.0+4.1*q;TANK.location.z=-.14*math.sin(math.pi*q)**2
  TANK.rotation_euler.y=.13*math.sin(2*math.pi*(q-.12))
  cam.location=(TANK.location.x+4.8,-5.7,1.7);target.location=(TANK.location.x,0,1.15);cam.data.shift_x=.07;cam.data.shift_y=-.24;distance=4.1*q
 elif SHOT=='stall':
  # Cough at local .55s; stop at .8-1.3s; restart at 1.35s.
  distance=.5*min(t,.72)+.5*max(0,t-1.36);TANK.location.x=distance
  TANK.rotation_euler.y=.014*math.sin(t*25)*(1-smooth((t-1.35)/.35))
  cam.location=(4.8+distance,-5.8,1.45);target.location=(distance,0,1.25);cam.data.shift_x=.07;cam.data.shift_y=-.25
 else:
  distance=0;TANK.location=(0,0,0);cam.location=(1.0+.11*math.sin(t*.6),-7.7+.13*q,3.2+.06*math.sin(t*.8));target.location=(0,0,1.28);cam.data.shift_x=.025;cam.data.shift_y=-.18
  HATCH.rotation_euler.x=1.3*(1-smooth((t-2.4)/.65))
  for i,p in enumerate(CREW):p.rotation_euler.z=.035*math.sin(t*3+i);p.rotation_euler.x=.02*math.sin(t*4+i)
  FLYWHEEL.rotation_euler.y=t*11
  for arm,i,side,p0 in CREW_ARMS:
   end=Vector((side*(.26+.055*math.sin(t*3+i)),-.28,.77+.18*math.sin(t*3.7+i+side)))
   delta=end-p0;arm.location=(p0+end)/2;arm.rotation_quaternion=Vector((0,0,1)).rotation_difference(delta.normalized());arm.scale.z=delta.length/.34
 for o,off,side in TRACKS:
  x,z,ang=path(off+distance);o.location=(x,side*1.3,z);o.rotation_euler.y=-ang
 # Crushing deforms the real wire curves; snapped posts and springing wire.
 hit=1.10 if SHOT in ('hook','loop') else CROSS_HIT
 k=smooth((t-hit)/(.10 if SHOT=='hook' else .23)) if SHOT in ('hook','cross') else 0
 for o,x,y in POSTS:
  if x<5 and -2<y<2.5:o.rotation_euler.y=1.45*k;o.rotation_euler.x=(.45 if y<0 else -.45)*k
 for o,x,z,pts in WIRES:
  if x>5:continue
  for j,p in enumerate(o.data.splines[0].points):
   xx,yy,zz=pts[j];contact=math.exp(-((yy+.1)/2.35)**6)
   spring=math.sin(max(0,t-hit)*13+j*.035)*math.exp(-max(0,t-hit)*2.8)*k
   wing=math.exp(-((abs(yy)-2.05)/.8)**2)
   p.co.z=max(.045,zz*(1-.91*k*contact)+1.45*abs(spring)*wing+.22*spring*contact)
   p.co.x=xx+.65*k*contact+.6*spring*wing
   p.co.y=yy+(.6 if yy>0 else -.6)*k*wing
 for o,x,y,z in BARBS:
  if x<5:
   c=math.exp(-((y+.1)/2.35)**6);spring=math.sin(max(0,t-hit)*13)*math.exp(-max(0,t-hit)*2.8)*k;wing=math.exp(-((abs(y)-2.05)/.8)**2)
   o.location=(.65*k*c+.6*spring*wing,(.6 if y>0 else -.6)*k*wing,-z*.91*k*c+1.45*abs(spring)*wing)
bpy.app.handlers.frame_change_pre.append(on_frame)
still=arg('--still');want=sorted(int(x) for x in still.split(',')) if still else None
FRAMING=[]
def record_framing(f):
 from bpy_extras.object_utils import world_to_camera_view
 bpy.context.view_layer.update()
 pts=[]
 for o in TANK.children_recursive:
  if o.type=='MESH' and not o.hide_render and not o.name.startswith(('engine exhaust','continuous track','crushes','particle')):
   pts.extend(world_to_camera_view(sc,cam,o.matrix_world@Vector(v)) for v in o.bound_box)
 xs=[v.x for v in pts];ys=[v.y for v in pts]
 FRAMING.append(dict(frame_zero=f-1,time_s=(f-1)/30,width_fraction=max(xs)-min(xs),left=min(xs),right=max(xs),bottom=min(ys),top=max(ys),crew=len(CREW)))
for f in range(-25,1):sc.frame_set(f)
for f in range(1,(max(want) if want else NF)+1):
 sc.frame_set(f);on_frame(sc)
 if (want and f in want) or not want:
  if want or f in (1,36,46,91,NF):record_framing(f)
  sc.render.filepath=os.path.join(OUT,('still_' if want else 'f_')+f'{f:04d}.png');bpy.ops.render.render(write_still=True)
json.dump(FRAMING,open(os.path.join(OUT,'framing.json'),'w'),indent=2)
print('COMPLETE',SHOT,flush=True)

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
KHAKI=mat('dark British khaki brown',(.23,.205,.105),.8,.25);PLATE=mat('worn khaki panels',(.31,.275,.15),.72,.3)
TRACK=mat('blackened steel track',(.105,.115,.10),.57,.65);EDGE=mat('worn raised steel grousers',(.28,.285,.23),.5,.7)
RIVET=mat('rivets',(.40,.36,.22),.6,.55);BLACK=mat('recess charcoal',(.025,.028,.023));WOOD=mat('broken rough wood',(.22,.13,.065),.95)
WIRE=mat('steel barbed wire',(.39,.38,.31),.4,.8);MUD=mat('wet mud',(.105,.075,.043),.36,.05);DIRT=mat('flying wet earth',(.17,.11,.055),.85)
WHITE=mat('Stick round white heads',(.92,.92,.83),.8);CLOTH=mat('crew khaki',(.32,.28,.14),.9)
# Procedural mud normal and subtle mottled armour. No photographic plates.
for m,scale,strength,dist in ((MUD,4,.65,.14),(KHAKI,12,.24,.022),(PLATE,14,.22,.02)):
 nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=4
 tc=nt.nodes.new('ShaderNodeTexCoord');b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=dist
 nt.links.new(tc.outputs['Object'],n.inputs['Vector']);nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])
TANK=empty('Mark I male - 8 m - no turret')
OUTLINE=[(-4.02,1.30),(-2.70,2.76),(2.55,2.76),(4.03,1.78),(2.72,.22),(-2.84,.22)]
prism('angular central armoured hull',[(-3.25,.55),(-3.2,2.23),(-2.2,2.5),(2.6,2.5),(3.40,1.78),(2.7,.55)],-1.14,1.14,KHAKI,TANK)
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
 for j in range(78):
  o=box('moving track shoe',(0,0,0),(.224,.64,.115),TRACK,TANK)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  g=box('raised transverse grouser',(0,0,.07),(.055,.65,.055),EDGE,o)
  TRACKS.append((o,j*length/78,side))
 for x in (-2.7,-1.8,-.9,0,.9,1.8,2.65):
  cyl('side plate seam',(x,side*1.415,.61),(x,side*1.415,2.36),.013,BLACK,TANK,6)
  for z in (.65,1,1.4,1.8,2.25):ball('rivet',(x+.07,side*1.43,z),.034,RIVET,TANK,1)
 # Male side sponsons; two short 6-pounder barrels, no rotating turret.
 prism('projecting angular gun sponson',[(-.65,.77),(-.65,1.95),(.65,2.02),(1.25,1.55),(.95,.77)],side*1.35,side*2.05,KHAKI,TANK)
 cyl('side gun mounting',(.63,side*2.02,1.52),(.74,side*2.14,1.52),.22,PLATE,TANK,16)
 cyl('short male 6 pounder barrel',(.69,side*2.13,1.54),(1.40,side*2.55,1.54),.085,EDGE,TANK,16)
 cyl('dark gun muzzle',(1.40,side*2.55,1.54),(1.414,side*2.558,1.54),.063,BLACK,TANK,16)
 for x,z in ((-.45,.94),(-.45,1.75),(.5,1.85),(.84,.96)):ball('sponson rivet',(x,side*2.07,z),.034,RIVET,TANK,1)
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
for x in (3.16,7.6):
 for y in (-4,-1.15,1.75,4.5):
  # A permanent stump and a separately hinged upper section make a real break.
  cyl('snapped stake stump',(x,y,.01),(x,y,.27),.058,WOOD,verts=8)
  e=empty('splintering stake',(x,y,.27));cyl('breaking upper stake',(0,0,0),(.04,.03,.85),.055,WOOD,e,8);POSTS.append((e,x,y))
 for z in (.48,.86):
  pts=[(x+.12*math.sin(j*.7),-4+j*8.5/100,z-.12*abs(math.sin(j*.12))) for j in range(101)]
  o=curve('barbed wire strand',pts,.012,WIRE);WIRES.append((o,x,z,pts))
  for j in range(2,100,4):
   xx,yy,zz=pts[j]
   for v in (-1,1):
    barb=curve('sharp barb',[(xx-.065,yy-.04,zz-v*.085),(xx+.065,yy+.04,zz+v*.085)],.008,WIRE);BARBS.append((barb,x,yy,zz))
# A background wire line gives depth and cannot be mistaken for people.
for x in range(-15,20,3):cyl('distant fence post',(x,9,0),(x+.15,9,1),.05,WOOD)
curve('distant sagging wire',[(x/4,9,.7+.1*math.sin(x*.7)) for x in range(-60,81)],.011,WIRE)
world=bpy.data.worlds.new('overcast');sc.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.56,.61,.64,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
bpy.ops.object.light_add(type='SUN',rotation=(.35,-.45,-.6));bpy.context.object.data.energy=1.6;bpy.context.object.data.angle=.65
bpy.ops.object.light_add(type='AREA',location=(3,-7,10));bpy.context.object.data.energy=1900;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=10
# FX helpers copied from S04: Object coordinates; density-masked volume emission.
from tank_fx import emitter,psys,vol_shape
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(0,0,-200));DROP=bpy.context.object;DROP.name='particle earth clod';DROP.scale=(1,.7,.65);DROP.data.materials.append(DIRT)
if SHOT in ('hook','loop','cross'):
 e=emitter('continuous track mud',(2.75,-1.25,.13),.5,2.8,parent=TANK);psys(e,DROP,180,-12,NF,19,.6,1.5,.045,.7,1,.15)
 if SHOT!='cross':
  e=emitter('crushes mud burst',(3.16,-1.1,.15),.55,1.5);psys(e,DROP,240,35.5,38,26,3.2,2.7,.07,.8,1,.2)
 else:
  e=emitter('trench climb mud spray',(.95,-1,.03),.5,2.3);psys(e,DROP,190,54,72,24,2.2,2,.055,.75,1,.2)
if SHOT!='crew':
 smoke=vol_shape('engine exhaust',(-2.35,.72,3.3),8,(.065,.06,.05),'ball',speed=.75,nscale=2.2,
  dens_keys=[(1,.45),(14,.5),(24,2.8),(38,2.3),(59,.5),(NF,.45)] if SHOT=='stall' else [(1,.38),(NF,.38)],
  scale_keys=[(1,(.55,.42,.7)),(26,(1.2,.8,1.6)),(NF,(1.5,1,2))],parent=TANK)
CREW=[];CREW_ARMS=[];FLYWHEEL=None
if SHOT=='crew':
 # Open camera-facing side and roof, retain far rhomboid track and real sponsons.
 for o in list(TANK.children):
  if o.name.startswith(('angular central','engine roof','rhomboid side','fixed driver','driver vision')) or (o.name.startswith('moving track') and o.location.y<0):o.hide_render=True
 # Hide near-side plating details and sponson, keep far side structural silhouette.
 for o in list(TANK.children):
  if o.location.y<-.9:o.hide_render=True
  if o.type=='MESH' and all(v.co.y<-.9 for v in o.data.vertices):o.hide_render=True
 for o,off,side in TRACKS:
  if side<0:
   o.hide_render=True
   for child in o.children:child.hide_render=True
 box('cutaway floor',(0,0,.52),(6.9,2.55,.18),PLATE,TANK)
 box('far interior wall',(0,1.10,1.45),(6.5,.12,1.9),KHAKI,TANK)
 box('large central exposed engine',(-.45,0,1.12),(2.35,.85,1.02),TRACK,TANK)
 for x in (-1.3,-.9,-.5,-.1,.3):
  cyl('engine cylinder',(x,0,1.3),(x,0,1.85),.20,EDGE,TANK)
 FLYWHEEL=empty('turning engine flywheel',(.55,-.55,1.12));FLYWHEEL.parent=TANK
 cyl('flywheel hub',(0,.02,0),(0,-.12,0),.27,TRACK,FLYWHEEL,24)
 for j in range(6):
  ang=j*math.pi/3;cyl('flywheel spoke',(0,-.13,0),(.24*math.cos(ang),-.13,.24*math.sin(ang)),.023,EDGE,FLYWHEEL,8)
 cyl('hot exhaust manifold',(-1.4,.55,1.5),(.7,.55,1.5),.09,WOOD,TANK)
 for i,(x,y) in enumerate([(-2.7,-.80),(-1.7,-.80),(.95,-.80),(1.95,-.80),(-2.15,.75),(-1.15,.75),(1.5,.75),(2.5,.75)]):
  p=empty('Stick crew %d'%(i+1),(x,y,.62+(.16 if i>=4 else 0)));p.parent=TANK;CREW.append(p)
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
 box('upper hatch frame',(0,.6,2.42),(1.25,1.05,.10),KHAKI,TANK)
 HATCH.location=(0,.08,2.51)
 bpy.ops.object.light_add(type='AREA',location=(0,-4,4));bpy.context.object.data.energy=430;bpy.context.object.data.size=5;bpy.context.object.data.color=(1,.77,.48)
target=empty('camera target');bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.lens=25;cam.data.sensor_fit='HORIZONTAL';cam.data.clip_end=100
tr=cam.constraints.new('TRACK_TO');tr.target=target;tr.track_axis='TRACK_NEGATIVE_Z';tr.up_axis='UP_Y'
def on_frame(s,*args):
 f=s.frame_current;t=(f-1)/30;q=t/max(.01,(NF-1)/30)
 if SHOT in ('hook','loop'):
  TANK.location.x=.38*t;TANK.rotation_euler.y=.009*math.sin(t*5)
  k=smooth((t-1.42)/1.55)
  cam.location=mix((4.7,-3.1,.52),(4.4,-5.5,3.4),k)+Vector((TANK.location.x,0,0))
  target.location=mix((2.9,-1.1,.63),(.35,0,1.15),k)+Vector((TANK.location.x,0,0))
  distance=.8*t
 elif SHOT=='cross':
  TANK.location.x=-2.0+4.1*q;TANK.location.z=-.14*math.sin(math.pi*q)**2
  TANK.rotation_euler.y=.13*math.sin(2*math.pi*(q-.12))
  cam.location=(TANK.location.x+4.4,-5.7,2.1);target.location=(TANK.location.x,0,1.2);distance=4.1*q
 elif SHOT=='stall':
  # Cough at local .55s; stop at .8-1.3s; restart at 1.35s.
  distance=.5*min(t,.72)+.5*max(0,t-1.36);TANK.location.x=distance
  TANK.rotation_euler.y=.014*math.sin(t*25)*(1-smooth((t-1.35)/.35))
  cam.location=(4.6+distance,-5.6,2.6);target.location=(distance-.15,0,1.4)
 else:
  distance=0;TANK.location=(0,0,0);cam.location=(.45,-5.6,5.1);target.location=(0,0,1.1)
  HATCH.rotation_euler.x=-1.3*(1-smooth((t-2.4)/.65))
  for i,p in enumerate(CREW):p.rotation_euler.z=.035*math.sin(t*3+i);p.rotation_euler.x=.02*math.sin(t*4+i)
  FLYWHEEL.rotation_euler.y=t*11
  for arm,i,side,p0 in CREW_ARMS:
   end=Vector((side*(.26+.055*math.sin(t*3+i)),-.28,.77+.18*math.sin(t*3.7+i+side)))
   delta=end-p0;arm.location=(p0+end)/2;arm.rotation_quaternion=Vector((0,0,1)).rotation_difference(delta.normalized());arm.scale.z=delta.length/.34
 for o,off,side in TRACKS:
  x,z,ang=path(off+distance);o.location=(x,side*1.3,z);o.rotation_euler.y=-ang
 # Crushing deforms the real wire curves; snapped posts and springing wire.
 k=smooth((t-1.15)/.22) if SHOT in ('hook','loop') else (smooth((t-CROSS_HIT)/.22) if SHOT=='cross' else 0)
 for o,x,y in POSTS:
  if x<5 and -2<y<2.5:o.rotation_euler.y=-1.4*k;o.rotation_euler.x=.24*k
 for o,x,z,pts in WIRES:
  if x>5:continue
  for j,p in enumerate(o.data.splines[0].points):
   xx,yy,zz=pts[j];contact=math.exp(-((yy+.1)/2.2)**6)
   p.co.z=zz*(1-.93*k*contact)+.14*k*math.sin((t-1.15)*19+j*.2)*math.exp(-max(0,t-1.15)*2)*contact
   p.co.x=xx+.27*k*contact
 for o,x,y,z in BARBS:
  if x<5:
   c=math.exp(-((y+.1)/2.2)**6);o.location=(.27*k*c,0,-z*.93*k*c)
bpy.app.handlers.frame_change_pre.append(on_frame)
still=arg('--still');want=sorted(int(x) for x in still.split(',')) if still else None
for f in range(-25,1):sc.frame_set(f)
for f in range(1,(max(want) if want else NF)+1):
 sc.frame_set(f);on_frame(sc)
 if (want and f in want) or not want:
  sc.render.filepath=os.path.join(OUT,('still_' if want else 'f_')+f'{f:04d}.png');bpy.ops.render.render(write_still=True)
print('COMPLETE',SHOT,flush=True)

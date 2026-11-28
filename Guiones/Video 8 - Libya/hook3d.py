"""Hook propio usando materiales, geometría, cámara y animación del kit de V7."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE.parent/'Video 7 - Middle East'/'blender_kit.py').read_text(encoding='utf-8')
exec(compile(source[:source.index('globals()["shot_" + SHOT]()')],str(HERE/'blender_kit_reused.py'),'exec'))
sun(2.8,(math.radians(45),0,math.radians(-35)),(1,.86,.68))
water=mat('Mediterranean',(0.025,.16,.22),rough=.28)
box('sea',(300,300,.04),(0,0,-.14),water)
sand=mat('quay',(0.48,.41,.3));box('quay',(20,3,.65),(0,2.7,.12),sand)
for i in range(9):
    box('port warehouse',(1.6,1.8,rnd.uniform(.7,1.5)),(-8+i*2,5,.6),mat('stucco'+str(i),(.55+i*.015,.47,.35)))
root=bpy.data.objects.new('Merkury reconstruction',None);sc.collection.objects.link(root)
grey=mat('naval grey',(.22,.28,.32),rough=.6,metal=.15)
verts=[(-3,-.46,-.2),(-3,.46,-.2),(2.3,.46,-.2),(3.25,0,-.2),(2.3,-.46,-.2),(-3,-.46,.36),(-3,.46,.36),(2.3,.46,.36),(3.25,0,.36),(2.3,-.46,.36)]
faces=[(0,4,3,2,1),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
me=bpy.data.meshes.new('hull');me.from_pydata(verts,[],faces);obj_from(me,'hull',grey).parent=root
for name,sz,loc in [('superstructure',(2.8,.7,.55),(-.6,0,.62)),('bridge',(1,.6,.5),(.4,0,1.06)),('mast',(.06,.06,1.5),(-.4,0,1.7)),('gun',(.4,.4,.23),(1.8,0,.52)),('barrel',(.8,.06,.06),(2.15,0,.62))]:
    box(name,sz,loc,grey).parent=root
for y in [-.28,.28]:
    box('radar',(.7,.04,.16),(-.4,y,1.9),grey).parent=root
windows=mat('bridge windows',(.025,.09,.13),metal=.2)
for x in [.05,.25,.45,.65,.85]:
    box('bridge window',(.14,.012,.14),(x,-.308,1.12),windows).parent=root
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.24,location=(-1.25,0,1.25));bpy.context.object.data.materials.append(mat('radome',(.65,.7,.72)));bpy.context.object.parent=root
cyl('gun turret',.24,.22,(1.8,0,.57),grey).parent=root
for x in [-2.8,-2.4,-2,-1.6,1.1,1.5,1.9,2.3]:
    for y in [-.43,.43]:
        cyl('rail stanchion',.009,.18,(x,y,.44),grey,seg=6).parent=root
for y in [-.43,.43]:box('aft rail',(1.7,.014,.014),(-2.1,y,.54),grey).parent=root
deck=mat('helipad',(.13,.18,.2));cyl('flight deck',.39,.012,(-2.35,0,.37),deck,seg=32).parent=root
font=bpy.data.curves.new('hull number','FONT');font.body='734';font.size=.32;font.extrude=.001
ob=obj_from(font,'pennant 734',mat('number white',(.9,.92,.91)));ob.location=(1.65,-.466,-.02);ob.rotation_euler=(math.pi/2,0,0);ob.parent=root
keys(root,'rotation_euler',[(1,(math.radians(-8),0,0)),(90,(math.radians(-17),0,0)),(180,(math.radians(-25),0,0))])
keys(root,'location',[(1,(0,0,0)),(180,(0,0,-.17))])
firemat=mat('fire',(1,.22,.012),emit=1.8);smoke=mat('smoke',(.075,.08,.085),rough=1)
for i in range(18):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,0));o=bpy.context.object;o.name='fire';o.data.materials.append(firemat)
    base=Vector((1.5+rnd.uniform(-.45,.45),-.48+rnd.uniform(-.12,.12),.1+rnd.uniform(0,.3)))
    keys(o,'location',[(1,base),(80,base+Vector((.3,0,1))),(180,base+Vector((.8,0,1.3)))])
    r=rnd.uniform(.12,.3);keys(o,'scale',[(1,(r,r,r*1.6)),(35,(r*1.4,r,r*2)),(120,(r*.5,)*3),(180,(r*.4,)*3)])
for i in range(16):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);o=bpy.context.object;o.name='rising smoke';o.data.materials.append(smoke)
    base=Vector((1.5+rnd.uniform(-.3,.3),.2,.8+i*.13));r=.2+i*.025
    keys(o,'location',[(1,base),(180,base+Vector((1.5,0,2.2)))])
    keys(o,'scale',[(1,(r,)*3),(180,(r*1.5,)*3)])
for i in range(25):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(1.5+rnd.uniform(-.7,.7),-.9+rnd.uniform(-.5,.2),.03));o=bpy.context.object;o.name='splash';o.data.materials.append(mat('foam'+str(i),(.6,.85,.9)))
    keys(o,'scale',[(1,(.03,.03,.08)),(25,(.02,.02,.25)),(60,(.001,)*3),(180,(.001,)*3)])
cam,tgt=camera(36)
keys(cam,'location',[(1,(8,-11,5)),(21,(7.6,-10.5,4.8)),(22,(4.8,-5.8,2.9)),(42,(4.6,-5.5,2.8)),(43,(1,-8,9)),(180,(2,-9,8))])
keys(tgt,'location',[(1,(.2,0,.7)),(21,(.2,0,.7)),(22,(.8,0,.6)),(42,(.8,0,.6)),(43,(0,0,.4)),(180,(0,0,.4))])
for ob in [cam,tgt]:
    try:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation='LINEAR'
    except Exception:pass
sc.render.image_settings.file_format='JPEG';sc.render.image_settings.quality=92
os.makedirs(OUT,exist_ok=True)
if STILL:
    for fr in map(int,STILL.split(',')):
        sc.frame_set(fr);sc.render.filepath=os.path.join(OUT,f'still_{fr:04d}.jpg');bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath=os.path.join(OUT,'f_');bpy.ops.render.render(animation=True)

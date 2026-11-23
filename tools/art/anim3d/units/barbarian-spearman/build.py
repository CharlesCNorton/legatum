"""Barbarian spearman: real MPFB anatomy and original fitted 3D kit."""
import bpy, os, sys, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/barbarian-spearman'; A=R/'assets/barbarian-spearman'
M.mkdir(parents=True,exist_ok=True);random.seed(81)
# Reuse the lead's reviewed geometry and two-bone posing utilities, without running its model.
shared=Path('tools/art/anim3d/scene.py').read_text()
exec(shared[shared.index('def material('):shared.index("bpy.ops.object.select_all(action='SELECT')")])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.48,muscle=.90,weight=.61,height=.53,proportions=.6)
body=HumanService.create_human(macro_detail_dict=macro);body.name='MPFB barbarian anatomy'
bpy.context.view_layer.update(); ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs=[v.co.z for v in me.vertices];ev.to_mesh_clear()
f=1.78/(max(zs)-min(zs));body.scale=(f*1.08,f,f)
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Barbarian skeleton';rig.location.z=.16
sc=bpy.context.scene
# Framing at 256: base spans x55..200, face around 139,36; orthographic miniature lens.
bpy.ops.object.camera_add(location=(0,-8,3.5));sc.camera=bpy.context.object
cam=sc.camera;cam.name='Painting camera';cam.data.type='ORTHO';cam.data.ortho_scale=2.32
cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
def pixel(x,y,depth=0):
 # Inverse orthographic screen coordinate on a constant world-Y depth plane.
 q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0))
 center=Vector((0,0,.96));p=center+right*((x/256-.5)*2.32)+up*((.5-y/256)*2.32)
 direction=q@Vector((0,0,-1));p+=direction*((depth-p.y)/direction.y)
 return p
# Pigments are linear values; displayed cream is calibrated by the rest grade.
skin=material('Painted warm skin',(.43,.23,.12),0,.7)
linen=material('Painted flax linen',(.55,.43,.28),0,.88)
fur=material('Wolf brown fur',(.105,.074,.043),0,.92)
hair=material('Ochre brown hair',(.13,.075,.032),0,.75)
leather=material('Scuffed hide leather',(.12,.061,.025),0,.75)
rawhide=material('Ochre rawhide shield',(.59,.43,.24),0,.79)
red=material('Iron oxide red',(.35,.025,.009),0,.8)
steel=material('Worn iron',(.46,.49,.50),1,.36)
brass=material('Aged brass',(.47,.29,.07),1,.4)
wood=material('Ash shaft',(.24,.10,.025),0,.65)
stone=material('Warm cream #E9CFA0',(.815,.624,.352),0,.87)
body.data.materials.clear();body.data.materials.append(skin)
sub=body.modifiers.new('Smooth anatomical topology','SUBSURF');sub.levels=sub.render_levels=1
for p in body.data.polygons:p.use_smooth=True
# Pose matches the low weapon and wide bent-knee painting.
limb('thigh_r','calf_r',(-.40,-.16,-.05),(-.45,-.48,.5))
limb('thigh_l','calf_l',(.28,.39,-.05),(.40,-.32,.5))
limb('upperarm_r','lowerarm_r',tuple(pixel(76,111,-.24)-rig.location),(-.55,-.10,1.17))
limb('upperarm_l','lowerarm_l',tuple(pixel(158,112,-.15)-rig.location),(.52,-.05,1.14))
for side in ('r','l'):
 aim_bone('hand_'+side,(.08,-.02,-.02))
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):
   p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.05
p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.y=-.25
bpy.context.view_layer.update();head_matrix=p.matrix.copy();head_matrix.translation+=Vector((.075,0,.025));p.matrix=head_matrix
bpy.context.view_layer.update()
# Clothing is a full circumference shell, with folded hem and real thickness.
def garment(name,rings,mat,bone,fold=.008):
 vs=[];fs=[];n=64
 for j,(z,rx,ry,cy) in enumerate(rings):
  for i in range(n):
   a=i*2*pi/n; r=fold*sin(a*13+j*.4)+fold*.5*sin(a*23)
   vs.append(((rx+r)*sin(a),cy-(ry+r)*cos(a),z+(.009*sin(a*19) if j==0 else 0)))
 for j in range(len(rings)-1):
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 o=solid(mesh(name,vs,fs,mat),.009);bevel(o,.002);attach(o,bone);return o
# Tunic follows the torso; skirt flares past both thighs.
garment('Linen fitted tunic',[(.98,.19,.13,0),(1.13,.19,.14,0),(1.45,.25,.16,0),(1.60,.21,.12,0)],linen,'spine_03')
skirt=garment('Torn folded linen skirt',[(.77,.34,.22,0),(.84,.31,.20,0),(.96,.25,.17,0),(1.10,.20,.14,0)],linen,'pelvis',.017)
# Trousers and boot shells follow actual evaluated anatomy and retain original weights.
def shell(name,predicate,mat,offset):
 # Convert the posed skin into a fitted shell then attach rigidly to its named segment.
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh()
 faces=[p for p in me.polygons if all(predicate(body.matrix_world@me.vertices[i].co) for i in p.vertices)]
 ids=sorted({i for p in faces for i in p.vertices});mp={v:i for i,v in enumerate(ids)}
 vs=[body.matrix_world@(me.vertices[i].co+me.vertices[i].normal*offset) for i in ids]
 o=solid(mesh(name,[tuple(v) for v in vs],[[mp[i] for i in p.vertices] for p in faces],mat),.006)
 ev.to_mesh_clear();return o
for side,sg in [('r',-1),('l',1)]:
 o=shell('Hide breeches '+side,lambda v,s=sg:v.x*s>0 and .42<v.z<.91,fur,.019);attach(o,'thigh_'+side)
 o=shell('Leather boot '+side,lambda v,s=sg:v.x*s>0 and v.z<.50,leather,.013);attach(o,'calf_'+side)
 # Crossed wrap laces, aligned along the calf rather than world axes.
 calf=rig.pose.bones['calf_'+side];a=calf.head+rig.location;b=calf.tail+rig.location
 for phase in [0,pi]:
  pts=[]
  for k in range(90):
   t=k/89;v=b.lerp(a,.06+.85*t);theta=t*pi*9+phase;v+=Vector((.070*cos(theta),.063*sin(theta),0));pts.append(tuple(v))
  attach(curve('Crossed calf bindings '+side,pts,.007,linen),'calf_'+side)
# Fur cape: a thick folded mantle and hundreds of tapered 3D locks, no alpha cards.
vs=[];fs=[];nx=32;ny=24
for j in range(ny+1):
 t=j/ny
 for i in range(nx+1):
  u=i/nx;vs.append(((u-.5)*(.65+.22*t),.11+.11*t+.035*sin(u*10*pi),1.62-.89*t+.025*sin(u*17*pi)))
for j in range(ny):
 for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
cape=solid(mesh('Folded fur cloak',vs,fs,fur),.018);attach(cape,'spine_03')
def lock(name,points,width,mat,bone):
 # Solid tapered triangular tuft, with a raised ridge and beveled edges.
 a,b,c=map(Vector,points);side=(b-a).cross(Vector((0,-1,.1))).normalized()*width
 verts=[a-side,a+side,b+side*.6,b-side*.6,c,b+Vector((0,-width*.7,0))]
 ob=mesh(name,[tuple(v) for v in verts],[(0,1,5),(1,2,5),(2,4,5),(4,3,5),(3,0,5),(0,3,4,2,1)],mat)
 bevel(ob,.001,2);attach(ob,bone)
# Front pelt collar trails from shoulders to sternum; tufts overlap like the painting.
for i in range(170):
 a=random.uniform(-1.7,1.7);t=random.random();x=.30*sin(a);y=-.13*cos(a)-.035;z=1.64-.25*t+.045*abs(sin(a))
 lock('Fur collar lock',[(x,y,z),(x+.01*sin(a),y-.015,z-.040),(x+.02*sin(a),y-.01,z-.075)],.010+random.random()*.006,fur,'spine_03')
for i in range(150):
 u=random.random();t=random.random();x=(u-.5)*(.65+.22*t);y=.11+.11*t+.035*sin(u*10*pi);z=1.62-.89*t
 lock('Cloak fur lock',[(x,y,z),(x+.018,y+.018,z-.035),(x+.025,y+.02,z-.07)],.016,fur,'spine_03')
# Hair and beard matched to anatomical head (full 3D swept locks).
h=rig.pose.bones['head'];hc=(h.head+h.tail)*.5+rig.location
vs=[];fs=[]
for j in range(13):
 t=j*pi/24
 for i in range(64):
  a=i*2*pi/64;vs.append(tuple(hc+Vector((.104*cos(t)*sin(a),.113*cos(t)*cos(a),.040+.125*sin(t)))))
for j in range(12):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,a+64,b+64,b))
attach(solid(mesh('Sculpted swept hair cap',vs,fs,hair),.009),'head')
for i in range(180):
 a=random.uniform(-pi,pi);t=random.uniform(0,.95);x=hc.x+.10*sin(a);y=hc.y+.105*cos(a);z=hc.z+.105-.08*t
 if cos(a)<-.45 and z<hc.z+.065:continue
 end=Vector((x-.08,y+.075,z-.19-random.random()*.05))
 lock('Swept shoulder hair',[(x,y,z),tuple(Vector((x-.02,y+.03,z-.07))),tuple(end)],.017,hair,'head')
for i in range(75):
 a=random.uniform(-1.3,1.3);x=hc.x+.072*sin(a);y=hc.y-.105*cos(a);z=hc.z-.045+random.uniform(-.02,.015)
 lock('Full beard lock',[(x,y,z),(x,y-.008,z-.035),(x*.8,y,z-.080)],.010,hair,'head')
# A wide leather belt, stitched edges, brass buckle, baldric, and hanging strap ends.
garment('Waist belt',[(1.005,.211,.151,0),(1.055,.211,.151,0)],leather,'pelvis',.001)
for z in [1.01,1.05]:attach(curve('Belt stitched border',[(.214*sin(a),-.155*cos(a),z) for a in [i*2*pi/96 for i in range(97)]],.0025,linen),'pelvis')
for x in [-.045,.045]:attach(curve('Buckle sides',[(x,-.172,1.01),(x,-.172,1.06)],.006,brass),'pelvis')
for z in [1.01,1.06]:attach(curve('Buckle crossbar',[(-.045,-.172,z),(.045,-.172,z)],.006,brass),'pelvis')
attach(curve('Thick leather baldric',[(-.17,-.175,1.49),(-.10,-.21,1.34),(.10,-.19,1.08)],.020,leather),'spine_03')
attach(sphere('Circular cloak brooch',(-.17,-.20,1.48),(.031,.012,.031),brass),'spine_03')
# Low, long spear (all pieces parented to a control at the actual palm).
grip=rig.pose.bones['hand_r'].head+rig.location+Vector((.01,-.025,0))
direction=(pixel(229,157,-.26)-pixel(22,97,-.26)).normalized()
weapon=bpy.data.objects.new('Spear grip control',None);bpy.context.collection.objects.link(weapon);weapon.location=grip;attach(weapon,'hand_r')
def weapon_part(o):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=weapon;o.matrix_world=w;return o
start=grip-direction*.52;end=grip+direction*1.36
weapon_part(curve('Ash spear shaft',[tuple(start),tuple(end)],.011,wood))
weapon_part(curve('Iron spear socket',[tuple(end-direction*.11),tuple(end)],.016,steel))
side=Vector((-direction.z,0,direction.x))*.040;tip=end+direction*.22
weapon_part(mesh('Forged leaf spearhead',[tuple(end-side),tuple(end+side),tuple(end+Vector((0,-.014,0))),tuple(end+Vector((0,.014,0))),tuple(tip)],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(0,3,1,2)],steel,False))
# Oval rawhide shield, deliberately slim in screen space but deep and convex in 3D.
center=pixel(181,115,-.34);rx=.205;rz=.70
vs=[tuple(center+Vector((0,-.075,0)))];fs=[];nr=12;ns=80
for j in range(1,nr+1):
 t=j/nr
 for i in range(ns):
  a=i*2*pi/ns;vs.append(tuple(center+Vector((rx*t*sin(a)-.055*t*cos(a),-.075*(1-t*t),rz*t*cos(a)))))
for i in range(ns):fs.append((0,1+(i+1)%ns,1+i))
for j in range(nr-1):
 for i in range(ns):a=1+j*ns+i;b=1+j*ns+(i+1)%ns;fs.append((a,b,b+ns,a+ns))
shield=solid(mesh('Convex oval rawhide shield',vs,fs,rawhide),.025);bevel(shield,.004);attach(shield,'lowerarm_l')
for rr in [1,.97]:
 pts=[tuple(center+Vector((rx*rr*sin(a)-.055*rr*cos(a),-.005,rz*rr*cos(a)))) for a in [2*pi*i/128 for i in range(129)]]
 attach(curve('Rawhide rolled shield rim',pts,.009,leather),'lowerarm_l')
for i in range(46):
 a=2*pi*i/46;c=center+Vector((rx*sin(a)-.055*cos(a),-.008,rz*cos(a)))
 attach(curve('Shield rim lacing',[tuple(c+Vector((-.010,-.009,-.012))),tuple(c+Vector((.010,-.013,.012)))],.0035,linen),'lowerarm_l')
attach(sphere('Domed iron shield boss',tuple(center+Vector((0,-.092,0))),(.072,.040,.10),steel),'lowerarm_l')
# A separate shield control lets the heavy oval settle independently on death.
shield_parts=[o for o in list(sc.objects) if 'shield' in o.name.lower()]
shield_control=bpy.data.objects.new('Shield grip control',None);bpy.context.collection.objects.link(shield_control);shield_control.location=center;attach(shield_control,'lowerarm_l')
for ob in shield_parts:
 world=ob.matrix_world.copy();ob.parent=shield_control;ob.parent_type='OBJECT';ob.matrix_world=world
# Red armband, an identity accent visible even at 64 px.
o=shell('Red upper arm binding',lambda v:v.x<-.18 and 1.25<v.z<1.35,red,.018);attach(o,'upperarm_r')
# Closed lasted boots bridge ankle to stone and show real toes/soles in side views.
for side in ['r','l']:
 ankle=rig.pose.bones['foot_'+side].head+rig.location
 boot=sphere('Lasted leather shoe '+side,(ankle.x,ankle.y-.075,.148),(.071,.145,.061),leather)
 bpy.context.view_layer.objects.active=boot;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);attach(boot,'foot_'+side)
 for k in range(5):
  y=ankle.y-.16+k*.030
  pts=[(ankle.x+.065*cos(a),y,.15+.055*sin(a)) for a in [i*pi/16 for i in range(17)]]
  attach(curve('Shoe wrap '+side,pts,.005,linen),'foot_'+side)
# The base stays immutable throughout every animation.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.655,depth=.095,location=(0,0,.04));base=bpy.context.object;base.name='Stationary cream base';base.data.materials.append(stone);bevel(base,.016,3)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.18,.18,.18);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
for name,loc,power,size,col in [('Warm key',(-3,-4,6),650,3,(1,.9,.73)),('Soft fill',(4,-3,3),150,4,(.87,.92,1)),('Cool rim',(1,3,4),350,2,(.76,.86,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='barbarian-spearman';sc['stage']='plain';sc['source']='MPFB 2.0.18 CC0 anatomy, original kit, CC BY 4.0 painting'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
(M/'model-info.json').write_text(json.dumps({'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects)},indent=2))
print('BARBARIAN_BUILD_READY')

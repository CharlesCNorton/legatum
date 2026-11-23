"""Sample Quaternius's real horse actions, with saddle-parented rider performance."""
import bpy,os,ast,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True,'Idle',80),'move':(8,12,True,'Gallop',14),'attack':(10,14,False,'Idle',80),'hit':(4,12,False,'Idle_HitReact_Left',16),'death':(10,10,False,'Death',24)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
for clip,(count,fps,loop,src,length) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'cuirassier.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 raised={n:Matrix(m) for n,m in json.loads(hrig.get('raised_idle_foreleg','{}')).items()}
 act=bpy.data.actions['AnimalArmature|'+src];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
 # Opaque smoke meshes have actual volume and keyed visibility, never zero scale.
 smoke=[]
 if clip=='attack':
  barrel=bpy.data.objects['GEO-pistol steel barrel'];tip=barrel.matrix_world@barrel.data.splines[0].points[-1].co.xyz
  mat=bpy.data.materials.new('MAT-pistol smoke');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.48,.45,.40,1);bs.inputs['Roughness'].default_value=1
  for j in range(4):
   bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.040+j*.011,location=tip+Vector((-.035-j*.045,.01*j,.015*j)));ob=bpy.context.object;ob.name='GEO-pistol smoke '+str(j);ob.data.materials.append(mat);smoke.append(ob)
 poses=[]
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  f=t*length;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  sampled={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};object_matrix=hrig.matrix_basis.copy()
  if clip=='idle':sampled.update(raised)
  if clip=='move':
   # Three-beat canter contact order, using only time-warped source trajectories.
   # Extend the source's short gallop stances, so support persists until one flight phase.
   legs=[('back','R',0.,6.,3.),('back','L',.23,8.5,3.),('front','R',.23,11.5,2.5),('front','L',.46,13.5,2.5)]
   for family,side,start,source_start,stance in legs:
    phase=(t-start)%1
    shifted=(source_start+(phase/.34*stance if phase<.34 else stance+(phase-.34)/.66*(length-stance)))%length
    sc.frame_set(int(shifted),subframe=shifted%1);bpy.context.view_layer.update()
    prefixes=['FrontShoulder','FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','PoleTarget'] if family=='front' else ['BackShoulder','BackLeg','BackUpperLeg','BackLowerLeg','IKBackLeg','FFB','PoleTargetBack']
    for p in hrig.pose.bones:
     if p.name.endswith('.'+side) and p.name.split('.')[0] in prefixes:sampled[p.name]=p.matrix_basis.copy()
  poses.append((sampled,object_matrix))
 hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Cuirassier '+clip+' sampled '+src)
 base={n:Matrix(v) for n,v in json.loads(rig['seated_pose']).items()};root_rest=root.location.copy();rider_rest=rig.matrix_basis.copy();weapons=[o for o in sc.objects if o.name.startswith(('GEO-pistol','GEO-wheellock','GEO-trigger','GEO-barrel'))];weapon_rest={o.name:o.matrix_basis.copy() for o in weapons}
 for i,(pose,obmat) in enumerate(poses):
  f=i+1;t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  sc.frame_set(f)
  for j,ob in enumerate(smoke):
   ob.hide_render=not (i in [3,4]);ob.keyframe_insert('hide_render',frame=f);ob.scale=(1+.25*(i%3),)*3;ob.keyframe_insert('scale',frame=f)
  hrig.matrix_basis=obmat;rig.matrix_basis=rider_rest
  for obj in weapons:obj.matrix_basis=weapon_rest[obj.name]
  for p in hrig.pose.bones:
   p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
   if clip=='death':
    buckle=min(t/.35,1)
    if p.name.startswith('FrontUpperLeg'):p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),.5*buckle)
    if p.name.startswith('FrontLowerLeg'):p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),-.95*buckle)
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  bpy.context.view_layer.update();neck=hrig.pose.bones['Neck1'];head=neck.head.copy();axis=hrig.matrix_world.to_3x3().inverted()@Vector((1,0,0))
  neck.matrix=Matrix.Translation(head)@Quaternion(axis.normalized(),-.34).to_matrix().to_4x4()@Matrix.Translation(-head)@neck.matrix
  for prop in ['location','rotation_quaternion','scale']:neck.keyframe_insert(prop,frame=f)
  hrig.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=f)
  for n,m in base.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  lean=0.;twist=0.
  if clip=='idle':lean=.025*sin(2*pi*t)
  if clip=='move':lean=.10+.055*sin(2*pi*t);twist=.015*sin(2*pi*t)
  if clip=='attack':
   recoil=max(0,1-abs(t-.38)/.18);lean=-.08*recoil
   p=rig.pose.bones['upperarm_r'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((0,1,0),-.16*recoil)
  if clip=='hit':lean=-.22*sin(pi*t);twist=.19*sin(pi*t)
  if clip=='death':
   lean=.85*t;twist=.25*t
   limb('upperarm_r','lowerarm_r',Vector((-.77,.09,1.72)).lerp(Vector((-.25,-.15,.99)),t),(-.48,0,1.18))
  p=rig.pose.bones['spine_02'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),lean)
  p=rig.pose.bones['head'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((0,1,0),twist)
  root.location=root_rest.copy()
  # Pistol attack is fired from a standing mount, with upper-body recoil.
  if clip=='death':
   bpy.context.view_layer.update()
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
   # Remove the source's sideways travel while retaining its articulated collapse.
   fall=min(t/.5,1);center=Vector(((min(v.x for v in vs)+max(v.x for v in vs))/2,(min(v.y for v in vs)+max(v.y for v in vs))/2,0))
   root.location.x-=center.x*fall;root.location.y-=center.y*fall
   root.location.z+=.112-min(v.z for v in vs)
   root.location+=Vector((-.8,.6,0))*(.38*fall)
  root.keyframe_insert('location',frame=f)
  if clip=='death':
   bpy.context.view_layer.update()
   body=bpy.data.objects['Rider MPFB CC0 anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   if lo<.115:
    mat=rig.matrix_world.copy();mat.translation.z+=.115-lo;rig.matrix_world=mat
  rig.keyframe_insert('location',frame=f)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(list(range(1,count)) + [count-1] if clip=='death' else list(range(1,count+1)));sc['horse_source_action']=act.name+(' (source trajectories retimed to three-beat canter with extended stances)' if clip=='move' else '');sc['clip']=clip;sc['loop']=loop
 sc['source_master_sha256']=hashlib.sha256((M/'cuirassier.blend').read_bytes()).hexdigest()
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('MOUNTED_CLIP_READY',clip)

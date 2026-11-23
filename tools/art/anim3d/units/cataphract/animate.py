"""Sample Quaternius's real horse actions, with saddle-parented rider performance."""
import bpy,os,ast,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cataphract';(M/'clips').mkdir(exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reins import key_reins
from rider_motion import sample_rider
from contacts import key_contacts
CLIPS={'idle':(8,10,True,'Idle',80),'move':(8,12,True,'Walk',28),'attack':(10,14,False,'Walk',28),'hit':(4,12,False,'Idle_HitReact_Left',16),'death':(10,10,False,'Death',24)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
for clip,(count,fps,loop,src,length) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'cataphract.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 act=bpy.data.actions['AnimalArmature|'+src];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
 poses=[]
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  f=t*length;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  sampled={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};object_matrix=hrig.matrix_basis.copy()
  poses.append((sampled,object_matrix))
 human, human_samples=sample_rider(rig,clip,count,loop)
 hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Cataphract '+clip+' sampled '+src)
 base={n:Matrix(v) for n,v in json.loads(rig['seated_pose']).items()};root_rest=root.location.copy();rider_rest=rig.matrix_basis.copy();weapons=[bpy.data.objects[n] for n in ['Spear ash shaft','Iron spear blade']];weapon_rest={o.name:o.matrix_basis.copy() for o in weapons}
 for i,(pose,obmat) in enumerate(poses):
  f=i+1;t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  sc.frame_set(f);hrig.matrix_basis=obmat;rig.matrix_basis=rider_rest
  for obj in weapons:obj.matrix_basis=weapon_rest[obj.name]
  for p in hrig.pose.bones:
   p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
   if clip=='death':
    buckle=min(t/.35,1)
    if p.name.startswith('FrontUpperLeg'):p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),.5*buckle)
    if p.name.startswith('FrontLowerLeg'):p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),-.95*buckle)
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  hrig.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=f)
  for n,m in base.items():
   p=rig.pose.bones[n];p.matrix_basis=m;p.rotation_mode='QUATERNION'
   if n in human_samples[i]:p.rotation_quaternion=p.rotation_quaternion@human_samples[i][n]
  bpy.context.view_layer.update()
  lean=0.;twist=0.
  if clip=='attack':
   thrust=sin(pi*t)**.65;lean=.28*thrust
   hand=rig.pose.bones['hand_r'].head.copy();elbow=rig.pose.bones['lowerarm_r'].head.copy()
   limb('upperarm_r','lowerarm_r',hand+Vector((0,-.16*thrust,-.10*thrust)),elbow)
   angle=math.atan(.25)+thrust*.65;aim_bone('hand_r',(0,-sin(angle),cos(angle)))
  if clip=='hit':
   angle=math.atan(.25)+.25*sin(pi*t);aim_bone('hand_r',(0,-sin(angle),cos(angle)))
  p=rig.pose.bones['spine_02'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),lean)
  p=rig.pose.bones['head'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((0,1,0),twist)
  root.location=root_rest.copy()
  if clip=='attack':root.location.y-=.08*sin(pi*t)
  if clip=='death':
   bpy.context.view_layer.update()
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
   # Remove the source's sideways travel while retaining its articulated collapse.
   fall=min(t/.5,1);center=Vector(((min(v.x for v in vs)+max(v.x for v in vs))/2,(min(v.y for v in vs)+max(v.y for v in vs))/2,0))
   root.location.x-=center.x*fall;root.location.y-=center.y*fall
   root.location.z+=.112-min(v.z for v in vs)
  root.keyframe_insert('location',frame=f)
  if clip=='attack':
   # Slide the rigid lance through the grip so its point clears the muzzle in
   # the thrust; preserve length and return to the painted guard at both ends.
   bpy.context.view_layer.update();shaft=weapons[0]
   points=[v.co for v in shaft.data.vertices]
   direction=(shaft.matrix_world@max(points,key=lambda p:p.z)-shaft.matrix_world@min(points,key=lambda p:p.z)).normalized()
   for obj in weapons:
    matrix=obj.matrix_world.copy();matrix.translation+=direction*(.55*thrust);obj.matrix_world=matrix
    obj.keyframe_insert('location',frame=f)
  if clip=='death':
   bpy.context.view_layer.update()
   body=bpy.data.objects['Rider MPFB CC0 anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   if lo<.115:
    mat=rig.matrix_world.copy();mat.translation.z+=.115-lo;rig.matrix_world=mat
  if clip=='death':
   # Adapt the free-standing source fall to a mounted collapse: after release,
   # gravity/contact settles each hand on the evaluated horse surface. Keep the
   # source elbow plane and two-bone lengths, rather than holding the guard pose.
   settle=max(0,min(1,(t-.45)/.45));settle=settle*settle*(3-2*settle)
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
   for side in ['l','r']:
    bpy.context.view_layer.update()
    hand=rig.matrix_world@rig.pose.bones['hand_'+side].head
    found,point,normal,_=ev.closest_point_on_mesh(ev.matrix_world.inverted()@hand)
    if found:
     target=ev.matrix_world@point+(ev.matrix_world.to_3x3()@normal).normalized()*.035
     target=rig.matrix_world.inverted()@hand.lerp(target,settle)
     elbow=rig.pose.bones['lowerarm_'+side].head.copy()
     limb('upperarm_'+side,'lowerarm_'+side,target,elbow)
   # The released lance must not leave a dead rider holding a raised closed fist.
   release=max(0,min(1,(t-.35)/.4))
   for name,matrix in base.items():
    if any(name.startswith(digit) for digit in ['index','middle','ring','pinky']):
     rig.pose.bones[name].rotation_quaternion=matrix.to_quaternion().slerp(Quaternion(),release*.8)
   bpy.context.view_layer.update()
   shaft=weapons[0];points=[v.co for v in shaft.data.vertices]
   a=shaft.matrix_world@min(points,key=lambda p:p.z);b=shaft.matrix_world@max(points,key=lambda p:p.z);center=(a+b)*.5
   release=max(0,min(1,(t-.35)/.4));release=release*release*(3-2*release)
   rotation=Quaternion((1,0,0,0)).slerp((b-a).normalized().rotation_difference(Vector((1,0,0))),release)
   destination=center.lerp(Vector((0,0,.145)),release)
   transform=Matrix.Translation(destination)@rotation.to_matrix().to_4x4()@Matrix.Translation(-center)
   for obj in weapons:
    obj.matrix_world=transform@obj.matrix_world;obj.rotation_mode='QUATERNION'
    for prop in ['location','rotation_quaternion','scale']:obj.keyframe_insert(prop,frame=f)
  rig.keyframe_insert('location',frame=f)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  key_reins(f)
 key_contacts(count,loop,clip)
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(list(range(1,count)) + [count-1] if clip=='death' else list(range(1,count+1)));sc['horse_source_action']=act.name;sc['clip']=clip;sc['loop']=loop
 sc['source_master_sha256']=hashlib.sha256((M/'cataphract.blend').read_bytes()).hexdigest()
 sc['rider_source_action']=human
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('CATAPHRACT_CLIP_READY',clip)

"""Sample Quaternius's real horse actions, with saddle-parented rider performance."""
import bpy,os,ast,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from bpy_extras.object_utils import world_to_camera_view
from math import sin,cos,pi
sys.path.insert(0,str(Path(__file__).parent))
from tack import reins
from rider_motion import sample_rider
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True,'Idle',80),'move':(8,12,True,'Gallop',14),'attack':(10,14,False,'Gallop',14),'hit':(4,12,False,'Idle_HitReact_Left',16),'death':(10,10,False,'Death',24)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
for clip,(count,fps,loop,src,length) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'cavalry.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 rest_pose={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
 rider_action,rider_samples=sample_rider(rig,clip,count,loop)
 raised={n:Matrix(m) for n,m in json.loads(hrig['registered_stance']).items()}
 act=bpy.data.actions['AnimalArmature|'+src];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
 poses=[]
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  # Sparse source actions must not inherit registered rest translations/scales.
  for p in hrig.pose.bones:p.matrix_basis=Matrix.Identity(4)
  f=t*length;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  sampled={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};object_matrix=hrig.matrix_basis.copy()
  if clip=='idle':sampled.update(raised)
  if clip in {'attack','hit','death'}:
   blend=min(t/.22,1) if clip=='death' else sin(pi*t)**.65
   sampled={n:rest_pose[n].lerp(m,blend) for n,m in sampled.items()}
  # Preserve source tail timing with restrained amplitude on the longer
  # painted hair sculpture; raw source angles turn it into an upright whip.
  for n,m in sampled.items():
   if n.startswith('Tail'):sampled[n]=rest_pose[n].lerp(m,.4 if clip=='death' else .25)
  poses.append((sampled,object_matrix))
 hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Cavalry '+clip+' sampled '+src)
 base={n:Matrix(v) for n,v in json.loads(rig['seated_pose']).items()};root_rest=root.location.copy();rider_rest=rig.matrix_basis.copy();weapons=[bpy.data.objects[n] for n in ['GEO-sabre-grip','GEO-sabre-blade','GEO-sabre-guard']];weapon_rest={o.name:o.matrix_basis.copy() for o in weapons}
 for i,(pose,obmat) in enumerate(poses):
  f=i+1;t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  sc.frame_set(f);hrig.matrix_basis=obmat;rig.matrix_basis=rider_rest
  for obj in weapons:obj.matrix_basis=weapon_rest[obj.name]
  for p in hrig.pose.bones:
   p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
   if clip=='death':
    buckle=min(t/.35,1)
    if p.name.startswith('FrontUpperLeg'):p.rotation_quaternion=p.rotation_quaternion @ Quaternion((1,0,0),.5*buckle)
    if p.name.startswith('FrontLowerLeg'):p.rotation_quaternion=p.rotation_quaternion @ Quaternion((1,0,0),-.95*buckle)
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  hrig.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=f)
  for n,m in base.items():rig.pose.bones[n].matrix_basis=m
  for n,delta in rider_samples[i].items():
   p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion @ delta
  bpy.context.view_layer.update()
  lean=0.;twist=0.
  if clip=='move':lean=.10+.055*sin(2*pi*t);twist=.015*sin(2*pi*t)
  if clip=='attack':
   thrust=sin(pi*t)**.8;lean=.15*thrust
   p=rig.pose.bones['upperarm_r'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion @ Quaternion((1,0,0),.2*thrust)
   p=rig.pose.bones['lowerarm_r'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion @ Quaternion((0,1,0),.15*thrust)
   bpy.context.view_layer.update()
   wrist=rig.pose.bones['hand_r'];pivot=wrist.head.copy();wrist.matrix=Matrix.Translation(pivot) @ Quaternion((1,0,0),1.3*thrust).to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ wrist.matrix
  p=rig.pose.bones['spine_02'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion @ Quaternion((1,0,0),lean)
  p=rig.pose.bones['head'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion @ Quaternion((0,1,0),twist)
  root.location=root_rest.copy()
  if clip=='attack':root.location.y-=.16*sin(pi*t)
  if clip=='death':
   bpy.context.view_layer.update()
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
   # Remove the source's sideways travel while retaining its articulated collapse.
   fall=min(t/.5,1);center=Vector(((min(v.x for v in vs)+max(v.x for v in vs))/2,(min(v.y for v in vs)+max(v.y for v in vs))/2,0))
   root.location.x-=center.x*fall;root.location.y-=center.y*fall
   root.location.z+=.112-min(v.z for v in vs)
   screen_right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0));screen_right.z=0
   root.location-=screen_right*.20*fall
   # Fold the released sword arm across the body instead of leaving a raised
   # fist hanging in the air after the horse and rider have settled.
   bpy.context.view_layer.update()
   folded=max(0,min(1,(t-.35)/.45));folded=folded*folded*(3-2*folded)
   pelvis=rig.pose.bones['pelvis'].head.copy()
   target=rig.pose.bones['hand_r'].head.lerp(pelvis+Vector((-.18,-.20,.18)),folded)
   pole=rig.pose.bones['lowerarm_r'].head.lerp(pelvis+Vector((-.55,-.25,.35)),folded)
   limb('upperarm_r','lowerarm_r',target,pole)
  # A hit recoil previously lifted the sabre out of the fixed camera. Rotate
  # the articulated wrist (including fingers/grip), never crop or rescale a frame.
  if clip in {'hit','death'}:
   wrist=rig.pose.bones['hand_r'];axis=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
   for attempt in range(30):
    bpy.context.view_layer.update()
    blade=weapons[1]
    if max(world_to_camera_view(sc,sc.camera,blade.matrix_world @ v.co).y for v in blade.data.vertices)<.965:break
    world=rig.matrix_world @ wrist.matrix;pivot=world.translation.copy()
    turn=Matrix.Translation(pivot) @ Quaternion(axis,-.025).to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    wrist.matrix=rig.matrix_world.inverted() @ turn @ world
   else:raise RuntimeError(f'{clip}: sabre cannot fit the fixed camera')
  root.keyframe_insert('location',frame=f)
  if clip=='death':
   bpy.context.view_layer.update()
   body=bpy.data.objects['Rider MPFB CC0 anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
   if lo<.115:
    mat=rig.matrix_world.copy();mat.translation.z+=.115-lo;rig.matrix_world=mat
  if clip=='death':
   bpy.context.view_layer.update()
   shaft=weapons[0];points=shaft.data.splines[0].points
   a=shaft.matrix_world @ points[0].co.xyz;b=shaft.matrix_world @ points[-1].co.xyz;center=(a+b)*.5
   release=max(0,min(1,(t-.35)/.4));release=release*release*(3-2*release)
   rotation=Quaternion((1,0,0,0)).slerp((b-a).normalized().rotation_difference(Vector((1,0,0))),release)
   destination=center.lerp(Vector((-.3,.1,.16)),release)
   transform=Matrix.Translation(destination) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-center)
   for obj in weapons:
    obj.matrix_world=transform @ obj.matrix_world;obj.rotation_mode='QUATERNION'
    for prop in ['location','rotation_quaternion','scale']:obj.keyframe_insert(prop,frame=f)
  rig.keyframe_insert('location',frame=f)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  bpy.context.view_layer.update();reins(f)
 # Smooth interpolation for the editable rig; delivered samples remain exact.
 for obj in [hrig,rig,root]+weapons:
  if obj.animation_data and obj.animation_data.action:
   for layer in obj.animation_data.action.layers:
    for strip in layer.strips:
     if hasattr(strip,'channelbags'):
      for bag in strip.channelbags:
       for fc in bag.fcurves:
        for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(list(range(1,count)) + [count-1] if clip=='death' else list(range(1,count+1)));sc['horse_source_action']=act.name+' (native synchronized source trajectories)';sc['clip']=clip;sc['loop']=loop;sc['rider_source_action']=rider_action
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'clip':clip,'rider_source_action':rider_action,'source_master_sha256':hashlib.sha256((M/'cavalry.blend').read_bytes()).hexdigest(),'frames':count,'fps':fps,'loop':loop},indent=2))
 print('CAVALRY_CLIP_READY',clip)

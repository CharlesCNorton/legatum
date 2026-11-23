"""Sample Quaternius's real horse actions, with saddle-parented rider performance."""
import bpy,os,ast,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
sys.path.insert(0,str(Path('tools/art/anim3d/units/knight').resolve()))
from reins import update_reins
from tail import update_tail
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True,'Idle',80),'move':(8,12,True,'Walk',28),'attack':(10,14,False,'Gallop',14),'hit':(4,12,False,'Idle_HitReact_Left',16),'death':(10,10,False,'Death',24)}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
human=json.loads((M/'rider-motion.json').read_text())
for clip,(count,fps,loop,src,length) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'knight.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 rest_pose={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
 raised={n:Matrix(m) for n,m in json.loads(hrig.get('raised_idle_foreleg','{}')).items()}
 hrig.animation_data_create();act=bpy.data.actions['AnimalArmature|'+src];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
 poses=[]
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  f=t*length;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  sampled={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};object_matrix=hrig.matrix_basis.copy()
  if clip=='idle':sampled.update(raised)
  if clip in ('attack','hit','death'):
   blend=min(t/.35,1) if clip=='death' else sin(pi*t)**.65
   sampled={n:rest_pose[n].lerp(mat,blend) for n,mat in sampled.items()}
  poses.append((sampled,object_matrix))
 hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Knight '+clip+' sampled '+src)
 base={n:Matrix(v) for n,v in json.loads(rig['seated_pose']).items()};root_rest=root.location.copy();rider_rest=rig.matrix_basis.copy();weapons=[bpy.data.objects[n] for n in ['Spear ash shaft','Iron spear blade','GEO lance gold spiral']];weapon_rest={o.name:o.matrix_basis.copy() for o in weapons}
 for i,(pose,obmat) in enumerate(poses):
  f=i+1;t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  sc.frame_set(f);hrig.matrix_basis=obmat;rig.matrix_basis=rider_rest
  for obj in weapons:obj.matrix_basis=weapon_rest[obj.name]
  for p in hrig.pose.bones:
   p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  hrig.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=f)
  for n,m in base.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  lean=0.;twist=0.
  if clip=='attack':
   thrust=sin(pi*t)**.65;lean=.28*thrust
   start=rig.pose.bones['hand_r'].head.copy();pole=rig.pose.bones['lowerarm_r'].head.copy();direction=rig.pose.bones['hand_r'].vector.normalized()
   limb('upperarm_r','lowerarm_r',start.lerp(Vector((-.31,-.45,1.19)),thrust),pole.lerp(Vector((-.47,-.07,1.13)),thrust))
   aim_bone('hand_r',direction.lerp(Vector((0,-1,0)),thrust))
  if clip in human:
   for name,q in human[clip]['frames'][i].items():
    bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION';bone.rotation_quaternion=bone.rotation_quaternion@Quaternion(q)
  p=rig.pose.bones['spine_02'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((1,0,0),lean)
  p=rig.pose.bones['head'];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion((0,1,0),twist)
  root.location=root_rest.copy()
  if clip=='attack':root.location.y-=.16*sin(pi*t)
  if clip=='death':
   bpy.context.view_layer.update()
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
   # Remove the source's sideways travel while retaining its articulated collapse.
   fall=min(t/.5,1);center=Vector(((min(v.x for v in vs)+max(v.x for v in vs))/2,(min(v.y for v in vs)+max(v.y for v in vs))/2,0))
   root.location.x-=center.x*fall;root.location.y-=center.y*fall
   root.location.z+=.112-min(v.z for v in vs)
  if clip!='death':
   # Bind-space sculpt changes foot extents; ground actual rendered geometry.
   bpy.context.view_layer.update()
   horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   floor=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   # Walk/idle/hit have no flight phase: lower hovering soles as well as
   # raising penetrating ones. Gallop attack retains intentional suspension.
   root.location.z+=(.112-floor) if clip in ('idle','move','hit') else max(0,.112-floor)
  root.keyframe_insert('location',frame=f)
  if clip=='death':
   bpy.context.view_layer.update()
   body=bpy.data.objects['Rider MPFB CC0 anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   if lo<.115:
    mat=rig.matrix_world.copy();mat.translation.z+=.115-lo;rig.matrix_world=mat
  if clip=='death':
   bpy.context.view_layer.update()
   shaft=weapons[0];points=shaft.data.splines[0].points
   a=shaft.matrix_world@points[0].co.xyz;b=shaft.matrix_world@points[-1].co.xyz;center=(a+b)*.5
   release=max(0,min(1,(t-.35)/.4));release=release*release*(3-2*release)
   rotation=Quaternion((1,0,0,0)).slerp((b-a).normalized().rotation_difference(Vector((1,0,0))),release)
   destination=center.lerp(Vector((0,0,.145)),release)
   transform=Matrix.Translation(destination)@rotation.to_matrix().to_4x4()@Matrix.Translation(-center)
   for obj in weapons:
    obj.matrix_world=transform@obj.matrix_world;obj.rotation_mode='QUATERNION'
    for prop in ['location','rotation_quaternion','scale']:obj.keyframe_insert(prop,frame=f)
  bpy.context.view_layer.update();update_reins(f);update_tail(f,t,clip in ('move','attack','hit'))
  rig.keyframe_insert('location',frame=f)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(list(range(1,count)) + [count-1] if clip=='death' else list(range(1,count+1)));sc['horse_source_action']=act.name;sc['rider_source_action']=human[clip]['source'] if clip in human else 'Authored lance attack';sc['clip']=clip;sc['loop']=loop
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('KNIGHT_CLIP_READY',clip)

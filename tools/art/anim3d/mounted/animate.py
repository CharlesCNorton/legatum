"""Sample Quaternius's real horse actions, with saddle-parented rider performance."""
import bpy,os,ast,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from math import sin,cos,pi
sys.path.insert(0,str(Path('tools/art/anim3d/mounted').resolve()))
from reins import update_reins
from tail import update_tail
from source_pose import reset_pose
from contacts import hooves, transfer_contacts
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/horseman-3d';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True,'Idle',80),'move':(8,12,True,'Walk',28),'attack':(10,14,False,'Gallop',14),'hit':(4,12,False,'Idle_HitReact_Left',16),'death':(10,10,False,'Death',24)}
# Measure the original licensed mesh before anatomical fitting. This keeps the
# source's four footfalls; whole-horse grounding alone lost all front contacts.
bpy.ops.wm.open_mainfile(filepath=str(M/'horseman-unpainted.blend'))
source_rig=bpy.data.objects['AnimalArmature'];source_horse=bpy.data.objects['Horse'];source_scene=bpy.context.scene
reset_pose(source_rig)
source_rig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];source_rig.animation_data.action_slot=source_rig.animation_data.action.slots[0]
source_scene.frame_set(0);source_rest_contacts=hooves(source_horse)
reset_pose(source_rig)
source_rig.animation_data.action=bpy.data.actions['AnimalArmature|Walk'];source_rig.animation_data.action_slot=source_rig.animation_data.action.slots[0]
source_walk_contacts=[]
for i in range(9):
 sample=i/8*28;source_scene.frame_set(int(sample),subframe=sample%1);source_walk_contacts.append(hooves(source_horse))
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
# Normalize the task-owned shield before making independent clips.
bpy.ops.wm.open_mainfile(filepath=str(M/'horseman.blend'));horse_rig=bpy.data.objects['AnimalArmature']
for obj in bpy.context.scene.objects:
 if obj.name=='Slung bronze riding shield':
  center=sum(v.co.x for v in obj.data.vertices)/len(obj.data.vertices)
  for v in obj.data.vertices:v.co.x+=.24-center
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(M/'horseman.blend'))
for clip,(count,fps,loop,src,length) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'horseman.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 rest_pose={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
 painted_rest_contacts=hooves(bpy.data.objects['Horse']);contact_offsets=[]
 raised={n:Matrix(m) for n,m in json.loads(hrig.get('raised_idle_foreleg','{}')).items()}
 # glTF actions are sparse: Idle does not key IKBackLeg translations. Leaving
 # a previous Walk pose in those channels tears the cannon away from the hoof.
 reset_pose(hrig)
 act=bpy.data.actions['AnimalArmature|'+src];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
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
 hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Horseman '+clip+' sampled '+src)
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
  for n,m in base.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  lean=0.;twist=0.
  if clip=='idle':lean=.025*sin(2*pi*t)
  if clip=='move':lean=.04+.025*sin(2*pi*t);twist=.012*sin(2*pi*t)
  if clip=='attack':
   thrust=sin(pi*t)**.65;lean=.28*thrust
   start=rig.pose.bones['hand_r'].head.copy();pole=rig.pose.bones['lowerarm_r'].head.copy();direction=rig.pose.bones['hand_r'].vector.normalized()
   limb('upperarm_r','lowerarm_r',start.lerp(Vector((-.31,-.45,1.19)),thrust),pole.lerp(Vector((-.47,-.07,1.13)),thrust))
   aim_bone('hand_r',direction.lerp(Vector((0,-1,0)),thrust))
  if clip=='hit':
   lean=-.22*sin(pi*t);twist=.19*sin(pi*t)
   angle=.90*sin(pi*t);aim_bone('hand_r',(0,-sin(angle),cos(angle)))
  if clip=='death':
   lean=1.1*t;twist=.25*t
   direction=rig.pose.bones['hand_r'].vector.normalized()
   aim_bone('hand_r',direction.lerp(Vector((0,-1,0)),.8*sin(pi*min(t/.75,1))))
   slump=max(0,min(1,(t-.35)/.4));slump=slump*slump*(3-2*slump)
   limb('upperarm_r','lowerarm_r',rig.pose.bones['hand_r'].head.lerp(Vector((-.25,-.24,1.09)),slump),Vector((-.48,-.12,1.19)))
   limb('upperarm_l','lowerarm_l',rig.pose.bones['hand_l'].head.lerp(Vector((.24,-.22,1.09)),slump),Vector((.43,-.12,1.15)))
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
  if clip=='move':
   bpy.context.view_layer.update()
   contact_offsets.append(transfer_contacts(hrig,bpy.data.objects['Horse'],source_walk_contacts[i],source_rest_contacts,painted_rest_contacts))
   for p in hrig.pose.bones:
    for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  if clip not in ('death','move'):
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
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(list(range(1,count)) + [count-1] if clip=='death' else list(range(1,count+1)));sc['horse_source_action']=act.name;sc['clip']=clip;sc['loop']=loop
 if clip=='move':sc['source_contact_transfer']=json.dumps({'source':source_walk_contacts,'offsets':contact_offsets,'method':'licensed actual sole paths; constant x/y rest offset, tapered bone translations, unchanged foot rotations'})
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('MOUNTED_CLIP_READY',clip)

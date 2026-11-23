"""Native CC0 horse actions and rest-basis compensated CC0 rider torso motion."""
import bpy,os,json,math,hashlib,ast
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/keshig';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True,'Idle',80,'Sitting_Idle_Loop'),'move':(8,12,True,'Gallop',14,'Sitting_Idle_Loop'),'attack':(10,14,False,'Gallop',14,'Sitting_Idle_Loop'),'hit':(4,12,False,'Idle_HitReact_Left',16,'Hit_Chest'),'death':(10,10,False,'Death',24,'Death01')}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<joint helpers>','exec'))
for clip,(count,fps,loop,action,length,human) in CLIPS.items():
 if os.environ.get('CLIP_FILTER') and clip!=os.environ['CLIP_FILTER']:continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'keshig.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine'];root=bpy.data.objects['Horse world control']
 sc.frame_set(sc['rest_frame']);bpy.context.view_layer.update()
 horse_rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};native_rest={n:Matrix(m) for n,m in json.loads(sc['horse_source_rest']).items()};seat={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
 floor_height=bpy.data.objects['Stationary cream stone'].location.z+.05;sc['support_height']=floor_height;base_root=root.location.copy();base_scale=root.scale.copy();act=bpy.data.actions['AnimalArmature|'+action];hrig.animation_data.action=act;hrig.animation_data.action_slot=act.slots[0]
 # Reference each source action at its own entry pose. Idle starts at the
 # painted rest instead of snapping from the gallop neck/tail to standing.
 for p in hrig.pose.bones:p.matrix_basis=native_rest[p.name]
 sc.frame_set(sc['rest_frame'] if action=='Gallop' else 0);bpy.context.view_layer.update()
 action_reference={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
 # Preserve open source motion on its original rig. No reoriented feet.
 poses=[]
 for i in range(count+int(loop)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  # Native glTF actions omit static location channels. Reset them before
  # sampling, or fitted locations leak into the source and get applied twice.
  for p in hrig.pose.bones:p.matrix_basis=native_rest[p.name]
  frame=((t*length+sc['rest_frame'])%length) if action=='Gallop' else t*length;sc.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
  pose={p.name:horse_rest[p.name] @ action_reference[p.name].inverted() @ p.matrix_basis for p in hrig.pose.bones}
  if clip=='idle':
   # A mounted archer holds the gallop silhouette at rest; native idle deltas
   # animate neck/head/tail, keeping the reference's supported leg silhouette.
   for p in hrig.pose.bones:
    if not any(k in p.name for k in ['Neck','Head','Tail']):pose[p.name]=horse_rest[p.name]
  if clip in ('hit','death'):
   blend=min(t/.25,1) if clip=='death' else math.sin(math.pi*t)
   pose={n:horse_rest[n].lerp(mat,blend) for n,mat in pose.items()}
  poses.append((pose,hrig.matrix_basis.copy()))
 # Import the licensed standard motion library without executing asset scripts.
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf'))
 added=set(bpy.data.objects)-before;src=next(o for o in added if o.type=='ARMATURE')
 for o in added:
  if o.type=='MESH':o.hide_render=True
 for track in src.animation_data.nla_tracks:track.mute=True
 ha=next(a for a in bpy.data.actions if a.name==human or a.name.endswith('|'+human))
 src.animation_data.action=ha;src.animation_data.action_slot=ha.slots[0]
 mapping={'spine_01':'DEF-spine.001','spine_02':'DEF-spine.002','spine_03':'DEF-spine.003','neck_01':'DEF-neck','head':'DEF-head'}
 if clip=='death':mapping.update({'upperarm_l':'DEF-upper_arm.L','lowerarm_l':'DEF-forearm.L','upperarm_r':'DEF-upper_arm.R','lowerarm_r':'DEF-forearm.R'})
 mapping={n:s for n,s in mapping.items() if n in rig.pose.bones and s in src.pose.bones}
 sc.frame_set(int(ha.frame_range[0]));bpy.context.view_layer.update();reference={s:src.pose.bones[s].rotation_quaternion.copy() for s in mapping.values()}
 human_samples=[]
 for i in range(len(poses)):
  t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1)
  f=ha.frame_range[0]+t*(ha.frame_range[1]-ha.frame_range[0]);sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();deltas={}
  for n,s in mapping.items():
   delta=reference[s].inverted() @ src.pose.bones[s].matrix_basis.to_quaternion()
   # Conjugate into destination bone rest axes, accounting for bone roll.
   basis=rig.data.bones[n].matrix_local.to_quaternion().inverted() @ src.data.bones[s].matrix_local.to_quaternion()
   weight=.16 if clip in ('idle','move','attack') else .55
   deltas[n]=Quaternion().slerp(basis @ delta @ basis.inverted(),weight)
  human_samples.append(deltas)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 hrig.animation_data_clear();rig.animation_data_clear();root.animation_data_clear()
 string=bpy.data.objects['GEO-drawn bowstring'];arrow=bpy.data.objects['GEO-nocked arrow'];tip=bpy.data.objects['GEO-arrow iron point']
 arrow_rest={o.name:o.matrix_basis.copy() for o in [arrow,tip]}
 if clip=='attack':
  string.shape_key_add(name='Basis');relax=string.shape_key_add(name='Release string')
  sc.frame_set(sc['rest_frame']);bpy.context.view_layer.update()
  viewright=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0))
  # Relax the drawn string toward its straight tip-to-tip line; real mesh morph.
  vals=[(string.matrix_world @ v.co).dot(viewright) for v in string.data.vertices];lo,hi=min(vals),max(vals)
  local=string.matrix_world.to_3x3().inverted() @ (-viewright*(hi-lo))
  for v,k,value in zip(string.data.vertices,relax.data,vals):k.co=v.co+local*max(0,(value-lo)/max(.001,hi-lo))

 for i,((pose,obmat),deltas) in enumerate(zip(poses,human_samples)):
  f=i+1;t=i/count if loop else min(i/(count-2 if clip=='death' else count-1),1);sc.frame_set(f)
  hrig.matrix_basis=obmat;hrig.rotation_mode='QUATERNION'
  for p in hrig.pose.bones:
   p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=f)
  for p in rig.pose.bones:
   p.matrix_basis=seat[p.name];p.rotation_mode='QUATERNION'
   if p.name in deltas:p.rotation_quaternion=p.rotation_quaternion @ deltas[p.name]
  bpy.context.view_layer.update()
  # Only the archery release/recovery is authored. Native gallop drives the mount.
  if clip=='attack':
   release=math.sin(math.pi*t)**2
   hand=rig.pose.bones['hand_r'].head.copy();elbow=rig.pose.bones['lowerarm_r'].head.copy()
   limb('upperarm_r','lowerarm_r',hand+Vector((0,-.10,.02))*release,elbow)
   shot=max(0,min(1,(t-.32)/.12));reset=max(0,min(1,(t-.75)/.25));relax.value=shot*(1-reset);relax.keyframe_insert('value',frame=f)
   for obj in [arrow,tip]:
    obj.hide_render=.48<t<.88;obj.keyframe_insert('hide_render',frame=f)

  root.location=base_root.copy();root.scale=base_scale.copy();bpy.context.view_layer.update()
  horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
  if clip=='death':
   factor=min(t/.5,1);root.location.x-=(min(v.x for v in vs)+max(v.x for v in vs))*.5*factor
   root.location.y-=(min(v.y for v in vs)+max(v.y for v in vs))*.5*factor
   root.location.z+=floor_height-min(v.z for v in vs)
  else:root.location.z+=max(0,floor_height-min(v.z for v in vs))
  # Keep the original stride in-place inside the fixed painted composition.
  # Whole-assembly framing correction never changes individual foot rotations.
  from bpy_extras.object_utils import world_to_camera_view
  bpy.context.view_layer.update()
  xx=[]
  for obj in sc.objects:
   if obj.type!='MESH' or obj.hide_render or obj.name=='Stationary cream stone':continue
   eo=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());em=eo.to_mesh()
   xx.extend(world_to_camera_view(sc,sc.camera,eo.matrix_world @ v.co).x*256 for v in em.vertices)
   eo.to_mesh_clear()
  # The registered tail and fully extended stride can exceed the canvas.
  # Preserve all geometry with a modest uniform assembly fit, never crop it.
  lo,hi=min(xx),max(xx);factor=min(1.,240/max(1.,hi-lo))
  assert factor>.85,('Motion envelope needs a new pose',clip,i,factor)
  if factor<1:
   pivot=world_to_camera_view(sc,sc.camera,root.matrix_world.translation).x*256
   lo=pivot+(lo-pivot)*factor;hi=pivot+(hi-pivot)*factor
   root.scale=base_scale*factor
  dx=max(0,8-lo)+min(0,248-hi)
  right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0))
  root.location+=right*(dx*sc.camera.data.ortho_scale/256)
  bpy.context.view_layer.update()
  ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  lowest=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
  root.location.z+=max(0,floor_height-lowest)
  if clip=='death':
   # The fallen rider and separately skinned hair have different armature
   # spaces. Re-evaluate after scaling; an analytic projected box is insufficient.
   for correction in range(3):
    bpy.context.view_layer.update();xx=[]
    for obj in sc.objects:
     if obj.type!='MESH' or obj.hide_render or obj.name=='Stationary cream stone':continue
     eo=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());em=eo.to_mesh()
     xx.extend(world_to_camera_view(sc,sc.camera,eo.matrix_world @ v.co).x*256 for v in em.vertices);eo.to_mesh_clear()
    lo,hi=min(xx),max(xx)
    if lo>=10 and hi<=246:break
    fit=min(1.,232/max(1.,hi-lo));root.scale*=fit;factor*=fit
    assert factor>.85,('Death envelope needs a new pose',i,factor)
    root.location+=right*((128-(lo+hi)/2)*sc.camera.data.ortho_scale/256)
   bpy.context.view_layer.update();ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   lowest=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear();root.location.z+=floor_height-lowest
  root.keyframe_insert('location',frame=f);root.keyframe_insert('scale',frame=f)
  sc[f'composition_scale_{i}']=factor
  for p in rig.pose.bones:
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['clip']=clip;sc['loop']=loop;sc['horse_source_action']=action;sc['rider_source_action']=human
 sc['source_master_sha256']=hashlib.sha256((M/'keshig.blend').read_bytes()).hexdigest();sc['sample_frames']=json.dumps(list(range(1,count+1)))
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('KESHIG_CLIP',clip,action,human)

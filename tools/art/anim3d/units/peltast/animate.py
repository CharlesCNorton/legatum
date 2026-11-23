"""Open CC0 motion with a weapon-specific throw and equipment release layer."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import retarget
source=M/'peltast.blend';(M/'clips').mkdir(exist_ok=True)
def rotate(rig,name,angle,axis):
 p=rig.pose.bones[name];mat=p.matrix.copy();head=p.head.copy();p.matrix=Matrix.Translation(head)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-head)@mat;bpy.context.view_layer.update()
def cloth_ground(rig, frame):
 for name in ('GEO-Blue wind folded cloak','GEO-Pleated linen skirt'):
  obj=bpy.data.objects[name]
  if obj.data.shape_keys is None:obj.shape_key_add(name='Basis')
  states=[(m,m.show_viewport) for m in obj.modifiers if m.type!='ARMATURE']
  for m,_ in states:m.show_viewport=False
  bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
  for m,state in states:m.show_viewport=state
  key=obj.shape_key_add(name=f'Ground contact {frame:02d}')
  for vertex,world in zip(obj.data.vertices,points):
   if world.z>=.228:continue
   weights={obj.vertex_groups[g.group].name:g.weight for g in vertex.groups if obj.vertex_groups[g.group].name in rig.pose.bones}
   total=sum(weights.values())
   if not total:continue
   deform=Matrix([[sum(w/total*(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted())[r][c] for n,w in weights.items()) for c in range(4)] for r in range(4)])
   delta=(obj.matrix_world@deform).to_3x3().inverted()@Vector((0,0,.228-world.z))
   key.data[vertex.index].co+=delta
  key.value=0;key.keyframe_insert('value',frame=max(0,frame-1))
  key.value=1;key.keyframe_insert('value',frame=frame)
  key.value=0;key.keyframe_insert('value',frame=frame+1)
  bpy.context.view_layer.update()
def keyed(o,f):
 o.rotation_mode='QUATERNION'
 for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=f)
for clip,(n,fps,loop) in CLIPS.items():
 if os.environ.get('ONLY_CLIP') and clip!=os.environ['ONLY_CLIP']:continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast'];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
 # The rig object carries the death fall. Every skinned garment must inherit it.
 for obj in sc.objects:
  if obj.parent is None and any(mod.type=='ARMATURE' and mod.object==rig for mod in obj.modifiers):
   world=obj.matrix_world.copy();obj.parent=rig;obj.matrix_parent_inverse=rig.matrix_world.inverted();obj.matrix_basis=world
 bpy.context.view_layer.update();rest={p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for p in rig.pose.bones}
 controls={name:bpy.data.objects[name] for name in ['CTRL-Pelta','CTRL-Throwing javelin']};worlds={k:o.matrix_world.copy() for k,o in controls.items()};bones={'CTRL-Pelta':'hand_l','CTRL-Throwing javelin':'hand_r'};restbones={k:rig.pose.bones[bones[k]].matrix.copy() for k in controls}
 for name,o in controls.items():o.parent=None;o.matrix_world=worlds[name]
 cloth=bpy.data.objects['GEO-Blue wind folded cloak'].data.shape_keys.key_blocks['Trailing breeze']
 motion=None;motion_info=None
 if clip in retarget.ACTIONS:
  phases=[i/n if loop else min(i/(n-2),1) if clip=='death' else i/(n-1) for i in range(n+1 if loop else n)]
  motion,motion_info=retarget.prepare(rig,ROOT,clip,phases)
  motion_info['baked_foot_rotations']=[]
 for i in range(n+1 if loop else n):
  f=i+1;sc.frame_set(f);rig.matrix_world=Matrix.Identity(4)
  for p in rig.pose.bones:
   p.location,p.rotation_quaternion,p.scale=rest[p.name]
  bpy.context.view_layer.update();phase=2*pi*i/n;t=i/(n-1)
  cloth.value=.12*sin(phase)
  if motion is not None:
   retarget.apply_matrices(rig,motion[i]['matrices'])
   motion_info['baked_foot_rotations'].append({side:list(rig.pose.bones['foot_'+side].matrix.to_quaternion()) for side in ('l','r')})
   rig.location=motion[i]['root']
   cloth.value=(.22 if clip=='idle' else .48)*sin(phase-.4)
   if clip=='death':cloth.value=.3*sin(pi*min(i/(n-2),1))
  elif clip=='attack' and i not in (0,n-1):
   # Windup, forward acceleration, release, follow-through, recovered guard.
   xs=[66,61,59,77,107,145,158,134,91,66];ys=[47,49,51,44,44,59,78,72,53,47]
   target=P(xs[i],ys[i],-.075-.10*sin(pi*t));elbow=P(62+(xs[i]-66)*.6,76+12*sin(pi*t),-.07)
   bone_line(rig,'upperarm_r',rig.pose.bones['upperarm_r'].head,elbow);bone_line(rig,'lowerarm_r',elbow,target);bone_line(rig,'hand_r',target,target+Vector((.02,-.015,.03)))
   rotate(rig,'spine_03',-.06*sin(pi*t),'Y');cloth.value=.60*sin(pi*t)
  bpy.context.view_layer.update()
  if clip in ('move','death'):
   # Keep the lower boot on the stone; preserve every source foot rotation.
   deps=bpy.context.evaluated_depsgraph_get();lowest=100
   grounded=['GEO-Laced ankle boot '+side for side in ('l','r')]
   if clip=='death':grounded.append('GEO-MPFB peltast anatomy')
   for name in grounded:
    boot=bpy.data.objects[name].evaluated_get(deps);me=boot.to_mesh()
    lowest=min(lowest,min((boot.matrix_world@v.co).z for v in me.vertices));boot.to_mesh_clear()
   rig.location.z+=.222-lowest;bpy.context.view_layer.update()
   if clip=='death':
    cloth_ground(rig,f)
  for name,o in controls.items():
   mat=rig.matrix_world@rig.pose.bones[bones[name]].matrix@restbones[name].inverted()@worlds[name]
   if clip=='attack' and i not in (0,n-1) and name=='CTRL-Throwing javelin':
    grip=P(xs[i]+2,ys[i]-4,-.11);mat=Matrix.Translation(grip)@Matrix.Rotation([0,-.08,-.16,.22,.65,.75,.75,.4,.15,0][i],4,'Z')@Matrix.Translation(-worlds[name].translation)@worlds[name]
    hidden=5<=i<=7
   else:hidden=False
   if clip=='death' and i>=3:
    u=min((i-3)/5,1);u=u*u*(3-2*u)
    # Release equipment into separate rigid transforms; terminal frames identical.
    if name=='CTRL-Throwing javelin':
     dest=Matrix.Translation(Vector((-.52,-.32,.30)))@Matrix.Rotation(.18,4,'Z')@Matrix.Rotation(.10,4,'Y')@Matrix.Translation(-worlds[name].translation)@worlds[name]
    else:
     dest=Matrix.Translation(Vector((.33,.28,.28)))@Matrix.Rotation(-pi/2,4,'X')@Matrix.Translation(-worlds[name].translation)@worlds[name]
    if i==3:o['release_matrix']=json.dumps([list(row) for row in mat])
    origin=Matrix(json.loads(o['release_matrix']));loc=origin.translation.lerp(dest.translation,u);rot=origin.to_quaternion().slerp(dest.to_quaternion(),u);scale=origin.to_scale().lerp(dest.to_scale(),u);mat=Matrix.LocRotScale(loc,rot,scale)
   o.matrix_world=mat;keyed(o,f)
   for child in o.children:
    child.hide_render=hidden;child.hide_viewport=hidden;child.keyframe_insert('hide_render',frame=f);child.keyframe_insert('hide_viewport',frame=f)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  keyed(rig,f);cloth.keyframe_insert('value',frame=f)
 if clip=='move':
  # Contact correction uses the evaluated baked rig, where nonuniform painting
  # bone scales may add small TRS decomposition error to the constraint sample.
  speed=motion_info['contact']['virtual_ground_m_per_sample'];samples=[]
  for j in range(n+1):
   sc.frame_set(j+1);bpy.context.view_layer.update()
   samples.append({'root':rig.location.copy(),'toes':{side:rig.matrix_world@rig.pose.bones['ball_'+side].head for side in ('l','r')}})
  maximum=0
  for side,start,end in [('l',1,4),('r',5,8)]:
   anchor=samples[start]['toes'][side]
   for j in range(start,end+1):
    actual=samples[j]['toes'][side];desired=anchor+Vector((0,speed*(j-start),0))
    delta=desired-actual;delta.z=0;maximum=max(maximum,delta.length)
    sc.frame_set(j+1);rig.location=samples[j]['root']+delta;rig.keyframe_insert('location',frame=j+1)
    for control in controls.values():
     control.location+=delta;control.keyframe_insert('location',frame=j+1)
  sc.frame_set(n+1);end_root=rig.location.copy();end_controls={name:o.location.copy() for name,o in controls.items()}
  sc.frame_set(1);rig.location=end_root;rig.keyframe_insert('location',frame=1)
  for name,o in controls.items():o.location=end_controls[name];o.keyframe_insert('location',frame=1)
  assert maximum<.04,('Baked contact correction too large',maximum)
  motion_info['contact']['baked_root_correction_m']=maximum
 for action in bpy.data.actions:
  if hasattr(action,'fcurves'):curves=action.fcurves
  else:curves=[fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for k in fc.keyframe_points:
    k.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
 sc['motion_provenance']=json.dumps(motion_info) if motion_info else 'Original weapon-specific authored attack';
 if motion_info:(M/'clips'/f'{clip}-motion.json').write_text(json.dumps(motion_info,indent=2))
 sc['clip']=clip;sc['frames']=n;sc['loop']=loop;sc['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();sc.frame_set(1);save('clips/'+clip+'.blend');(M/'clips'/f'{clip}.json').write_text(json.dumps({'source_sha256':sc['source_sha256'],'frames':n,'fps':fps,'loop':loop},indent=2))
log('- Quaternius CC0 idle/walk/hit/death plus authored weapon-specific attack on MPFB rig: 8/8/10/4/10 samples; rest/roll-calibrated source motion, thrown-javelin visibility, hit recovery, independent equipment release and held death. Cloth uses authored secondary deformation, not a cloth simulation.')

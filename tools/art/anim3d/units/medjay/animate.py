"""Open CC0 motion retarget plus a weapon-specific attack and equipment release."""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
import retarget
def keep_above_disc(control):
 bpy.context.view_layer.update()
 points=[];deps=bpy.context.evaluated_depsgraph_get()
 for o in control.children_recursive:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();points.extend(ev.matrix_world @ v.co for v in mesh.vertices);ev.to_mesh_clear()
 if points:
  low=min(v.z for v in points)
  if low<.095:control.location.z+=.095-low
 bpy.context.view_layer.update()
source=M/'medjay.blend';source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and clip!=os.environ['CLIP']:continue
 (M/f'{clip}.json').unlink(missing_ok=True);bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Medjay MPFB game_engine'];rest={n:Matrix(v) for n,v in json.loads(rig['neutral_pose']).items()};loc=Vector(rig['neutral_location']);rig.rotation_mode='XYZ';sc.render.fps=fps
 def reset():
  rig.location=loc;rig.rotation_euler=(0,0,0)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name];p.rotation_mode='QUATERNION'
  bpy.context.view_layer.update()
 def rot(name,axis,angle):
  p=rig.pose.bones[name];p.rotation_quaternion=rest[name].to_quaternion() @ Quaternion(Vector(axis),angle)
 reset();spear=bpy.data.objects['Spear control'];bpy.context.view_layer.update();spear_offset=(rig.matrix_world @ rig.pose.bones['hand_r'].matrix).inverted() @ spear.matrix_world
 if clip=='death':
  world=spear.matrix_world.copy();spear.parent=None;spear.matrix_world=world;spear.rotation_mode='QUATERNION'
 shield=bpy.data.objects['Shield control'];bpy.context.view_layer.update();shield_offset=(rig.matrix_world @ rig.pose.bones['lowerarm_l'].matrix).inverted() @ shield.matrix_world
 if clip=='death':
  world=shield.matrix_world.copy();shield.parent=None;shield.matrix_world=world;shield.rotation_mode='QUATERNION'
 release=None;shield_release=None
 samples=None;motion='Original weapon-specific attack'
 if clip in retarget.ACTIONS:
  phases=([i/count for i in range(count+1)] if loop else [0,.32,.68,1] if clip=='hit' else [0,.09,.23,.39,.56,.73,.9,1,1,1])
  samples,motion=retarget.prepare(rig,ROOT,clip,phases)
 reset()
 reset();feet={s:rig.pose.bones['calf_'+s].tail.copy() for s in ['l','r']};hand={s:rig.pose.bones['hand_'+s].head.copy() for s in ['l','r']}
 for i in range(count+1 if loop else count):
  reset();phase=2*pi*i/count;t=i/max(1,count-1)
  if samples:
   retarget.apply_matrices(rig,samples[i]['matrices']);rig.location=loc+samples[i]['root']
   bpy.context.view_layer.update()
   # Vertical support corrects mesh fit only; source foot rotations are untouched.
   body=bpy.data.objects['Medjay MPFB anatomical body'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   low=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
   rig.location.z+=.09-low
  elif clip=='attack':
   # Anticipation, controlled lateral jab in screen space, then guard recovery.
   thrust=[0,-.12,-.20,.12,.40,.48,.35,.15,.04,0][i];rig.location.x+=thrust*.16;rig.location.z-=max(0,thrust)*.05
   target=hand['r']+Vector((-thrust*.32,-thrust*.36,thrust*.08));limb(rig,'upperarm_r','lowerarm_r',target,Vector((-.33,-.05,1.11)).lerp(Vector((-.52,-.08,1.10)),min(1,abs(thrust)*2)));rot('hand_r',(0,0,1),thrust*.55);rot('spine_03',(0,0,1),-thrust*.20)
   # Legs stay planted while the front knee accepts the weight shift.
   for s in ['l','r']:limb(rig,'thigh_'+s,'calf_'+s,feet[s]-Vector((thrust*.16,0,-max(0,thrust)*.05)),(feet[s].x,-.4,.50))
  if (i==0 and clip in {'attack','hit','death'}) or (clip=='attack' and i==count-1):reset()
  bpy.context.view_layer.update()
  if clip=='death':
   held=rig.matrix_world @ rig.pose.bones['hand_r'].matrix @ spear_offset
   if i<3:
    spear.matrix_world=held;release=held.copy()
   else:
    u=min(1,(i-2)/4);ease=1-(1-u)**2
    final_rot=Vector((-.235,0,.972)).rotation_difference(Vector((1,0,0)))
    spear.location=release.translation.lerp(Vector((.28,-.31,.12)),ease)
    spear.location.z+=.14*sin(pi*u)
    spear.rotation_quaternion=release.to_quaternion().slerp(final_rot,ease)
   if i>=3:keep_above_disc(spear)
   spear.keyframe_insert('location',frame=i+1);spear.keyframe_insert('rotation_quaternion',frame=i+1)
   held=rig.matrix_world @ rig.pose.bones['lowerarm_l'].matrix @ shield_offset
   if i<3:
    shield.matrix_world=held;shield_release=held.copy()
   else:
    u=min(1,(i-2)/4);ease=1-(1-u)**2
    shield.location=shield_release.translation.lerp(Vector((.12,.20,.18)),ease)
    shield.rotation_quaternion=shield_release.to_quaternion().slerp(Quaternion(Vector((1,0,0)),pi/2),ease)
   if i>=3:keep_above_disc(shield)
   shield.keyframe_insert('location',frame=i+1);shield.keyframe_insert('rotation_quaternion',frame=i+1)
  for p in rig.pose.bones:
   p.keyframe_insert('location',frame=i+1);p.keyframe_insert('rotation_quaternion',frame=i+1);p.keyframe_insert('scale',frame=i+1)
  rig.keyframe_insert('location',frame=i+1);rig.keyframe_insert('rotation_euler',frame=i+1)
 # Blender 5 layered actions: clamp handles to avoid extra-frame overshoot.
 action=rig.animation_data.action;action.name='Medjay '+clip
 for layer in action.layers:
  for strip in layer.strips:
   for bag in getattr(strip,'channelbags',[]):
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
 sc.frame_start=1;sc.frame_end=count;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/f'medjay-{clip}.blend'))
 (M/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'master_sha256':source_sha,'motion':motion,'held_death':clip=='death'},indent=2));log(f'Saved {clip}: {count} frames at {fps} fps; saved editable rig action and equipment attachments.')

(M/'animation-inputs.json').write_text(json.dumps({name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ['animate.py','retarget.py']},indent=2))

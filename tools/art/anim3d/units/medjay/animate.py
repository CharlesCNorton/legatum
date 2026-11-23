"""Five authored skeletal clips with equipment attached to real hands/forearm."""
import sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
def keep_above_disc(control):
 bpy.context.view_layer.update()
 points=[];deps=bpy.context.evaluated_depsgraph_get()
 for o in control.children_recursive:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();points.extend(ev.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
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
  p=rig.pose.bones[name];p.rotation_quaternion=rest[name].to_quaternion()@Quaternion(Vector(axis),angle)
 reset();spear=bpy.data.objects['Spear control'];bpy.context.view_layer.update();spear_offset=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).inverted()@spear.matrix_world
 if clip=='death':
  world=spear.matrix_world.copy();spear.parent=None;spear.matrix_world=world;spear.rotation_mode='QUATERNION'
 shield=bpy.data.objects['Shield control'];bpy.context.view_layer.update();shield_offset=(rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix).inverted()@shield.matrix_world
 if clip=='death':
  world=shield.matrix_world.copy();shield.parent=None;shield.matrix_world=world;shield.rotation_mode='QUATERNION'
 release=None;shield_release=None
 reset();feet={s:rig.pose.bones['calf_'+s].tail.copy() for s in ['l','r']};hand={s:rig.pose.bones['hand_'+s].head.copy() for s in ['l','r']}
 for i in range(count+1 if loop else count):
  reset();phase=2*pi*i/count;t=i/max(1,count-1)
  if clip=='idle':
   rot('spine_02',(1,0,0),.012*sin(phase));rot('spine_03',(0,0,1),.010*sin(phase));rot('head',(0,1,0),.022*sin(phase));rot('lowerarm_r',(1,0,0),.016*sin(phase))
  elif clip=='move':
   rig.location.z+=.018*(1-cos(phase*2));rig.location.x+=.015*sin(phase)
   for s,offset in [('r',0),('l',pi)]:
    p=phase+offset;target=feet[s]+Vector((0,.17*cos(p),.075*max(0,sin(p))));limb(rig,'thigh_'+s,'calf_'+s,target,(target.x,-.45,.48))
   rot('spine_02',(0,0,1),.035*sin(phase));rot('lowerarm_r',(1,0,0),.035*sin(phase));rot('head',(1,0,0),-.012*cos(phase*2))
  elif clip=='attack':
   # Anticipation, controlled lateral jab in screen space, then guard recovery.
   thrust=[0,-.12,-.20,.12,.40,.48,.35,.15,.04,0][i];rig.location.x+=thrust*.16;rig.location.z-=max(0,thrust)*.05
   target=hand['r']+Vector((-thrust*.32,-thrust*.36,thrust*.08));limb(rig,'upperarm_r','lowerarm_r',target,(-.52,-.08,1.10));rot('hand_r',(0,0,1),thrust*.55);rot('spine_03',(0,0,1),-thrust*.20)
   # Legs stay planted while the front knee accepts the weight shift.
   for s in ['l','r']:limb(rig,'thigh_'+s,'calf_'+s,feet[s]-Vector((thrust*.16,0,-max(0,thrust)*.05)),(feet[s].x,-.4,.50))
  elif clip=='hit':
   recoil=[0,1,.40,0][i];rot('spine_02',(1,0,0),-.16*recoil);rot('spine_03',(0,0,1),.10*recoil);rot('head',(1,0,0),-.12*recoil);rot('upperarm_l',(0,0,1),-.10*recoil)
  elif clip=='death':
   # Collapse onto the disc; last two samples are exactly the same settled pose.
   fall=[0,.03,.14,.35,.60,.79,.94,1,1,1][i];bend=min(1,fall*2.4);rot('thigh_r',(1,0,0),-.80*bend);rot('calf_r',(1,0,0),1.15*bend);rot('thigh_l',(1,0,0),-.55*bend);rot('calf_l',(1,0,0),1.05*bend);rot('spine_02',(0,0,1),.18*fall)
   rig.rotation_euler.y=-1.54*fall;rig.rotation_euler.z=.30*fall;rig.location=loc+Vector((.87*fall,.03*fall,.145*fall));rot('head',(0,0,1),.20*fall)
   bpy.context.view_layer.update();inv=rig.matrix_world.inverted()
   # World-space IK curls both legs onto the disc instead of kicking upward.
   for side,foot_end in [('r',(.35,-.04,.15)),('l',(.49,.13,.16))]:
    live=rig.matrix_world@rig.pose.bones['calf_'+side].tail
    target=live.lerp(Vector(foot_end),fall)
    limb(rig,'thigh_'+side,'calf_'+side,inv@target,inv@Vector((.50,.40,.48)))
    if fall>.8:aim(rig,'foot_'+side,inv.to_3x3()@Vector((.05,-.15,-.02)))
   for side,end,pole in [('r',(-.45,-.22,.14),(-.55,-.31,.35)),('l',(-.15,.14,.25),(-.18,.36,.45))]:
    live=rig.matrix_world@rig.pose.bones['hand_'+side].head
    limb(rig,'upperarm_'+side,'lowerarm_'+side,inv@live.lerp(Vector(end),fall),inv@Vector(pole))
  bpy.context.view_layer.update()
  if clip=='death':
   held=rig.matrix_world@rig.pose.bones['hand_r'].matrix@spear_offset
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
   held=rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix@shield_offset
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
 (M/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'master_sha256':source_sha,'motion':'Original authored MPFB skeletal keys; not mocap','held_death':clip=='death'},indent=2));log(f'Authored {clip}: {count} frames at {fps} fps; saved editable rig action and equipment attachments.')

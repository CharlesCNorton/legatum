"""CC0 retargeted clips and a weapon-specific attack on the MPFB skeleton; no pose-image warping.

Each master is independent, with explicit samples and a held terminal death.
All motion is keyed on skeletal or equipment transforms. Cloth is folded and
bone-attached in round 1, not claimed as a simulated cloth solve.
"""
import bpy, json, math, os, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from retarget import prepare, apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier';source=M/'tagmatic-soldier.blend'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('ANIMATE_CLIP') and clip!=os.environ['ANIMATE_CLIP']:continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Tagmatic MPFB'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy()
 out=M/'clips';out.mkdir(exist_ok=True);(out/f'{clip}.json').unlink(missing_ok=True)
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
 hands={s:rig.pose.bones['hand_'+s].matrix.copy() for s in ['r','l']}
 ankles={s:rig.matrix_world@rig.pose.bones['calf_'+s].tail for s in ['r','l']}
 elbows={s:rig.matrix_world@rig.pose.bones['lowerarm_'+s].head for s in ['r','l']}
 knees={s:rig.matrix_world@rig.pose.bones['calf_'+s].head for s in ['r','l']}
 wrists={s:rig.matrix_world@rig.pose.bones['lowerarm_'+s].tail for s in ['r','l']}
 spear=[o for o in sc.objects if o.name.startswith(('GEO-overhand ash','GEO-iron spear socket','GEO-forged iron spear'))]
 shieldprops=[o for o in sc.objects if o.name.startswith(('GEO-convex wooden kite','GEO-kite shield','GEO-shield brass','GEO-vertical cross','GEO-horizontal cross','GEO-shield boss','GEO-shield back'))]
 rigidfloor=[o for o in sc.objects if o.name.startswith(('GEO-lamellar skirt panel','GEO-leather scabbard','GEO-sword brass throat'))]
 props=spear+shieldprops+rigidfloor
 clothfloor=[o for o in sc.objects if o.name.startswith(('GEO-folded red tunic skirt','GEO-tunic gold embroidered hem'))]
 prop_basis={o.name:o.matrix_basis.copy() for o in props};prop_world={o.name:o.matrix_world.copy() for o in props}
 for o in props:o.rotation_mode='QUATERNION'
 phases=[i/count if loop else min(1,i/(count-2 if clip=='death' else count-1)) for i in range(count+int(loop))]
 if clip=='hit':phases=[0,.25,.60,0]  # sourced impact, then the sampled guard for recovery
 captured,provenance=prepare(rig,R,clip,phases) if clip!='attack' else (None,{'method':'original weapon-specific attack'})
 def reset():
  rig.location=base;rig.rotation_euler=(0,0,0)
  for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
  for o in props:o.matrix_basis=prop_basis[o.name]
  bpy.context.view_layer.update()
 def aim(name,direction):
  p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized());m=(delta@q).to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
 def turn(name,axis,a):
  p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(a,4,axis)@m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
 def limb(u,l,world,pole):
  inv=rig.matrix_world.inverted();target=inv@Vector(world);pole=inv@Vector(pole);a=rig.pose.bones[u].head.copy();v=target-a;d=min(v.length,rig.data.bones[u].length+rig.data.bones[l].length-.0001);v.normalize();l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;along=(l1*l1-l2*l2+d*d)/(2*d);side=pole-a;side=(side-v*side.dot(v)).normalized();elbow=a+v*along+side*max(0,l1*l1-along*along)**.5;aim(u,elbow-a);aim(l,target-elbow)
 def hold_hand(s,angle=0):
  p=rig.pose.bones['hand_'+s];m=hands[s].copy();m=Matrix.Rotation(angle,4,'Y')@m;m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
 def pose(i):
  reset();t=i/count if loop else i/(count-1)
  if captured:
   apply_matrices(rig,captured[i]['matrices']);rig.location=base+captured[i]['root'];bpy.context.view_layer.update()
  if clip=='move':
   # Weapon-bearing arm clearance; captured legs and feet remain untouched.
   wrist=rig.matrix_world@rig.pose.bones['lowerarm_r'].tail
   hand=rig.pose.bones['hand_r'].matrix.copy()
   pole=rig.matrix_world@rig.pose.bones['lowerarm_r'].head
   limb('upperarm_r','lowerarm_r',wrist-Vector((0,0,.14)),pole-Vector((0,0,.10)))
   hand.translation=rig.pose.bones['hand_r'].head;rig.pose.bones['hand_r'].matrix=hand;bpy.context.view_layer.update()
  if clip=='attack':
   power=[0,-.12,-.25,.15,.8,1,.80,.35,.06,0][i];rig.location=base+Vector((.045*power,-.018*power,-.025*max(0,power)));turn('spine_03','Y',.07*power)
   for s in ['r','l']:
    limb('thigh_'+s,'calf_'+s,ankles[s],knees[s]);aim('foot_'+s,(0,-1,-.12));aim('ball_'+s,(0,-1,0))
   limb('upperarm_r','lowerarm_r',wrists['r']+Vector((.25*power,-.20*power,-.14*power)),elbows['r']+Vector((.06*power,-.08*power,-.04*power)));hold_hand('r',.22*power)
   limb('upperarm_l','lowerarm_l',wrists['l']+Vector((.015*power,-.035*power,.012*power)),elbows['l']);hold_hand('l')
  bpy.context.view_layer.update()
  if captured:
   # Vertical root contact on the evaluated soles/body; preserve all source rolls.
   ground_objects=[o for o in sc.objects if o.type=='MESH' and o.parent==rig and o not in props and o not in clothfloor]
   if clip!='death':ground_objects=[o for o in ground_objects if o.name.startswith(('GEO-closed leather shoe','GEO-stitched boot sole'))]
   dg=bpy.context.evaluated_depsgraph_get();low=99
   for o in ground_objects:
    ev=o.evaluated_get(dg);me=ev.to_mesh();low=min(low,min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   rig.location.z+=.178-low
   bpy.context.view_layer.update()
  if clip=='death':
   # Free-fall from the last held world pose, accelerating to the stone.
   # Apply after root contact so released equipment never follows root corrections.
   # Carry through the initial loss of balance, then release from that actual
   # hand pose. Previously props detached at frame one and hovered for 0.6 s.
   for group,release,land,pivot,target,angle,axis in [
    (spear,2,5,Vector((-.1,-.15,2.03)),Vector((-.10,-.40,.29)),-.33,'Y'),
    (shieldprops,3,5,Vector((.10,-.45,1.05)),Vector((.02,-.28,.25)),-1.20,'X')]:
    if i<=release:release_world.update({o.name:o.matrix_world.copy() for o in group})
    else:
     d=min(1,((i-release)/(land-release))**2)
     release_delta=release_world[group[0].name]@prop_world[group[0].name].inverted()
     center=(release_delta@pivot).lerp(target,d)
     rotation=release_delta.to_quaternion().slerp(Matrix.Rotation(angle,4,axis).to_quaternion(),min(1,(i-release)/(land-release)))
     delta=Matrix.Translation(center)@rotation.to_matrix().to_4x4()@Matrix.Translation(-pivot)
     for o in group:o.matrix_world=delta@prop_world[o.name]
   bpy.context.view_layer.update()
   for group in [spear,shieldprops]:
    low=min((o.matrix_world@v.co).z for o in group for v in o.data.vertices)
    if low<.178:
     for o in group:
      m=o.matrix_world.copy();m.translation.z+=.178-low;o.matrix_world=m
   for o in rigidfloor:
    low=min((o.matrix_world@Vector(v)).z for v in o.bound_box)
    if low<.19:
     m=o.matrix_world.copy();m.translation.z+=.19-low;o.matrix_world=m
   bpy.context.view_layer.update()
 release_world={}
 samples=[]
 for i in range(count+(1 if loop else 0)):
  frame=i+1;sc.frame_set(frame);pose(i)
  if clip=='death':
   # Authored geometric contact folds; real 3D shape keys, not image deformation.
   for o in clothfloor:
    if o.data.shape_keys is None:o.shape_key_add(name='Basis')
    for key in o.data.shape_keys.key_blocks[1:]:key.value=0
    key=o.shape_key_add(name=f'Stone contact {frame:02}');inv=o.matrix_world.inverted()
    for v,point in zip(o.data.vertices,key.data):
     world=o.matrix_world@v.co
     if world.z<.195:world.z=.195;point.co=inv@world
    key.value=0;key.keyframe_insert('value',frame=1)
    if frame>1:key.keyframe_insert('value',frame=frame-1)
    key.value=1;key.keyframe_insert('value',frame=frame)
    key.value=0;key.keyframe_insert('value',frame=frame+1)
    key.value=1
  for p in rig.pose.bones:
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=frame)
  rig.keyframe_insert('location',frame=frame)
  for o in props:
   for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=frame)
  if i<count:samples.append(frame)
 # Use auto-clamped Bezier easing for organic motion without overshoot.
 for action in bpy.data.actions:
  action.use_fake_user=True
  curves=[fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
 sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc['sample_frames']=json.dumps(samples);sc['clip']=clip;sc['cloth_method']='Modeled folds with bone attachments; no cloth simulation in round 1';sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
 (out/f'{clip}.json').write_text(json.dumps({'clip':clip,'frames':samples,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'motion_source':provenance},indent=2))
 print('CLIP_READY',clip)

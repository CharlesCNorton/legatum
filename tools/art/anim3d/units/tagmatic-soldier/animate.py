"""Five authored clips on the MPFB skeleton; no pose-image warping.

Each master is independent, with explicit samples and a held terminal death.
All motion is keyed on skeletal or equipment transforms. Cloth is folded and
bone-attached in round 1, not claimed as a simulated cloth solve.
"""
import bpy, json, math, os, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier';source=M/'tagmatic-soldier.blend'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
for clip,(count,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Tagmatic MPFB'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy()
 out=M/'clips';out.mkdir(exist_ok=True);(out/f'{clip}.json').unlink(missing_ok=True)
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
 hands={s:rig.pose.bones['hand_'+s].matrix.copy() for s in ['r','l']}
 ankles={s:rig.matrix_world@rig.pose.bones['calf_'+s].tail for s in ['r','l']}
 wrists={s:rig.matrix_world@rig.pose.bones['lowerarm_'+s].tail for s in ['r','l']}
 spear=[o for o in sc.objects if o.name.startswith(('GEO-overhand ash','GEO-iron spear socket','GEO-forged iron spear'))]
 shieldprops=[o for o in sc.objects if o.name.startswith(('GEO-convex wooden kite','GEO-kite shield','GEO-shield brass','GEO-vertical cross','GEO-horizontal cross','GEO-shield boss'))]
 rigidfloor=[o for o in sc.objects if o.name.startswith(('GEO-lamellar skirt panel','GEO-leather scabbard','GEO-sword brass throat'))]
 props=spear+shieldprops+rigidfloor
 clothfloor=[o for o in sc.objects if o.name.startswith(('GEO-folded red tunic skirt','GEO-tunic gold embroidered hem'))]
 prop_basis={o.name:o.matrix_basis.copy() for o in props};prop_world={o.name:o.matrix_world.copy() for o in props}
 for o in props:o.rotation_mode='QUATERNION'
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
  if clip=='idle':
   a=math.sin(2*math.pi*t);turn('spine_03','Y',.012*a);turn('head','Z',.012*a)
   for s in ['r','l']:
    limb('upperarm_'+s,'lowerarm_'+s,wrists[s]+Vector((0,0,.007*a)),wrists[s]+Vector((-.25 if s=='r' else .25,.12,-.2)));hold_hand(s)
  elif clip=='move':
   phase=2*math.pi*t;rig.location=base+Vector((.018*math.sin(phase),0,.012*(1-math.cos(2*phase))))
   turn('spine_03','Z',.025*math.sin(phase));bpy.context.view_layer.update()
   for s,offset in [('r',0),('l',math.pi)]:
    ph=phase+offset;target=ankles[s]+Vector((0,.11*math.cos(ph),.065*max(0,math.sin(ph))));limb('thigh_'+s,'calf_'+s,target,target+Vector((0,-.45,.4)));aim('foot_'+s,(0,-1,-.12));aim('ball_'+s,(0,-1,0))
    limb('upperarm_'+s,'lowerarm_'+s,wrists[s]+Vector((0,.01*math.cos(ph),.010*math.cos(2*phase))),wrists[s]+Vector((-.25 if s=='r' else .25,.12,-.2)));hold_hand(s)
  elif clip=='attack':
   power=[0,-.12,-.25,.15,.8,1,.80,.35,.06,0][i];rig.location=base+Vector((.045*power,-.018*power,-.025*max(0,power)));turn('spine_03','Y',.07*power)
   for s in ['r','l']:
    limb('thigh_'+s,'calf_'+s,ankles[s],ankles[s]+Vector((0,-.4,.4)));aim('foot_'+s,(0,-1,-.12));aim('ball_'+s,(0,-1,0))
   limb('upperarm_r','lowerarm_r',wrists['r']+Vector((.16*power,-.13*power,-.07*power)),wrists['r']+Vector((-.2,.12,-.22)));hold_hand('r',.06*power)
   limb('upperarm_l','lowerarm_l',wrists['l']+Vector((.015*power,-.035*power,.012*power)),wrists['l']+Vector((.2,.1,-.1)));hold_hand('l')
  elif clip=='hit':
   power=[0,1,.45,0][i];turn('spine_03','X',-.15*power);turn('head','X',-.12*power);turn('head','Z',.06*power)
   for s in ['r','l']:
    limb('upperarm_'+s,'lowerarm_'+s,wrists[s]+Vector((-.035*power,.045*power,.03*power)),wrists[s]+Vector((-.2 if s=='r' else .2,.15,-.2)));hold_hand(s,.025*power)
  else:
   # Bend knees, roll onto the rear side of the stone, then hold two samples.
   p=min(1,i/8);ease=p*p*(3-2*p)
   rig.location=base+Vector((.30*ease,.18*ease,-.68*ease));turn('pelvis','Y',-1.35*ease);turn('spine_03','Y',-.15*ease);turn('head','X',.22*ease)
   for s,sg in [('r',-1),('l',1)]:
    target=ankles[s].lerp(Vector((.15+sg*.13,.10+sg*.13,.36)),ease)
    limb('thigh_'+s,'calf_'+s,target,Vector((-.25,-.30,.55)));aim('foot_'+s,(0,-1,-.12));aim('ball_'+s,(0,-1,0))
    target=wrists[s].lerp(Vector((-.40,.03,.60 if s=='r' else .45)),ease)
    limb('upperarm_'+s,'lowerarm_'+s,target,Vector((-.3,.15,.55)));hold_hand(s,-.4*ease)
   # Equipment release: continuous rigid transforms, never hidden/scaled away.
   drop=min(1,max(0,(p-.08)/.67));d=drop*drop*(3-2*drop)
   spearcenter=Vector((-.1,-.15,2.03));target=Vector((-.10,-.40,.29));rot=Matrix.Rotation(-.33*d,4,'Y')
   trans=Matrix.Translation(spearcenter.lerp(target,d))@rot@Matrix.Translation(-spearcenter)
   for o in spear:o.matrix_world=trans@prop_world[o.name]
   shieldcenter=Vector((.10,-.45,1.05));land=Vector((.02,-.28,.25));a=min(1,max(0,(p-.20)/.70));a=a*a*(3-2*a)
   trans=Matrix.Translation(shieldcenter.lerp(land,a))@Matrix.Rotation(1.85*a,4,'X')@Matrix.Translation(-shieldcenter)
   for o in shieldprops:o.matrix_world=trans@prop_world[o.name]
   bpy.context.view_layer.update()
   # Rigid skirt plates and the scabbard settle on the stone without bending.
   for o in rigidfloor:
    low=min((o.matrix_world@Vector(v)).z for v in o.bound_box)
    if low<.19:
     m=o.matrix_world.copy();m.translation.z+=.19-low;o.matrix_world=m
  bpy.context.view_layer.update()
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
 (out/f'{clip}.json').write_text(json.dumps({'clip':clip,'frames':samples,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2))
 print('CLIP_READY',clip)

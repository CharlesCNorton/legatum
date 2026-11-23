"""Five authored MPFB actions, IK-foot placement and keyed cloth follow-through."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/scout';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
clip_sources=json.loads((M/'clip-sources.json').read_text()) if (M/'clip-sources.json').exists() else {}
for clip,(n,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'scout.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Scout MPFB game_engine'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy();cloak=bpy.data.objects['GEO-Wind folded olive cloak'];breeze=cloak.data.shape_keys.key_blocks['Breeze'];staff=[o for o in sc.objects if any(x in o.name for x in ['walking staff','Staff fork','Staff grain'])]
 targets={k:Vector(v) for k,v in json.loads(rig['registered_targets']).items()}
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 def reset():
  rig.location=base
  for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
  bpy.context.view_layer.update()
 def turn(name,axis,a):
  p=rig.pose.bones[name];mat=p.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(a,4,axis)@mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
 def aim(name,d):
  p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q@Vector((0,1,0))).rotation_difference(Vector(d).normalized());mat=(delta@q).to_matrix().to_4x4();mat=mat@Matrix.Diagonal((1,1.17,1,1)) if 'arm_' in name else mat;mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
 def limb(u,l,target,pole):
  a=rig.pose.bones[u].head.copy();v=Vector(target)-a;scale=1.17 if 'arm_' in u else 1;l1=rig.data.bones[u].length*scale;l2=rig.data.bones[l].length*scale;d=min(v.length,l1+l2-.0001);v.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);side=Vector(pole)-a;side=(side-v*side.dot(v)).normalized();joint=a+along*v+max(0,l1*l1-along*along)**.5*side;aim(u,joint-a);aim(l,Vector(target)-joint)
 def pose(t):
  reset();breeze.value=.22+.15*sin(2*pi*t)
  if clip=='idle':
   turn('spine_03','X',.016*sin(2*pi*t));turn('head','Z',.055*sin(2*pi*t));turn('upperarm_l','Y',.025*sin(2*pi*t))
  elif clip=='move':
   phase=2*pi*t;rig.location.z=base.z+.024*(1-cos(2*phase));turn('spine_03','Y',-.12);turn('spine_03','Z',.055*sin(phase))
   for side,sg in [('l',1),('r',-1)]:
    a=phase+(0 if sg==1 else pi);y=.21*cos(a);lift=.14*max(0,sin(a));z=.16+lift-(rig.location.z-base.z)
    limb('thigh_'+side,'calf_'+side,(sg*.21,y,z),(sg*.28,-.42,.55));aim('foot_'+side,(0,-1,-.19))
   limb('upperarm_l','lowerarm_l',(.30,-.18,1.16+.05*sin(phase)),(.42,-.06,1.32));turn('hand_l','X',-.55)
   turn('upperarm_r','Y',.045*sin(phase));breeze.value=.42+.30*sin(phase-.6)
  elif clip=='attack':
   # Anticipation, forward staff shove, recovery; right hand remains fixed to staff.
   a=[0,-.10,-.22,-.12,.40,1,.65,.22,.04,0][min(9,round(t*9))]
   turn('spine_03','Z',-.18*a);turn('spine_03','X',.09*a)
   turn('upperarm_r','Y',-.30*a);turn('lowerarm_r','Z',.18*a);turn('hand_r','Y',.70*a)
   brace=[0,.4,.8,1,1,1,1,.7,.3,0][min(9,round(t*9))];target=targets['hand_l'].lerp(Vector((.37,-.25,1.34)),brace);pole=targets['lowerarm_l'].lerp(Vector((.51,-.04,1.42)),brace);limb('upperarm_l','lowerarm_l',target,pole);aim('hand_l',(-.98,-.12,-.06));breeze.value=.3+.40*max(0,a)
  elif clip=='hit':
   a=[0,1,.45,0][min(3,round(t*3))];turn('spine_03','X',-.10*a);turn('head','Y',-.16*a);turn('upperarm_l','Z',-.20*a);breeze.value=.25+.45*a
  elif clip=='death':
   u=min(1,t/.78);a=u*u*(3-2*u);rig.location=base+Vector((-.03*a,.05*a,-.54*a));turn('pelvis','Y',-1.35*a);turn('spine_03','Y',-.16*a);turn('head','X',.22*a)
   for side,sg in [('l',1),('r',-1)]:
    start=targets['foot_'+side];end=Vector((.30+sg*.10,-.09+sg*.12,.72));target=start.lerp(end,a);limb('thigh_'+side,'calf_'+side,target,targets['calf_'+side].lerp(Vector((.3,-.4,.65)),a))
   limb('upperarm_l','lowerarm_l',targets['hand_l'].lerp(Vector((-.35,-.16,.77)),a),targets['lowerarm_l'].lerp(Vector((-.5,-.15,1.0)),a));limb('upperarm_r','lowerarm_r',targets['hand_r'].lerp(Vector((-.10,-.29,.72)),a),targets['lowerarm_r'].lerp(Vector((-.25,-.3,.9)),a));turn('hand_r','Y',1.30*a);breeze.value=.25*(1-a)
  bpy.context.view_layer.update()
  # Ground each sample from evaluated anatomy; no near-zero scale or hidden geometry.
  body=bpy.data.objects['GEO-Scout MPFB anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();floor=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=.100-floor;bpy.context.view_layer.update()
 sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n+1 if loop else n
 for i in range(n+(1 if loop else 0)):
  frame=i+1;sc.frame_set(frame);t=i/n if loop else min(i,n-2)/(n-2) if clip=='death' else i/(n-1);pose(t)
  if clip=='death':
   # Authored ground-contact corrective shapes retain real cloak thickness.
   # Clamp the cloth/hem to the stone plane rather than hiding or shrinking it.
   for ob in [cloak,bpy.data.objects['GEO-Cloak worn hem']]:
    if ob.data.shape_keys is None:ob.shape_key_add(name='Basis',from_mix=False)
    basis=ob.data.shape_keys.key_blocks['Basis'];key=ob.shape_key_add(name=f'Ground contact {frame:02}',from_mix=False);inv=ob.matrix_world.inverted()
    for j,v in enumerate(key.data):
     co=basis.data[j].co.copy()
     if ob==cloak:co+=(breeze.data[j].co-basis.data[j].co)*breeze.value
     world=ob.matrix_world@co
     if world.z<.108:
      target=world.copy();target.z=.108;v.co=basis.data[j].co+(inv@target-co)
    key.value=0;key.keyframe_insert('value',frame=max(0,frame-1));key.keyframe_insert('value',frame=frame+1)
    key.value=1;key.keyframe_insert('value',frame=frame)
  rig.keyframe_insert('location',frame=frame)
  for p in rig.pose.bones:
   p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
  breeze.keyframe_insert('value',frame=frame)
 if rig.animation_data and rig.animation_data.action:
  action=rig.animation_data.action;action.name='Scout '+clip
  curves=list(action.fcurves) if hasattr(action,'fcurves') else [fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
 sc['samples']=json.dumps(list(range(1,n+1)));sc['clip']=clip;sc['source_sha256']=hashlib.sha256((M/'scout.blend').read_bytes()).hexdigest();sc['loop']=loop;sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/(clip+'.blend')))
 clip_sources[clip]=sc['source_sha256']
 print('SCOUT_CLIP_READY',clip,n,flush=True)

(M/'clip-sources.json').write_text(json.dumps(clip_sources,indent=2))

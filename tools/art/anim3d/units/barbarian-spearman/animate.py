"""Five authored skeletal actions; hand-mounted weapon, weighted anatomy, fixed base."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';source=M/'barbarian-spearman.blend'
shared=Path('tools/art/anim3d/scene.py').read_text()
exec(shared[shared.index('def aim_bone('):shared.index('def camera(')])
clips={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def rotate(name,axis,angle):
 p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion(axis,angle)
def smooth(t):return t*t*(3-2*t)
for clip,(count,fps,loop) in clips.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Barbarian skeleton'];base=bpy.data.objects['Stationary cream base'];base_matrix=base.matrix_world.copy()
 neutral={p.name:p.matrix_basis.copy() for p in rig.pose.bones};root=rig.location.copy();feet={s:rig.pose.bones['foot_'+s].head.copy() for s in ['r','l']}
 foot_rest={side:rig.pose.bones['foot_'+side].matrix.copy() for side in ['r','l']}
 weapon=bpy.data.objects['Spear grip control'];wrest=weapon.matrix_world.copy();wloc=weapon.location.copy()
 hand_pose_rest=rig.pose.bones['hand_r'].matrix.copy()
 hand_rest=(rig.matrix_world@hand_pose_rest).copy()
 shield=bpy.data.objects['Shield grip control'];shield_rest=shield.matrix_world.copy();arm_rest=(rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix).copy()
 if clip=='death':
  weapon.parent=None;weapon.matrix_world=wrest;shield.parent=None;shield.matrix_world=shield_rest
 sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 samples=list(range(1,count+1))
 if clip=='death':samples[-1]=samples[-2]
 for i in range(count+int(loop)):
  sc.frame_set(i+1);t=i/count if loop else min(i/(count-2),1) if clip=='death' else i/(count-1)
  rig.location=root;rig.rotation_euler=(0,0,0)
  for p in rig.pose.bones:p.matrix_basis=neutral[p.name]
  bpy.context.view_layer.update()
  if clip=='idle':
   rotate('spine_03',(1,0,0),.017*sin(2*pi*t));rotate('head',(0,1,0),.025*sin(2*pi*t+.4));rotate('upperarm_r',(0,0,1),.012*sin(2*pi*t))
  elif clip=='move':
   rig.location.z-=.065
   bpy.context.view_layer.update()
   # In-place gait with planted contact half and raised swing half.
   for s,offset in [('r',0),('l',.5)]:
    u=(t+offset)%1;a=2*pi*u;target=feet[s].copy();target.y+=.17*cos(a);target.z+=.07*max(0,sin(a))
    lift=.07*max(0,sin(a))
    for correction in range(6):
     limb('thigh_'+s,'calf_'+s,target,(target.x,-.5,.6))
     foot=rig.pose.bones['foot_'+s];flat=foot_rest[s].copy();flat.translation=foot.head.copy();foot.matrix=flat
     bpy.context.view_layer.update()
     shoe=bpy.data.objects['Lasted leather shoe '+s]
     lowest=min((shoe.matrix_world@v.co).z for v in shoe.data.vertices)
     target.z+=.092+lift-lowest
   rotate('spine_03',(0,1,0),.035*sin(2*pi*t));rotate('head',(0,0,1),.025*sin(2*pi*t))
  elif clip=='attack':
   # Guard -> pull back -> fast thrust -> recover; the weapon follows its palm control.
   pulse=[0,-.15,-.30,.35,1.,.82,.48,.18,.04,0][i]
   rotate('spine_03',(0,1,0),-.08*pulse);bpy.context.view_layer.update()
   target=hand_pose_rest.translation+Vector((.065,-.18,.090))*pulse
   limb('upperarm_r','lowerarm_r',target,(-.55,-.10,1.17))
   hand=rig.pose.bones['hand_r'];hm=hand_pose_rest.copy();hm.translation=hand.head.copy()
   pivot=hm.translation.copy();hand.matrix=Matrix.Translation(pivot)@Matrix.Rotation(-.12*pulse,4,'Y')@Matrix.Translation(-pivot)@hm
   rotate('upperarm_l',(0,1,0),.04*pulse)
   rotate('thigh_r',(1,0,0),.06*pulse);rotate('calf_r',(1,0,0),-.05*pulse)
  elif clip=='hit':
   pulse=[0,1,.48,0][i];rotate('spine_03',(1,0,0),-.18*pulse);rotate('head',(1,0,0),-.12*pulse);rotate('upperarm_l',(0,1,0),-.15*pulse)
  else:
   fall=smooth(max(0,min(1,(t-.12)/.72)))
   rotate('thigh_r',(1,0,0),.72*fall);rotate('calf_r',(1,0,0),-.88*fall);rotate('thigh_l',(1,0,0),.42*fall);rotate('calf_l',(1,0,0),-.65*fall)
   rotate('spine_03',(1,0,0),.20*fall);rotate('head',(0,0,1),.25*fall)
   # Fold both elbows after release so a straight arm cannot prop up the corpse.
   tuck=smooth(max(0,min(1,(t-.32)/.42)))
   if tuck>0:
    for side,sign in [('r',-1),('l',1)]:
     start=rig.pose.bones['hand_'+side].head.copy();target=start.lerp(Vector((sign*.12,-.18,1.25)),tuck)
     limb('upperarm_'+side,'lowerarm_'+side,target,(sign*.40,-.08,1.06))
   pivot=Vector((0,0,1.05));rot=Matrix.Rotation(-1.40*fall,4,'Y');target=Vector((.05*fall,.04*fall,1.05-.75*fall))
   rig.matrix_world=Matrix.Translation(target)@rot@Matrix.Translation(-pivot)@Matrix.Translation(root)
   bpy.context.view_layer.update()
   # Keep the falling anatomy and boots above the stationary stone top.
   dg=bpy.context.evaluated_depsgraph_get();lowest=10
   for name in ['MPFB barbarian anatomy','Leather boot r','Leather boot l','Lasted leather shoe r','Lasted leather shoe l']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh()
    lowest=min(lowest,min((ob.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   if lowest<.095:rig.location.z+=.095-lowest;bpy.context.view_layer.update()
   if t<.35:
    weapon.matrix_world=(rig.matrix_world@rig.pose.bones['hand_r'].matrix)@hand_rest.inverted()@wrest
   else:
    drop=smooth(min(1,(t-.35)/.45));wm=wrest.copy();wm.translation=wrest.translation.lerp(Vector((-.45,-.52,.13)),drop)
    # Rotate the diagonal shaft until it lies across the ground, not through the corpse.
    wm=Matrix.Translation(wm.translation)@Matrix.Rotation(-.28*drop,4,'Y');weapon.matrix_world=wm
   if t<.35:shield.matrix_world=(rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix)@arm_rest.inverted()@shield_rest
   else:
    drop=smooth(min(1,(t-.35)/.45));pos=shield_rest.translation.lerp(Vector((.28,.10,.28)),drop);shield.matrix_world=Matrix.Translation(pos)@Matrix.Rotation(1.45*drop,4,'X')
   shield.rotation_mode='QUATERNION';shield.keyframe_insert('location',frame=i+1);shield.keyframe_insert('rotation_quaternion',frame=i+1)
   weapon.rotation_mode='QUATERNION';weapon.keyframe_insert('location',frame=i+1);weapon.keyframe_insert('rotation_quaternion',frame=i+1)
   for digit in ['index','middle','ring','pinky']:
    for k in range(1,4):rotate(f'{digit}_{k:02d}_r',(1,0,0),-.65*fall)
  bpy.context.view_layer.update()
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.keyframe_insert('rotation_quaternion',frame=i+1);p.keyframe_insert('location',frame=i+1)
  rig.keyframe_insert('location',frame=i+1);rig.keyframe_insert('rotation_euler',frame=i+1)
  assert base.matrix_world==base_matrix,'Base moved'
 if rig.animation_data:rig.animation_data.action.name='Barbarian '+clip
 for ob in [rig,weapon,shield]:
  if not ob.animation_data or not ob.animation_data.action:continue
  act=ob.animation_data.action;curves=[fc for layer in act.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'
 sc['sample_frames']=json.dumps(samples);sc['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();sc['clip']=clip;sc['loop']=loop
 sc.frame_set(1);(M/'clips').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 print('CLIP_READY',clip)

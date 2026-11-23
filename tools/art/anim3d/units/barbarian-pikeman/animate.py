"""Authored skeletal clips: two-handed grip solve, planted base, terminal death."""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-pikeman';source=M/'barbarian-pikeman.blend'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def aim(rig,name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();q=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())@q;m=q.to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
def limb(rig,up,lo,target,pole):
 a=rig.pose.bones[up].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[up].length;l2=rig.data.bones[lo].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(rig,up,elbow-a);aim(rig,lo,t-elbow)
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];basis=json.loads(rig['rest_basis']);rpos=rig.location.copy();ppos=pike.location.copy();sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 hand_local={s:pike.matrix_world.inverted()@(rig.matrix_world@rig.pose.bones['hand_'+s].head) for s in ['r','l']}
 disabled=[]
 for o in sc.objects:
  for md in o.modifiers:
   if md.type in ['SUBSURF','BEVEL'] and md.show_viewport:disabled.append(md);md.show_viewport=False
 samples=[]
 for i in range(count+(1 if loop else 0)):
  sc.frame_set(i+1);t=i/count if loop else i/(count-1);wave=math.sin(t*math.tau)
  for p in rig.pose.bones:p.matrix_basis=Matrix(basis[p.name]);p.rotation_mode='QUATERNION'
  rig.location=rpos;rig.rotation_euler=(0,0,0);pike.location=ppos;pike.rotation_euler=(0,0,0)
  if clip=='idle':
   p=rig.pose.bones['spine_03'];p.rotation_mode='XYZ';p.rotation_euler.y+=.012*wave;pike.location.z+=.006*wave
  elif clip=='move':
   rig.location.z+=.012*(1-math.cos(t*math.tau*2));pike.location.z+=.012*(1-math.cos(t*math.tau*2))
  elif clip=='attack':
   # Anticipation, short two-hand thrust in depth, then recovery; long pike stays in frame.
   amount=[0,-.25,-.4,.15,1,.9,.55,.2,.05,0][i];pike.location.y-=.06*amount;pike.location.x+=.07*amount;pike.location.z+=.06*amount;pike.rotation_euler.x=.08*amount;rig.location.x+=.035*amount
   p=rig.pose.bones['spine_03'];p.rotation_mode='XYZ';p.rotation_euler.z-=.08*amount
  elif clip=='hit':
   amount=[0,1,.5,0][i];rig.location.x-=.055*amount;pike.location.x-=.045*amount;pike.rotation_euler.x=-.06*amount
   p=rig.pose.bones['spine_03'];p.rotation_mode='XYZ';p.rotation_euler.x-=.12*amount
  elif clip=='death':
   t=min(i/8,1);ease=t*t*(3-2*t);rig.rotation_euler.y=-1.53*ease;rig.location.x+=.70*ease;rig.location.z+=.03*ease
   pike.rotation_euler.x=math.pi/2*ease;pike.location.y+=.50*ease;pike.location.z-=.94*ease
   bpy.context.view_layer.update()
   # Floor constraint for the actual pike endpoints, never scale-to-zero hiding.
   inv=Matrix.Translation(ppos).inverted();points=[Vector((-1.17,-.26,.20)),Vector((1.17,-.26,2.34))]
   lowest=min((pike.matrix_world@(inv@v)).z for v in points)
   if lowest<.12:pike.location.z+=.12-lowest
  bpy.context.view_layer.update()
  if clip!='death':
   for side,x,y,phase in [('r',-.36,-.01,0),('l',.35,.02,math.pi)]:
    step=math.sin(t*math.tau+phase) if clip=='move' else 0
    target=(x+.055*step-(rig.location.x-rpos.x),y+.09*step-(rig.location.y-rpos.y),.08+(.07*max(0,step) if clip=='move' else 0)-(rig.location.z-rpos.z))
    limb(rig,'thigh_'+side,'calf_'+side,target,((-.40 if side=='r' else .23),-.30,.48));aim(rig,'foot_'+side,((-.065 if side=='r' else .16),-.16,-.065))
   for side in ['r','l']:
    target=rig.matrix_world.inverted()@(pike.matrix_world@hand_local[side]);pole=(-.48,-.16,1.05) if side=='r' else (.14,-.18,.85)
    limb(rig,'upperarm_'+side,'lowerarm_'+side,target,pole);aim(rig,'hand_'+side,(.06,-.01,.065))
  else:
   # Release both hands after impact starts; articulated limbs collapse with the body.
   for side in ['r','l']:
    p=rig.pose.bones['thigh_'+side];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),.95*ease)
    p=rig.pose.bones['calf_'+side];p.rotation_mode='XYZ';p.rotation_euler.x+=.65*ease
    for bn,direction in [('upperarm_'+side,((.05 if side=='l' else -.05),-.05,-1)),('lowerarm_'+side,((-.20 if side=='l' else .20),-.15,-1))]:
     p=rig.pose.bones[bn];p.rotation_mode='QUATERNION';before=p.rotation_quaternion.copy();aim(rig,bn,direction);target=p.rotation_quaternion.copy();p.rotation_quaternion=before.slerp(target,ease);bpy.context.view_layer.update()
   bpy.context.view_layer.update();body=bpy.data.objects['GEO-MPFB-anatomy'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=max(0,.10-low)
  bpy.context.view_layer.update()
  for o in [rig,pike]:
   o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
  for p in rig.pose.bones:
   p.keyframe_insert('location',frame=i+1);p.keyframe_insert('rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler',frame=i+1);p.keyframe_insert('scale',frame=i+1)
  samples.append({s:list(rig.matrix_world@rig.pose.bones['hand_'+s].head) for s in ['r','l']})
 for md in disabled:md.show_viewport=True
 info={'frames':count,'fps':fps,'loop':loop,'source_master_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'hand_positions':samples[:count]};sc['clip_info']=json.dumps(info);sc.frame_set(1)
 for o in [rig,pike]:
  if o.animation_data and o.animation_data.action:
   o.animation_data.action.name='barbarian-pikeman-'+clip+'-'+o.name
   for layer in o.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in bag.fcurves:
       for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
 (M/'clips').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));(M/'clips'/f'{clip}.json').write_text(json.dumps(info,indent=2));print('CLIP_OK',clip,count,flush=True)

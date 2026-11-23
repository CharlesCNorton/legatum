"""CC0 reference-space skeletal motion; authored two-hand pike thrust only."""
import bpy, os, json, math, hashlib, sys
from pathlib import Path
from mathutils import Matrix, Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from retarget import prepare, apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/pikeman';source=M/'pikeman.blend'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def aim(rig,name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();q=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())@q;m=q.to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
def limb(rig,up,lo,target,pole):
 a=rig.pose.bones[up].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[up].length;l2=rig.data.bones[lo].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(rig,up,elbow-a);aim(rig,lo,t-elbow)
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];rpos=rig.location.copy();ppos=pike.location.copy();neutral={p.name:p.matrix.copy() for p in rig.pose.bones}
 hand_local={s:pike.matrix_world.inverted()@(rig.matrix_world@rig.pose.bones['hand_'+s].head) for s in ['r','l']}
 hand_rotation={s:rig.pose.bones['hand_'+s].matrix.to_quaternion() for s in ['r','l']}
 poles={s:rig.pose.bones['lowerarm_'+s].head.copy() for s in ['r','l']}
 if clip!='attack':
  # Dense 24 Hz cycle allows source-derived planted-foot root stabilization.
  if clip=='move':
   dense=[0.0]*24+[i/24 for i in range(25)];allframes,motion=prepare(rig,R,clip,dense);captured=[allframes[24+round(i*24/count)] for i in range(count+1)]
  else:
   phases=[i/count for i in range(count+1)] if loop else [0,.45,.75,0] if clip=='hit' else [min(i/(count-2),1) for i in range(count)]
   captured,motion=prepare(rig,R,clip,phases)
 else:motion={'provider':'Original weapon-specific attack','method':'two-hand IK thrust with anticipation and recovery'}
 # Imported donor actions never own target animation.
 rig.animation_data_clear();pike.animation_data_clear();sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 samples=[]
 for i in range(count+(1 if loop else 0)):
  sc.frame_set(i+1);rig.location=rpos;rig.rotation_euler=(0,0,0);pike.location=ppos;pike.rotation_euler=(0,0,0)
  apply_matrices(rig,neutral if clip=='attack' else captured[i]['matrices'])
  if clip!='attack':rig.location+=captured[i]['root']
  if clip=='death' and i<2:
   weight=i*.6;blended={}
   for name,m in captured[i]['matrices'].items():
    q=neutral[name].to_quaternion().slerp(m.to_quaternion(),weight);v=neutral[name].translation.lerp(m.translation,weight);x=q.to_matrix().to_4x4();x.translation=v;blended[name]=x
   apply_matrices(rig,blended)
  if clip=='attack':
   amount=[0,-.25,-.4,.15,1,.9,.55,.2,.05,0][i];pike.location+=Vector((.04,-.22,.02))*amount;pike.rotation_euler.x=.42*amount
   p=rig.pose.bones['spine_03'];m=Matrix.Rotation(-.12*amount,4,'X')@neutral['spine_03'];m.translation=neutral['spine_03'].translation;p.matrix=m;bpy.context.view_layer.update()
  elif clip=='death':
   t=min(i/(count-2),1);ease=t*t*(3-2*t);pike.rotation_euler.x=math.pi/2*ease;pike.location.y+=.50*ease;pike.location.z-=.94*ease
  else:
   # The weapon follows captured torso translation, while both arms keep a grip.
   chest=rig.matrix_world@rig.pose.bones['spine_03'].head
   ref=Matrix.Translation(rpos)@neutral['spine_03'].translation
   pike.location+=chest-ref
  bpy.context.view_layer.update()
  if clip!='death':
   for side in ['r','l']:
    target=rig.matrix_world.inverted()@(pike.matrix_world@hand_local[side]);limb(rig,'upperarm_'+side,'lowerarm_'+side,target,poles[side])
    p=rig.pose.bones['hand_'+side];m=hand_rotation[side].to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
  else:
   # Passive released pike rests on the disc; geometry and scale remain intact.
   inv=Matrix.Translation(ppos).inverted();low=min((pike.matrix_world@(inv@v)).z for v in [Vector((-1.17,-.26,.20)),Vector((1.17,-.26,2.34))]);pike.location.z+=max(0,.115-low)
  bpy.context.view_layer.update()
  # One root-height contact constraint; never rotate a retargeted foot.
  if clip=='move':
   lows=[]
   for side in ['l','r']:
    ob=bpy.data.objects['GEO-leather-boots'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lows.append(min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   dz=.092-min(lows);rig.location.z+=dz;pike.location.z+=dz
  elif clip=='death':
   ev=bpy.data.objects['GEO-MPFB-anatomy'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=max(0,.10-low)
  bpy.context.view_layer.update()
  for o in [rig,pike]:o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.keyframe_insert('location',frame=i+1);p.keyframe_insert('rotation_quaternion',frame=i+1);p.keyframe_insert('scale',frame=i+1)
  samples.append({s:list(rig.matrix_world@rig.pose.bones['hand_'+s].head) for s in ['r','l']})
 info={'frames':count,'fps':fps,'loop':loop,'source_master_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'motion':motion,'hand_positions':samples[:count]};sc['clip_info']=json.dumps(info)
 for o in [rig,pike]:
  if o.animation_data and o.animation_data.action:
   o.animation_data.action.name='pikeman-'+clip+'-'+o.name
   for layer in o.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in bag.fcurves:
       for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);(M/'clips').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));(M/'clips'/f'{clip}.json').write_text(json.dumps(info,indent=2));print('CLIP_OK',clip,count,flush=True)

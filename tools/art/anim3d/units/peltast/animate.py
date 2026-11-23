"""Five authored skeletal clips; genuine joints, delayed cloth, release and held death."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from mathutils import Quaternion
source=M/'peltast.blend';(M/'clips').mkdir(exist_ok=True)
def rotate(rig,name,angle,axis):
 p=rig.pose.bones[name];mat=p.matrix.copy();head=p.head.copy();p.matrix=Matrix.Translation(head)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-head)@mat;bpy.context.view_layer.update()
def limb(rig,upper,lower,target,pole):
 a=rig.pose.bones[upper].head.copy();t=Vector(target);axis=t-a;l1=rig.pose.bones[upper].length;l2=rig.pose.bones[lower].length;d=min(axis.length,l1+l2-.001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h
 bone_line(rig,upper,a,elbow);bone_line(rig,lower,elbow,t)
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
 cloth=bpy.data.objects['GEO-Blue wind folded cloak'].data.shape_keys.key_blocks['Trailing breeze'];initial_feet={s:rig.pose.bones['foot_'+s].matrix.copy() for s in ['l','r']}
 for i in range(n+1 if loop else n):
  f=i+1;sc.frame_set(f);rig.matrix_world=Matrix.Identity(4)
  for p in rig.pose.bones:
   p.location,p.rotation_quaternion,p.scale=rest[p.name]
  bpy.context.view_layer.update();phase=2*pi*i/n;t=i/(n-1)
  cloth.value=.12*sin(phase)
  if clip=='idle':
   rotate(rig,'spine_03',.009*sin(phase),'Y');rotate(rig,'neck_01',.008*sin(phase-.4),'Z');cloth.value=.22*sin(phase)
  elif clip=='move':
   # Stepping guard: feet alternately lift and travel in depth; base remains fixed.
   for side,offset in [('l',0),('r',pi)]:
    ph=phase+offset;orig=initial_feet[side];target=orig.translation+Vector((.055*sin(ph),.15*sin(ph),.09*max(0,sin(ph))))
    limb(rig,'thigh_'+side,'calf_'+side,target,rig.pose.bones['calf_'+side].head+Vector((0,-.5,.1)))
    mat=orig.copy();mat.translation=target;rig.pose.bones['foot_'+side].matrix=mat;bpy.context.view_layer.update()
   rotate(rig,'spine_03',.024*sin(phase),'Z');cloth.value=.65*sin(phase-.8)
  elif clip=='attack' and i not in (0,n-1):
   # Windup, forward acceleration, release, follow-through, recovered guard.
   xs=[66,61,59,77,107,145,158,134,91,66];ys=[47,49,51,44,44,59,78,72,53,47]
   target=P(xs[i],ys[i],-.075-.10*sin(pi*t));elbow=P(62+(xs[i]-66)*.6,76+12*sin(pi*t),-.07)
   bone_line(rig,'upperarm_r',rig.pose.bones['upperarm_r'].head,elbow);bone_line(rig,'lowerarm_r',elbow,target);bone_line(rig,'hand_r',target,target+Vector((.02,-.015,.03)))
   rotate(rig,'spine_03',-.06*sin(pi*t),'Y');cloth.value=.60*sin(pi*t)
  elif clip=='hit':
   angle=[0,-.14,-.07,0][i];rotate(rig,'spine_01',angle,'Y');rotate(rig,'neck_01',-angle*.6,'Y');cloth.value=[0,.6,.25,0][i]
  elif clip=='death':
   tt=min(i/(n-2),1);ease=tt*tt*(3-2*tt)
   rotate(rig,'upperarm_r',-.9*ease,'Y');rotate(rig,'lowerarm_r',-.65*ease,'X');rotate(rig,'upperarm_l',.35*ease,'Y')
   pivot=Vector((-.145,0,1.03));rig.matrix_world=Matrix.Translation(Vector((0,-.10*ease,-.57*ease)))@Matrix.Translation(pivot)@Matrix.Rotation(-1.5*ease,4,'X')@Matrix.Translation(-pivot)
   cloth.value=.3*sin(pi*tt)
  bpy.context.view_layer.update()
  for name,o in controls.items():
   mat=rig.matrix_world@rig.pose.bones[bones[name]].matrix@restbones[name].inverted()@worlds[name]
   if clip=='attack' and i not in (0,n-1) and name=='CTRL-Throwing javelin':
    grip=P(xs[i]+2,ys[i]-4,-.11);mat=Matrix.Translation(grip)@Matrix.Rotation([0,-.08,-.16,.22,.65,.75,.75,.4,.15,0][i],4,'Z')@Matrix.Translation(-worlds[name].translation)@worlds[name]
    hidden=5<=i<=8
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
 for action in bpy.data.actions:
  if hasattr(action,'fcurves'):curves=action.fcurves
  else:curves=[fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
  for fc in curves:
   for k in fc.keyframe_points:
    k.interpolation='CONSTANT' if 'hide_' in fc.data_path else 'BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
 sc['clip']=clip;sc['frames']=n;sc['loop']=loop;sc['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();sc.frame_set(1);save('clips/'+clip+'.blend');(M/'clips'/f'{clip}.json').write_text(json.dumps({'source_sha256':sc['source_sha256'],'frames':n,'fps':fps,'loop':loop},indent=2))
log('- Authored idle/move/attack/hit/death on MPFB rig: 8/8/10/4/10 samples; looping breathing/steps, thrown-javelin visibility, hit recovery, independent equipment release and held death. Cloth uses authored secondary deformation, not a cloth simulation.')

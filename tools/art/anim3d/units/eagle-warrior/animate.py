"""Five authored MPFB skeletal clips; explicit samples, loop closure, held death."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
master=M/'eagle-warrior.blend';digest=__import__('hashlib').sha256(master.read_bytes()).hexdigest();(M/'clips').mkdir(exist_ok=True)
def fcurves(action):
 if hasattr(action,'fcurves'):return list(action.fcurves)
 return [fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for cb in strip.channelbags for fc in cb.fcurves]
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
 bpy.ops.wm.open_mainfile(filepath=str(master));sc=bpy.context.scene;rig=bpy.data.objects['RIG-eagle-warrior'];neutral={n:Matrix(v) for n,v in json.loads(rig['neutral_pose']).items()};sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 weapon=[o for o in sc.objects if o.name.startswith(('GEO-Wooden macuahuitl','GEO-Obsidian inset blade','GEO-Club grip binding'))];weapon_world={o.name:o.matrix_world.copy() for o in weapon}
 # A single release control keeps the entire club together during a fall.
 ctrl=bpy.data.objects.new('CTRL-club-release',None);sc.collection.objects.link(ctrl)
 for o in weapon:
  world=o.matrix_world.copy();o.parent=ctrl;o.parent_type='OBJECT';o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=world
 base_hand=rig.pose.bones['hand_r'].matrix.copy();hand_inv=base_hand.inverted()
 def rotate(name,angle,axis='Y'):
  p=rig.pose.bones[name];pivot=p.head.copy();p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-pivot)@p.matrix;bpy.context.view_layer.update()
 for frame in range(1,count+2 if loop else count+1):
  t=(frame-1)/count if loop else min(frame-1,count-2)/(count-2);sc.frame_set(frame)
  for name,mat in neutral.items():rig.pose.bones[name].matrix_basis=mat.copy()
  rig.matrix_world=Matrix.Identity(4);bpy.context.view_layer.update();phase=2*pi*t
  if clip=='idle':
   rotate('spine_03',.012*sin(phase),'X');rotate('head',.018*sin(phase+.4),'Z');rotate('lowerarm_r',.016*sin(phase-.3),'Y')
  elif clip=='move':
   # Authored in-place step; planted support stays at rest, swing rises and advances.
   for side,sg,x,y,d in [('r',1,86,207,.11),('l',-1,174,199,.42)]:
    wave=sin(phase)*sg;lift=max(0,wave)*8;travel=cos(phase)*4*sg;hip=(122,138,0) if side=='r' else (143,138,0);knee=(104+travel*.5,169-lift*.6,.01) if side=='r' else (161+travel*.5,168-lift*.6,.09);ankle=(x+travel,y-lift,d);toe=(83+travel,218-lift,.08) if side=='r' else (187+travel,208-lift,.39)
    bone_line(rig,'thigh_'+side,P(*hip),P(*knee));bone_line(rig,'calf_'+side,P(*knee),P(*ankle));bone_line(rig,'foot_'+side,P(*ankle),P(*toe))
   rotate('spine_03',.025*sin(phase),'Z');rotate('upperarm_r',.035*sin(phase),'Y');rotate('head',-.02*sin(phase),'Z')
  elif clip=='attack':
   vals=[0,.12,.23,-.25,-.85,-1.05,-.55,-.20,-.04,0];a=vals[frame-1];rotate('spine_03',a*.08,'Z');rotate('upperarm_r',a,'Y');rotate('lowerarm_r',-.10*sin(pi*t),'Y');rotate('head',-.10*sin(pi*t),'Z');rotate('upperarm_l',.08*sin(pi*t),'Y')
  elif clip=='hit':
   recoil=[0,.18,-.07,0][frame-1];rotate('spine_01',recoil,'X');rotate('head',recoil*.7,'X');rotate('upperarm_l',recoil*.5,'Y')
  elif clip=='death':
   fall=min(1,max(0,(t-.1)/.72));ease=fall*fall*(3-2*fall);rotate('thigh_r',-.65*ease,'Y');rotate('calf_r',.75*ease,'Y');rotate('thigh_l',.35*ease,'Y');rotate('calf_l',-.60*ease,'Y');rotate('upperarm_r',-.55*ease,'Y');rotate('upperarm_l',-.35*ease,'Y');pivot=P(132,139,0);rig.matrix_world=Matrix.Translation(Vector((-.04,0,-.51*ease)))@Matrix.Translation(pivot)@Matrix.Rotation(1.32*ease,4,'Y')@Matrix.Translation(-pivot)
  bpy.context.view_layer.update()
  if clip=='death':
   # Ground the actual deformed figure, including rigid feather tips, on the
   # stone. A pelvis-only drop otherwise lets the folded knees penetrate it.
   low=100.;dg=bpy.context.evaluated_depsgraph_get()
   for ob in sc.objects:
    if ob.type!='MESH' or ob.hide_render or ob in weapon or ob.name=='GEO-cream-stone-base':continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh()
    if me.vertices:low=min(low,min((ob.matrix_world@v.co).z for v in me.vertices))
    ev.to_mesh_clear()
   rig.location.z+=max(0,.205-low);bpy.context.view_layer.update()
  ctrl.matrix_world=rig.matrix_world@rig.pose.bones['hand_r'].matrix@hand_inv
  if clip=='death' and t>.10:
   u=min(1,(t-.10)/.50);u=u*u*(3-2*u);a=P(53,85,-.10);b=P(101,14,-.10);target_a=Vector((P(74,128).x,-.32,.235));target_b=Vector((P(166,128).x,-.32,.235));q=(b-a).rotation_difference(target_b-target_a);drop=Matrix.Translation(target_a)@q.to_matrix().to_4x4()@Matrix.Translation(-a);current=ctrl.matrix_world;loc=current.translation.lerp(drop.translation,u);rot=current.to_quaternion().slerp(drop.to_quaternion(),u);ctrl.matrix_world=Matrix.Translation(loc)@rot.to_matrix().to_4x4()
  ctrl.keyframe_insert('location',frame=frame);ctrl.rotation_mode='QUATERNION';ctrl.keyframe_insert('rotation_quaternion',frame=frame);ctrl.keyframe_insert('scale',frame=frame)
  rig.rotation_mode='QUATERNION';rig.keyframe_insert('location',frame=frame);rig.keyframe_insert('rotation_quaternion',frame=frame)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
 for obj in [rig,ctrl]:
  if obj.animation_data and obj.animation_data.action:
   obj.animation_data.action.name='Eagle warrior '+clip+' '+obj.name
   for fc in fcurves(obj.animation_data.action):
    for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);sc['clip_info']=json.dumps({'name':clip,'frames':count,'fps':fps,'loop':loop,'authored':True});sc['source_master_sha256']=digest;save('clips/'+clip+'.blend');(M/'clips'/f'{clip}.json').write_text(json.dumps({'source_master_sha256':digest,'frames':count,'fps':fps,'loop':loop},indent=2));print('ANIMATE_OK',clip,flush=True)
log('- Authored idle, move, attack, hit and terminal death on the MPFB skeleton; no mocap or cloth simulation claimed.')

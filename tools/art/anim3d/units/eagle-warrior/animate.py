"""CC0 Quaternius source motion and authored macuahuitl attack on MPFB."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from retarget import prepare, apply_matrices
master=M/'eagle-warrior.blend';digest=__import__('hashlib').sha256(master.read_bytes()).hexdigest();(M/'clips').mkdir(exist_ok=True)
def fcurves(action):
 if hasattr(action,'fcurves'):return list(action.fcurves)
 return [fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for cb in strip.channelbags for fc in cb.fcurves]
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('CLIP') and os.environ['CLIP']!=clip:continue
 (M/'clips'/f'{clip}.json').unlink(missing_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(master));sc=bpy.context.scene;rig=bpy.data.objects['RIG-eagle-warrior'];neutral={n:Matrix(v) for n,v in json.loads(rig['neutral_pose']).items()};sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 weapon=[o for o in sc.objects if o.name.startswith(('GEO-Wooden macuahuitl','GEO-Obsidian inset blade','GEO-Club grip binding'))]
 # A single release control keeps the entire club together during a fall.
 ctrl=bpy.data.objects.new('CTRL-club-release',None);sc.collection.objects.link(ctrl)
 for o in weapon:
  world=o.matrix_world.copy();o.parent=ctrl;o.parent_type='OBJECT';o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=world
 base_hand=rig.pose.bones['hand_r'].matrix.copy();hand_inv=base_hand.inverted()
 shield=[o for o in sc.objects if o.name.startswith(('GEO-Convex wicker shield','GEO-Shield red wrapped rim','GEO-Rim binding stitch','GEO-Wicker woven row','GEO-Shield fringe feather'))]
 shield_ctrl=bpy.data.objects.new('CTRL-shield-release',None);sc.collection.objects.link(shield_ctrl)
 for ob in shield:
  world=ob.matrix_world.copy();ob.parent=shield_ctrl;ob.parent_type='OBJECT';ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=world
 shield_hand_inv=rig.pose.bones['hand_l'].matrix.inverted()

 phases=[i/count if loop else min(1,i/7) if clip=='death' else i/(count-1) for i in range(count+int(loop))]
 motion,provenance=prepare(rig,ROOT,clip,phases) if clip!='attack' else (None,{'provider':'Original macuahuitl attack'})
 (M/'clips'/f'{clip}-motion.json').write_text(json.dumps(provenance,indent=2))

 def rotate(name,angle,axis='Y'):
  p=rig.pose.bones[name];pivot=p.head.copy();p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-pivot)@p.matrix;bpy.context.view_layer.update()
 for frame in range(1,count+2 if loop else count+1):
  t=phases[frame-1];sc.frame_set(frame)
  for name,mat in neutral.items():rig.pose.bones[name].matrix_basis=mat.copy()
  rig.matrix_world=Matrix.Identity(4);bpy.context.view_layer.update()
  if motion:
   apply_matrices(rig,motion[frame-1]['matrices']);rig.location=motion[frame-1]['root'];bpy.context.view_layer.update()
  if clip=='idle':
   rotate('upperarm_r',-.16,'Y')
  if clip=='move':
   # Constant carrying guard over source motion keeps the raised club in frame.
   rotate('upperarm_r',-.72,'Y')
  if clip=='death':
   ease=t*t*(3-2*t);pivot=rig.pose.bones['pelvis'].head.copy()
   rig.matrix_world=Matrix.Translation(rig.location)@Matrix.Translation(pivot)@Matrix.Rotation(-1.15*ease,4,'Z')@Matrix.Translation(-pivot)
   bpy.context.view_layer.update()
  if clip=='attack':
   vals=[0,.12,.23,-.25,-.85,-1.05,-.55,-.20,-.04,0];a=vals[frame-1];rotate('spine_03',a*.08,'Z');rotate('upperarm_r',a,'Y');rotate('lowerarm_r',-.10*sin(pi*t),'Y');rotate('head',-.10*sin(pi*t),'Z');rotate('upperarm_l',.08*sin(pi*t),'Y')
  bpy.context.view_layer.update()
  if motion:
   # Ground the actual deformed figure, including rigid feather tips, on the
   # stone. A pelvis-only drop otherwise lets the folded knees penetrate it.
   low=100.;dg=bpy.context.evaluated_depsgraph_get()
   for ob in sc.objects:
    if ob.type!='MESH' or ob.hide_render or ob in weapon or ob in shield or ob.name=='GEO-cream-stone-base':continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh()
    if me.vertices:low=min(low,min((ob.matrix_world@v.co).z for v in me.vertices))
    ev.to_mesh_clear()
   rig.location.z+=.205-low;bpy.context.view_layer.update()
   if clip=='death':
    # Centre the source collapse on the stone without altering the captured pose.
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for ob in sc.objects:
     if ob.type!='MESH' or ob.hide_render or ob in weapon or ob in shield or ob.name=='GEO-cream-stone-base':continue
     ev=ob.evaluated_get(dg);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    rig.location.x+=(.06-(min(p.x for p in pts)+max(p.x for p in pts))/2)*ease
    rig.location.y+=(.10-(min(p.y for p in pts)+max(p.y for p in pts))/2)*ease
    bpy.context.view_layer.update()
  ctrl.matrix_world=rig.matrix_world@rig.pose.bones['hand_r'].matrix@hand_inv
  if clip=='death' and t>0:
   u=min(1,t/.50);u=u*u*(3-2*u);a=P(53,85,-.10);b=P(101,14,-.10);target_a=Vector((P(74,128).x,-.32,.275));target_b=Vector((P(166,128).x,-.32,.275));q=(b-a).rotation_difference(target_b-target_a);drop=Matrix.Translation(target_a)@q.to_matrix().to_4x4()@Matrix.Translation(-a);current=Matrix.Identity(4);loc=current.translation.lerp(drop.translation,u);rot=current.to_quaternion().slerp(drop.to_quaternion(),u);ctrl.matrix_world=Matrix.Translation(loc)@rot.to_matrix().to_4x4()
  shield_ctrl.matrix_world=rig.matrix_world@rig.pose.bones['hand_l'].matrix@shield_hand_inv
  if clip=='death' and t>0:
   u=min(1,t/.60);u=u*u*(3-2*u);center=P(174,111,-.32)
   drop=Matrix.Translation(Vector((-.36,.22,.31)))@Matrix.Rotation(-pi/2,4,'X')@Matrix.Translation(-center)
   shield_ctrl.matrix_world=Matrix.Translation(Vector((0,0,0)).lerp(drop.translation,u))@Matrix.Identity(4).to_quaternion().slerp(drop.to_quaternion(),u).to_matrix().to_4x4()
   bpy.context.view_layer.update()
   dg=bpy.context.evaluated_depsgraph_get();low=100
   for ob in shield:
    ev=ob.evaluated_get(dg);me=ev.to_mesh();low=min(low,min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   shield_ctrl.location.z+=max(0,.205-low)
  shield_ctrl.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:shield_ctrl.keyframe_insert(prop,frame=frame)
  ctrl.keyframe_insert('location',frame=frame);ctrl.rotation_mode='QUATERNION';ctrl.keyframe_insert('rotation_quaternion',frame=frame);ctrl.keyframe_insert('scale',frame=frame)
  rig.rotation_mode='QUATERNION';rig.keyframe_insert('location',frame=frame);rig.keyframe_insert('rotation_quaternion',frame=frame)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
 for obj in [rig,ctrl,shield_ctrl]:
  if obj.animation_data and obj.animation_data.action:
   obj.animation_data.action.name='Eagle warrior '+clip+' '+obj.name
   for fc in fcurves(obj.animation_data.action):
    for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);sc['clip_info']=json.dumps({'name':clip,'frames':count,'fps':fps,'loop':loop,'motion':provenance});sc['source_master_sha256']=digest;save('clips/'+clip+'.blend');(M/'clips'/f'{clip}.json').write_text(json.dumps({'source_master_sha256':digest,'frames':count,'fps':fps,'loop':loop,'motion':provenance},indent=2));print('ANIMATE_OK',clip,flush=True)
log('- Retargeted CC0 Quaternius idle/walk/hit/death with calibrated bone rolls; retained authored macuahuitl attack and rigid club release. No cloth simulation claimed.')

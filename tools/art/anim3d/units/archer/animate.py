"""Five skeletal clips. CC0 Quaternius motion with an authored bow attack.

Bone transforms, bow flex, nock and visibility are saved as keys in each master.
The unchanging stone is outside the rig. No scale-to-zero hiding or runtime scripts.
"""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(1,str(Path(__file__).resolve().parents[2]))
from common import *
from retarget import prepare, apply_matrices
from math import sin,cos,pi
source=MASTER/'archer.blend';source_hash=hashlib.sha256(source.read_bytes()).hexdigest();out=MASTER/'clips';out.mkdir(exist_ok=True)
def turn(rig,name,axis,angle):
 p=rig.pose.bones[name];pos=p.head.copy();p.matrix=Matrix.Translation(pos)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-pos)@p.matrix;bpy.context.view_layer.update()
for clip,(count,fps,loop) in CLIPS.items():
 if os.environ.get('ONLY_CLIP') and clip!=os.environ['ONLY_CLIP']:continue
 (MASTER/'renders'/f'e-{clip}'/'render.json').unlink(missing_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Archer MPFB rig'];neutral=json.loads(rig['rest_pose']);base=rig.location.copy();control=bpy.data.objects['Bow grip'];control_rest=control.matrix_basis.copy();bow=bpy.data.objects['GEO-Yew bow'];bowedge=bpy.data.objects['GEO-Bow belly highlight'];string=bpy.data.objects['GEO-Bowstring'];arrow=bpy.data.objects['GEO-Nocked arrow'];body=bpy.data.objects['GEO-MPFB archer anatomy'];bow_points={o.name:[Vector(p.co[:3]) for p in o.data.splines[0].points] for o in [bow,bowedge]}
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 rig.rotation_mode='QUATERNION';control.rotation_mode='QUATERNION';sc.render.fps=fps;sc.frame_start=0;sc.frame_end=count-1
 # Sample the open library before inserting any target keys.
 motion = None
 if clip != 'attack':
  phases = [f/count if loop else min(1,f/(count-2)) if clip=='death' else f/(count-1) for f in range(count+1 if loop else count)]
  motion, motion_meta = prepare(rig,ROOT,clip,phases)
  if loop: motion[-1] = motion[0]
  (out/f'{clip}-motion.json').write_text(json.dumps(motion_meta,indent=2))
 sc.render.fps=fps
 checks=[]
 for f in range(count+1 if loop else count):
  sc.frame_set(f);t=f/count if loop else f/(count-1);rig.location=base;rig.rotation_quaternion=(1,0,0,0);control.matrix_basis=control_rest
  for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
  bpy.context.view_layer.update();draw=1;release=0
  if motion:
   sample=motion[f];apply_matrices(rig,sample['matrices'])
   # Transition from the painted guard to the open fall, with no first-frame pop.
   weight=min(1,f/3) if clip=='death' else (0 if f in (0,count-1) else 1) if clip=='hit' else 1
   if weight<1:
    for p in rig.pose.bones:
     p.matrix_basis=Matrix(neutral[p.name]).lerp(p.matrix_basis,weight)
   rig.location=base+sample['root']*weight
   bpy.context.view_layer.update()
  if clip=='attack':
   draw=[1,1,1.02,1.03,0,.05,.1,.2,.80,1][f];recoil=[0,0,0,.03,-.04,-.02,0,0,0,0][f]
   hand_target=(-.005+.38*(1-draw),-.22,1.43)
   if 4<=f<=7:hand_target=([-.09,-.12,-.10,.04][f-4],-.22,1.45)
   limb(rig,'upperarm_r','lowerarm_r',hand_target,(-.55,-.08,1.52));aim(rig,'hand_r',(.085,0,.015));turn(rig,'spine_03','Z',recoil)
  elif clip=='death':
   # Orient the captured backward fall diagonally across the display base.
   fall_turn=Matrix.Rotation(1.15*min(1,f/4),4,'Z')
   rig.rotation_quaternion=fall_turn.to_quaternion()
   rig.location=base+fall_turn.to_3x3()@(rig.location-base)
   bpy.context.view_layer.update()
   # Keep the source fall centered on this miniature's stationary disc.
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   coords=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
   center=Vector(((min(v.x for v in coords)+max(v.x for v in coords))/2,
                  (min(v.y for v in coords)+max(v.y for v in coords))/2,0))
   settle=max(0,min(1,(f-2)/2));settle=settle*settle*(3-2*settle)
   rig.location+=(Vector((.05,0,0))-center)*settle
   bpy.context.view_layer.update()
   release=max(0,min(1,(t-.15)/.5));draw=1-release
   # Released bow settles horizontally at front edge, independent of the hand.
   bpy.context.view_layer.update();w=control.matrix_world.copy();target=Matrix.Translation(Vector((.05,0,.13)))@Matrix.Rotation(.65,4,'Z')@Matrix.Rotation(pi/2,4,'X');q=w.to_quaternion().slerp(target.to_quaternion(),release);loc=w.translation.lerp(target.translation,release);control.matrix_world=Matrix.Translation(loc)@q.to_matrix().to_4x4()
   # Mesh-derived floor correction prevents anatomical penetration during the fall.
   bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   if low<.096 or f>=4:
    released_world=control.matrix_world.copy();rig.location.z+=.096-low;bpy.context.view_layer.update();control.matrix_world=released_world
  bpy.context.view_layer.update()
  if clip=='move':
   # Bone-head height is not sole contact. Ground the actual finished footwear.
   deps=bpy.context.evaluated_depsgraph_get();sole_low=[]
   for side in ['l','r']:
    sole=bpy.data.objects['GEO-Sandal sole '+side];ev=sole.evaluated_get(deps);me=ev.to_mesh();sole_low.append(min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
   rig.location.z+=.092-min(sole_low);bpy.context.view_layer.update()
  # A small physical bend of the bow limbs accompanies release; endpoints remain real geometry.
  for o in [bow,bowedge]:
   points=o.data.splines[0].points
   for i,(p,rest) in enumerate(zip(points,bow_points[o.name])):
    u=-1+2*i/(len(points)-1);v=rest+Vector((.07*(1-draw)*u*u,0,0));p.co=(*v,1);p.keyframe_insert('co',frame=f)
  top=bow.matrix_world@Vector(bow.data.splines[0].points[-1].co[:3]);bottom=bow.matrix_world@Vector(bow.data.splines[0].points[0].co[:3]);grip=control.matrix_world.translation
  nock=rig.matrix_world@rig.pose.bones['hand_r'].tail
  if clip=='death':nock=nock.lerp((top+bottom)*.5,release)
  if clip=='attack' and 4<=f<=7:nock=(top+bottom)*.5
  for p,v in zip(string.data.splines[0].points,[bottom,nock,top]):p.co=(*v,1);p.keyframe_insert('co',frame=f)
  tip=grip+Vector((.13,-.005,.025))
  if clip=='death':tip=nock+(top-bottom).cross(Vector((0,0,1))).normalized()*.6 if (top-bottom).cross(Vector((0,0,1))).length>.001 else grip
  for p,v in zip(arrow.data.splines[0].points,[nock,tip]):p.co=(*v,1);p.keyframe_insert('co',frame=f)
  arrow.hide_render=(clip=='attack' and 4<=f<=7) or (clip=='death' and release>.4);arrow.keyframe_insert('hide_render',frame=f)
  for o in [rig,control]:
   for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(prop,frame=f)
  for p in rig.pose.bones:
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
  checks.append({'frame':f,'nock_distance':(nock-rig.matrix_world@rig.pose.bones['hand_r'].tail).length,'bow_grip_distance':(grip-(rig.matrix_world@rig.pose.bones['hand_l'].head+Vector((0,-.013,.045)))).length})
 # Discrete property visibility has constant interpolation; transforms use auto-clamped Bezier.
 for action in bpy.data.actions:
  for layer in action.layers:
   for strip in layer.strips:
    for bag in getattr(strip,'channelbags',[]):
     for fc in bag.fcurves:
      for k in fc.keyframe_points:
       if 'hide_render' in fc.data_path:k.interpolation='CONSTANT'
       else:k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='AUTO_CLAMPED'
 sc['source_sha256']=source_hash;sc['clip']=clip;sc['sample_frames']=json.dumps(list(range(count)));sc['motion_source']='Quaternius CC0 rest/roll-compensated motion; original bow attack' if motion else 'Original bow attack';sc.frame_set(0);save(out/f'{clip}.blend');(out/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':source_hash,'checks':checks},indent=2));log(f'- Authored {clip}: {count} frames, {fps} fps; real rig keys, bow flex and nock keys, stationary base.')

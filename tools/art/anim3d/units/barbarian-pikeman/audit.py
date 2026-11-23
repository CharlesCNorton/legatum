"""Independent master/rig audit without rendering or changing saved assets."""
import bpy,os,json,math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_constants import PIKE_START, PIKE_END, PIKE_ORIGIN
from mathutils import Matrix,Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-pikeman';result=[]
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];base=bpy.data.objects['GEO-cream-stone-base'];stationary=base.matrix_world.copy();maxgrip=0;actions=[];feet=[]
 for o in sc.objects:
  for md in o.modifiers:
   if md.type in ['SUBSURF','BEVEL']:md.show_viewport=False
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==stationary
  for o in sc.objects:
   assert all(math.isfinite(v) for row in o.matrix_world for v in row),o.name
   assert min(abs(v) for v in o.scale)>.0001,o.name
  inv=Matrix.Translation(Vector(PIKE_ORIGIN)).inverted();a=pike.matrix_world @ (inv @ Vector(PIKE_START));b=pike.matrix_world @ (inv @ Vector(PIKE_END));axis=(b-a).normalized()
  if clip!='death':
   for side in ['r','l']:
    delta=rig.matrix_world @ rig.pose.bones['hand_'+side].head-a;maxgrip=max(maxgrip,(delta-axis*delta.dot(axis)).length)
  actions.append([list(r) for r in rig.matrix_world])
  if clip=='move':
   frame={}
   for side in ['l','r']:
    bone=rig.pose.bones['foot_'+side]
    # Measure yaw with the lateral foot axis: ankle-to-toe projection reverses
    # at steep toe-off and is not a valid travel-direction test at that pitch.
    lateral=bone.matrix.to_3x3() @ (bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0)))
    forward=lateral.cross(Vector((0,0,1)))
    frame[side]={name:list(rig.matrix_world @ rig.pose.bones[name+'_'+side].head) for name in ['foot','ball']}
    frame[side]['forward']=list(forward)
   feet.append(frame)
 assert maxgrip<.13,(clip,'wrist-to-shaft',maxgrip)
 if clip=='death':assert actions[-1]==actions[-2],'death root not held'
 foot_check=None
 if clip=='move':
  info=json.loads(sc['clip_info']);contact=info['motion']['contact'];speed=contact['virtual_ground_m_per_sample'];errors=[];yaw=[]
  for side,start,end in [('l',0,4),('r',4,8)]:
   for i in range(start,end-1):
    a=Vector(feet[i][side]['ball']);b=Vector(feet[i+1][side]['ball']);errors.append(max(abs(b.x-a.x),abs(b.y-a.y-speed)))
  for frame in feet:
   for side in ['l','r']:
    direction=Vector(frame[side]['forward'])
    yaw.append(math.degrees(math.atan2(abs(direction.x),-direction.y)))
  assert max(errors)<.002,('sampled stance drift',max(errors))
  assert max(yaw)<35,('foot travel direction mismatch',max(yaw))
  foot_check={'max_sampled_stance_residual_m':max(errors),'max_forward_yaw_deg':max(yaw),'virtual_ground_m_per_sample':speed,'limitation':'toe stance samples, not a full heel rollover collision test'}
 result.append({'foot_check':foot_check,'clip':clip,'frames':n,'max_wrist_to_shaft_m':maxgrip,'base_stationary':True,'finite_transforms':True,'safe_scales':True,'bones':len(rig.data.bones)})
(R/'review/3d-v2/barbarian-pikeman-rig-audit.json').write_text(json.dumps(result,indent=2));print('AUDIT_OK',json.dumps(result))

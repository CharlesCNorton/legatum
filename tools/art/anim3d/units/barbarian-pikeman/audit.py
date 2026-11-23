"""Independent master/rig audit without rendering or changing saved assets."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-pikeman';result=[]
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];base=bpy.data.objects['GEO-cream-stone-base'];stationary=base.matrix_world.copy();maxgrip=0;actions=[]
 for o in sc.objects:
  for md in o.modifiers:
   if md.type in ['SUBSURF','BEVEL']:md.show_viewport=False
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==stationary
  for o in sc.objects:
   assert all(math.isfinite(v) for row in o.matrix_world for v in row),o.name
   assert min(abs(v) for v in o.scale)>.0001,o.name
  inv=Matrix.Translation(Vector((-.24,-.26,1.06))).inverted();a=pike.matrix_world @ (inv @ Vector((-1.17,-.26,.20)));b=pike.matrix_world @ (inv @ Vector((1.17,-.26,2.34)));axis=(b-a).normalized()
  if clip!='death':
   for side in ['r','l']:
    delta=rig.matrix_world @ rig.pose.bones['hand_'+side].head-a;maxgrip=max(maxgrip,(delta-axis*delta.dot(axis)).length)
  actions.append([list(r) for r in rig.matrix_world])
 assert maxgrip<.13,(clip,'wrist-to-shaft',maxgrip)
 if clip=='death':assert actions[-1]==actions[-2],'death root not held'
 result.append({'clip':clip,'frames':n,'max_wrist_to_shaft_m':maxgrip,'base_stationary':True,'finite_transforms':True,'safe_scales':True,'bones':len(rig.data.bones)})
(R/'review/3d-v2/barbarian-pikeman-rig-audit.json').write_text(json.dumps(result,indent=2));print('AUDIT_OK',json.dumps(result))

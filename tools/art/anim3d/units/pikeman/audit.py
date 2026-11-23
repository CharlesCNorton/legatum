"""Independent rig, provenance, grip, stationary-base and terminal-pose checks."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/pikeman';result=[]
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];base=bpy.data.objects['GEO-cream-stone-base'];stationary=base.matrix_world.copy();maxgrip=0;poses=[]
 info=json.loads(sc['clip_info']);assert info['source_master_sha256']==hashlib.sha256((M/'pikeman.blend').read_bytes()).hexdigest()
 assert info['motion']['provider'].startswith('Quaternius') if clip!='attack' else 'Original' in info['motion']['provider']
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==stationary
  for o in sc.objects:
   assert all(math.isfinite(v) for row in o.matrix_world for v in row),o.name
   assert min(abs(v) for v in o.scale)>.0001,o.name
  inv=Matrix.Translation(Vector((-.24,-.26,1.06))).inverted();a=pike.matrix_world@(inv@Vector((-1.17,-.26,.20)));b=pike.matrix_world@(inv@Vector((1.17,-.26,2.34)));axis=(b-a).normalized()
  if clip!='death':
   for side in ['r','l']:
    delta=rig.matrix_world@rig.pose.bones['hand_'+side].head-a;maxgrip=max(maxgrip,(delta-axis*delta.dot(axis)).length)
  poses.append([v for p in rig.pose.bones for row in p.matrix for v in row]+[v for row in rig.matrix_world for v in row])
 assert maxgrip<.13,(clip,'wrist-to-shaft',maxgrip)
 if clip=='death':assert max(abs(a-b) for a,b in zip(poses[-1],poses[-2]))<1e-5,'death not held'
 result.append({'clip':clip,'frames':n,'max_wrist_to_shaft_m':maxgrip,'base_stationary':True,'finite_transforms':True,'safe_scales':True,'bones':len(rig.data.bones),'motion':info['motion']['provider']})
(R/'review/3d-v2/pikeman-rig-audit.json').write_text(json.dumps(result,indent=2));print('AUDIT_OK',json.dumps(result))

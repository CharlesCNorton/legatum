"""Geometry/provenance/contact evidence; visual gait approval stays separate."""
import bpy,os,json,hashlib
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/keshig';report={};base_matrix=None
master_hash=hashlib.sha256((M/'keshig.blend').read_bytes()).hexdigest()
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/f'clips/{clip}.blend'));sc=bpy.context.scene
 assert sc['source_master_sha256']==master_hash
 assert len(bpy.data.objects['Rider MPFB game_engine'].data.bones)==53
 floors=[]
 for f in range(1,count+1):
  sc.frame_set(f);bpy.context.view_layer.update();base=bpy.data.objects['Stationary cream stone'];mat=[list(r) for r in base.matrix_world]
  if base_matrix is None:base_matrix=mat
  assert mat==base_matrix,'Base moved'
  for o in sc.objects:
   assert min(abs(v) for v in o.scale)>.00001,(o.name,'unsafe scale')
  horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lowest=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();floors.append(round(lowest-sc['support_height'],5))
 report[clip]={'frames':count,'horse_action':sc['horse_source_action'],'rider_action':sc['rider_source_action'],'minimum_geometry_height_above_support':floors}
assert min(report['move']['minimum_geometry_height_above_support'])>=-.003
report['master_sha256']=master_hash;report['visual_approval']=False;report['limitations']='Native CC0 gallop retains suspension. Ground-height evidence is not proof of zero sliding or full rider/equipment collision clearance; inspect g-feet-check and clips.'
(M/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

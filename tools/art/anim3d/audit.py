"""Inspect saved animation geometry, immutable base and persistent cloth cache."""
import bpy,os,json,sys
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/spearman-3d-v2';report={};failures=[]
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/clip/(clip+'.blend')))
 sc=bpy.context.scene;base=bpy.data.objects['Stationary cream stone'];base_matrix=base.matrix_world.copy()
 rig=bpy.data.objects['Spearman • MPFB game_engine'];body=bpy.data.objects['MPFB anatomical male • original topology']
 assert len(body.data.vertices)==19158 and len(rig.data.bones)==53
 cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip'];assert cloth.point_cache.is_baked
 rows=[]
 for frame in json.loads(sc['sample_frames']):
  sc.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();bounds=[1.,1.,0.,0.];minz=100;lowest=None
  assert base.matrix_world==base_matrix
  for o in sc.objects:
   if o.type not in ['MESH','CURVE'] or o==base or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh()
   for v in me.vertices:
    w=o.matrix_world @ v.co
    if w.z<minz:minz=w.z;lowest=o.name
    p=world_to_camera_view(sc,sc.camera,w);bounds=[min(bounds[0],p.x),min(bounds[1],p.y),max(bounds[2],p.x),max(bounds[3],p.y)]
   ev.to_mesh_clear()
  row={'frame':frame,'camera_bounds':bounds,'min_z':minz,'lowest_object':lowest};rows.append(row)
  if min(bounds[:2])<0 or max(bounds[2:])>1:failures.append(f'{clip}/{frame}: geometry outside camera')
  if minz<.07:failures.append(f'{clip}/{frame}: {lowest} intersects base, z={minz:.4f}')
 report[clip]=rows
report['failures']=failures;(R/'review/3d-v2/rig-audit.json').write_text(json.dumps(report,indent=2))
print('AUDIT',len(failures),'findings')
for f in failures:print(f)
raise SystemExit(bool(failures))

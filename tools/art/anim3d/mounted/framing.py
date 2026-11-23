"""Find geometry outside the fixed camera before rendering expensive clips."""
import bpy,os,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/horseman-3d';report=[]
for clip,frames in [('hit',[2,3]),('death',[5,6,7])]:
 bpy.ops.wm.open_mainfile(filepath=str(m/'clips'/f'{clip}.blend'));sc=bpy.context.scene
 for f in frames:
  sc.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
  for ob in sc.objects:
   if ob.type not in ['MESH','CURVE'] or ob.hide_render:continue
   ev=ob.evaluated_get(dg);me=ev.to_mesh()
   if not me or not me.vertices:continue
   low=[min(v.co[i] for v in me.vertices) for i in range(3)];high=[max(v.co[i] for v in me.vertices) for i in range(3)];ev.to_mesh_clear()
   corners=[(x,y,z) for x in [low[0],high[0]] for y in [low[1],high[1]] for z in [low[2],high[2]]]
   qs=[world_to_camera_view(sc,sc.camera,ev.matrix_world@Vector(p)) for p in corners]
   box=[min(p.x for p in qs)*256,min(1-p.y for p in qs)*256,max(p.x for p in qs)*256,max(1-p.y for p in qs)*256]
   if box[0]<0 or box[1]<0 or box[2]>256 or box[3]>256:report.append({'clip':clip,'frame':f,'object':ob.name,'bbox':box})
print(json.dumps(report,indent=2));(r/'review/3d-v2/horseman-framing-audit.json').write_text(json.dumps(report,indent=2))

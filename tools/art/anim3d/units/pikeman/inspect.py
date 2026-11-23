"""Print projected object extents for matching the physical mesh to the painting."""
import bpy,os
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(Path(os.environ['ANIM_ROOT'])/'masters/pikeman/pikeman.blend'))
sc=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
for o in sc.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[world_to_camera_view(sc,sc.camera,ev.matrix_world@v.co) for v in me.vertices];ev.to_mesh_clear()
 if ps:print(o.name,[round(x,1) for x in [min(p.x for p in ps)*256,256-max(p.y for p in ps)*256,max(p.x for p in ps)*256,256-min(p.y for p in ps)*256]])

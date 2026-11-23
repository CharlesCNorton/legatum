import bpy,os,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/panzer'
bpy.ops.wm.open_mainfile(filepath=str(m/'panzer-plain.blend'));s=bpy.context.scene;bpy.context.view_layer.update()
for name in ['Sprocket pivot -1 -1.5','Sprocket pivot -1 1.5','Road wheel pivot -1 0','Road wheel pivot -1 7','Commander cupola','Stationary cream stone base','Two chamber muzzle brake']:
 o=bpy.data.objects[name];p=world_to_camera_view(s,s.camera,o.matrix_world.translation);print(name, [round(p.x*256,1),round((1-p.y)*256,1)])

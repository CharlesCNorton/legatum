"""Update bay-horse pastern pigment in existing masters without changing motion.

Use after a material-only correction, then rerender every affected stage. The
same rule lives in build.py for clean rebuilds. Nothing is uploaded or installed.
"""
import bpy,os
from pathlib import Path
m=Path(os.environ['ANIM_ROOT'])/'masters/horseman-3d'
for path in [m/'horseman.blend',*sorted((m/'clips').glob('*.blend'))]:
 bpy.ops.wm.open_mainfile(filepath=str(path));horse=bpy.data.objects['Horse']
 assert horse.data.materials[8].name.startswith('Ivory markings')
 for p in horse.data.polygons:
  c=p.center
  if abs(c.x)>.002 and -.006<c.y<-.0028 and p.material_index!=4:p.material_index=8
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('MOUNTED_MARKINGS_READY')

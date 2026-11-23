"""A warmer, darker vertical stone rim separates the single cream disc."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for path in ['unpainted.blend','plain.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(M/path));o=bpy.data.objects['GEO-cream-stone-base'];rim=material('Cream stone warm rim C6A16B',tuple(linear(c/255) for c in (198,161,107)),rough=.88);s=rim.node_tree.nodes.get('Principled BSDF');s.inputs['Emission Color'].default_value=s.inputs['Base Color'].default_value;s.inputs['Emission Strength'].default_value=.4;o.data.materials.append(rim)
 for p in o.data.polygons:
  if abs(p.normal.z)<.5:p.material_index=len(o.data.materials)-1
 save(path)

"""Idempotent pigment-only calibration on completed masters, without reprojection."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for file in ['surface.blend','plain.blend','eagle-warrior.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(M/file))
 for mat in bpy.data.objects['GEO-cream-stone-base'].data.materials:
  rim='rim' in mat.name
  color=tuple(linear(v/255) for v in ((235,190,131) if rim else (255,225,176)))+(1,)
  n=mat.node_tree.nodes;n['Principled BSDF'].inputs['Base Color'].default_value=color
  n['Camera stone pigment'].inputs['Emission Color'].default_value=color
  for node in n:
   if node.type=='MATH' and node.operation=='MULTIPLY':node.inputs[1].default_value=.85 if rim else .90
 save(file)
print('STONE_OK',flush=True)

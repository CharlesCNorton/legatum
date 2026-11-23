"""Apply the installed Blender material/lighting skills to this task-owned master."""
import bpy,os
from pathlib import Path
M=Path(os.environ['ANIM_ROOT'])/'masters/field-cannon'
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon.blend'))
metals=('Siege aged bronze','Siege bright worn bronze','Siege dark forged iron','Siege iron arris')
fabrics=('Siege indigo wool','Siege ivory linen','Siege vermilion facings')
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 p=mat.node_tree.nodes.get('Principled BSDF')
 if not p:continue
 if mat.name.startswith(metals):
  p.inputs['Metallic'].default_value=1.0
  if mat.name.startswith('Siege aged bronze'):
   for link in list(p.inputs['Roughness'].links):mat.node_tree.links.remove(link)
   p.inputs['Roughness'].default_value=.66
 if mat.name.startswith(fabrics):
  p.inputs['Sheen Weight'].default_value=.22;p.inputs['Sheen Roughness'].default_value=.6
bpy.data.objects['Cool fill'].data.energy=130
rim=bpy.data.objects['Gold rim'];rim.data.color=(.75,.85,1.0);rim.data.energy=200
sc=bpy.context.scene;sc['finish_skills']='blender-materials: binary metal and cloth sheen; blender-lighting: subject-aimed key/fill/cool rim; preserve project camera and named anatomy'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'))
print('SIEGE_FINISH_READY')

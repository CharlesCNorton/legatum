"""Remove the painting's occluding spear from clothing/shield projection.

This is a UV shader mask, not image editing or substitute geometry. The existing
unseen-surface material fills the narrow excluded band. Actual weapon meshes keep
their painting detail. Can update packed masters/clips without changing motion.
"""
import bpy,os,hashlib
from pathlib import Path

def apply():
 count=0
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or any(k in ob.name.lower() for k in ['spear','shaft','socket']):continue
  for mat in ob.data.materials:
   if not mat or not mat.use_nodes:continue
   n=mat.node_tree.nodes;l=mat.node_tree.links
   if n.get('Exclude painted spear'):continue
   uv=next((node for node in n if node.type=='UVMAP' and node.uv_map=='Frozen painting camera'),None)
   color=next((node for node in n if node.type=='VERTEX_COLOR' and node.layer_name=='Projection weight'),None)
   if not uv or not color:continue
   # Capture existing incidence destinations before connecting the mask.
   targets=[link.to_socket for link in list(color.outputs['Color'].links)]
   sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs[0],sep.inputs[0])
   line=n.new('ShaderNodeMath');line.operation='MULTIPLY_ADD';line.inputs[1].default_value=.275;line.inputs[2].default_value=-.6508;l.new(sep.outputs['X'],line.inputs[0])
   delta=n.new('ShaderNodeMath');delta.operation='ADD';l.new(line.outputs[0],delta.inputs[0]);l.new(sep.outputs['Y'],delta.inputs[1])
   absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(delta.outputs[0],absolute.inputs[0])
   keep=n.new('ShaderNodeMath');keep.name='Exclude painted spear';keep.operation='GREATER_THAN';keep.inputs[1].default_value=.0137;l.new(absolute.outputs[0],keep.inputs[0])
   mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(color.outputs['Color'],mask.inputs[0]);l.new(keep.outputs[0],mask.inputs[1])
   for target in targets:l.new(mask.outputs[0],target)
   count+=1
 bpy.context.scene['projection_occluder_mask']='Exclude source spear band y=89.4+0.275*x at 256px, 3.5px halfwidth; fill underlying material'
 print('PROJECTION_OCCLUDER_MASK',count)

if __name__=='__main__':
 M=Path(os.environ['ANIM_ROOT'])/'masters/barbarian-spearman';source=M/'barbarian-spearman.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source));apply();bpy.ops.wm.save_as_mainfile(filepath=str(source));digest=hashlib.sha256(source.read_bytes()).hexdigest()
 for path in sorted((M/'clips').glob('*.blend')):
  bpy.ops.wm.open_mainfile(filepath=str(path));apply();bpy.context.scene['source_sha256']=digest;bpy.ops.wm.save_as_mainfile(filepath=str(path))

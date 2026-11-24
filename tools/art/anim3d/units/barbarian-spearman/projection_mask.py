"""Generated garment/shield underpainting in the frozen source spear band only."""
import bpy, os
from pathlib import Path

def apply():
 image=bpy.data.images.load(str(Path(os.environ['ANIM_ROOT'])/'assets/barbarian-spearman/cloth-underpaint-aligned.png'));image.pack()
 count=0
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or any(k in ob.name.lower() for k in ['spear','shaft','socket','anatomy','base']):continue
  for mat in ob.data.materials:
   if not mat or not mat.use_nodes:continue
   n=mat.node_tree.nodes;l=mat.node_tree.links
   if n.get('Exclude painted spear'):continue
   uv=next((node for node in n if node.type=='UVMAP' and node.uv_map=='Frozen painting camera'),None)
   pigment=n.get('Camera painted pigment')
   if not uv or not pigment:continue
   tex=next(node for node in n if node.type=='TEX_IMAGE' and node.image.name.startswith('painting-aligned'))
   sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs[0],sep.inputs[0])
   line=n.new('ShaderNodeMath');line.operation='MULTIPLY_ADD';line.inputs[1].default_value=.275;line.inputs[2].default_value=-.6508;l.new(sep.outputs['X'],line.inputs[0])
   delta=n.new('ShaderNodeMath');delta.operation='ADD';l.new(line.outputs[0],delta.inputs[0]);l.new(sep.outputs['Y'],delta.inputs[1])
   absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(delta.outputs[0],absolute.inputs[0])
   keep=n.new('ShaderNodeMapRange');keep.name='Exclude painted spear';keep.clamp=True;keep.inputs['From Min'].default_value=.010;keep.inputs['From Max'].default_value=.023;l.new(absolute.outputs[0],keep.inputs['Value'])
   fill=n.new('ShaderNodeTexImage');fill.image=image;fill.extension='CLIP';l.new(uv.outputs[0],fill.inputs[0])
   mix=n.new('ShaderNodeMixRGB');l.new(keep.outputs[0],mix.inputs[0]);l.new(fill.outputs['Color'],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],pigment.inputs['Emission Color']);count+=1
 bpy.context.scene['projection_occluder_mask']='Generated frozen garment/shield pigment in spear band, feathered 2.6-5.9px; anatomy and base excluded; unchanged source and mesh alpha'
 print('PROJECTION_OCCLUDER_MASK',count)

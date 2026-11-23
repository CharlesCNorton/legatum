"""Fill the independently moving spear's narrow source band in frozen texture space.

Sample adjacent painted surface pigment above/below the shaft; do not change
mesh alpha, edit the source raster, or project from the animated camera.
"""
import bpy

def apply():
 count=0
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or any(k in ob.name.lower() for k in ['spear','shaft','socket']):continue
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
   keep=n.new('ShaderNodeMapRange');keep.name='Exclude painted spear';keep.clamp=True;keep.inputs['From Min'].default_value=.010;keep.inputs['From Max'].default_value=.018;l.new(absolute.outputs[0],keep.inputs['Value'])
   samples=[]
   for offset in [-.024,.024]:
    shift=n.new('ShaderNodeVectorMath');shift.operation='ADD';shift.inputs[1].default_value=(0,offset,0);l.new(uv.outputs[0],shift.inputs[0])
    sample=n.new('ShaderNodeTexImage');sample.image=tex.image;sample.extension='CLIP';l.new(shift.outputs[0],sample.inputs[0]);samples.append(sample)
   mean=n.new('ShaderNodeMixRGB');mean.inputs[0].default_value=.5;l.new(samples[0].outputs['Color'],mean.inputs[1]);l.new(samples[1].outputs['Color'],mean.inputs[2])
   mix=n.new('ShaderNodeMixRGB');l.new(keep.outputs[0],mix.inputs[0]);l.new(mean.outputs[0],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],pigment.inputs['Emission Color']);count+=1
 bpy.context.scene['projection_occluder_mask']='Spear band: adjacent frozen pigment samples, feathered 2.6-4.6px; unchanged source and mesh alpha'
 print('PROJECTION_OCCLUDER_MASK',count)

"""Painted hidden pigments and a clean registered stone plate on solid geometry."""
import bpy
from bpy_extras.object_utils import world_to_camera_view

for mat,file,dark,light in [
    (skin,'fill-skin.png',(.25,.12,.055,1),(.76,.49,.29,1)),
    (linen,'fill-linen.png',(.28,.20,.11,1),(.78,.63,.43,1)),
    (wool,'fill-linen.png',(.055,.028,.013,1),(.27,.15,.074,1)),
    (olive,'fill-linen.png',(.065,.06,.026,1),(.27,.24,.12,1)),
    (leather,'fill-leather.png',(.035,.016,.007,1),(.30,.15,.065,1)),
]:
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    coord=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/file),check_existing=True)
    tex.projection='BOX';tex.projection_blend=.4;l.new(coord.outputs['Generated'],tex.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.025;ramp.color_ramp.elements[0].color=dark
    ramp.color_ramp.elements[1].position=.65 if mat!=leather else .24;ramp.color_ramp.elements[1].color=light
    l.new(tex.outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Base Color'])
    mat['painted_fill']=file

# Stone texture coordinates are frozen on the actual finished disc. Generated
# pixels color its top only; original rim pigment is retained where unoccluded.
uv=base.data.uv_layers.new(name='Clean stone fixed UV')
for loop in base.data.loops:
    q=world_to_camera_view(sc,sc.camera,base.matrix_world@base.data.vertices[loop.vertex_index].co)
    uv.data[loop.index].uv=(q.x,q.y)
n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'stone-plate.png'));tex.extension='EXTEND';l.new(coord.outputs[0],tex.inputs[0])
original=n.new('ShaderNodeTexImage');original.image=bpy.data.images.load(str(A/'painting-aligned.png'));original.extension='EXTEND';l.new(coord.outputs[0],original.inputs[0])
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
mask=n.new('ShaderNodeMath');mask.operation='GREATER_THAN';mask.inputs[1].default_value=.7;l.new(sep.outputs['Z'],mask.inputs[0])
color=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],color.inputs[0]);l.new(original.outputs[0],color.inputs[1]);l.new(tex.outputs[0],color.inputs[2])
# The raster alpha never controls opacity or silhouette. Edge samples fall back
# to warm pigment so texture registration cannot make a black ring.
a=n.new('ShaderNodeMixRGB');a.inputs[1].default_value=(.85,.62,.38,1);l.new(tex.outputs['Alpha'],a.inputs[0]);l.new(color.outputs[0],a.inputs[2])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.5;l.new(a.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera stone pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0;pigment.inputs['Emission Strength'].default_value=1;l.new(shade.outputs[0],pigment.inputs['Emission Color'])
ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.97;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])

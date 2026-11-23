"""Registered stone pigment on a closed beveled disc, with live contact AO."""
import bpy
from bpy_extras.object_utils import world_to_camera_view
from common import ASSET


def finish_stone(scene):
    obj = bpy.data.objects['GEO-Stationary cream base']
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    uv = obj.data.uv_layers.new(name='StonePaintingUV')
    points = [world_to_camera_view(scene, scene.camera, obj.matrix_world @ v.co)
              for v in obj.data.vertices]
    # Match the source disc's measured image bounds, keeping actual solid geometry.
    left, right = min(p.x for p in points), max(p.x for p in points)
    bottom, top = min(p.y for p in points), max(p.y for p in points)
    for loop in obj.data.loops:
        p = points[loop.vertex_index]
        uv.data[loop.index].uv = ((p.x-left)/(right-left), (p.y-bottom)/(top-bottom))
    material = obj.data.materials[0].copy()
    obj.data.materials[0] = material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    image = bpy.data.images.load(str(ASSET/'stone-pigment.png')); image.pack()
    tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.extension = 'EXTEND'
    coord = nodes.new('ShaderNodeUVMap'); coord.uv_map = uv.name
    links.new(coord.outputs[0], tex.inputs[0])
    ao = nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .12
    multiply = nodes.new('ShaderNodeMixRGB'); multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = .68
    links.new(tex.outputs['Color'], multiply.inputs[1]); links.new(ao.outputs['AO'], multiply.inputs[2])
    pigment = nodes.new('ShaderNodeBsdfPrincipled'); pigment.label = 'Stone pigment with live contact'
    pigment.inputs['Base Color'].default_value = (0,0,0,1)
    pigment.inputs['Specular IOR Level'].default_value = 0
    pigment.inputs['Emission Strength'].default_value = 1
    links.new(multiply.outputs[0], pigment.inputs['Emission Color'])
    light = nodes.new('ShaderNodeLightPath'); blend = nodes.new('ShaderNodeMixShader')
    links.new(light.outputs['Is Camera Ray'], blend.inputs[0])
    links.new(bsdf.outputs[0], blend.inputs[1]); links.new(pigment.outputs[0], blend.inputs[2])
    links.new(blend.outputs[0], nodes.get('Material Output').inputs['Surface'])
    obj['pigment_source'] = 'generated occlusion fill, original rim; opaque solid geometry'

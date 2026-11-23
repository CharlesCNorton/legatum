"""Clean image-generated pigment on a solid stone disc, with live contact AO."""
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view


def finish_stone():
    scene = bpy.context.scene
    obj = bpy.data.objects['GEO-cream-stone-base']
    uv = obj.data.uv_layers.new(name='CleanStoneCamera')
    for loop in obj.data.loops:
        p = world_to_camera_view(scene, scene.camera,
                                 obj.matrix_world @ obj.data.vertices[loop.vertex_index].co)
        uv.data[loop.index].uv = (p.x, p.y)
    material = obj.active_material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.get('Material Output')
    physical = nodes.get('Principled BSDF')
    coords = nodes.new('ShaderNodeUVMap')
    coords.uv_map = uv.name
    textures = []
    for name in ['stone-fill-aligned.png', 'painting-aligned.png']:
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(Path(os.environ['ANIM_ROOT']) / 'assets/pikeman' / name))
        links.new(coords.outputs[0], tex.inputs['Vector'])
        # Texture alpha blends pigment only, never geometry coverage. A small
        # registration overhang must stay cream instead of sampling black RGB.
        color = nodes.new('ShaderNodeMixRGB')
        color.inputs[1].default_value = (.72, .51, .29, 1)
        links.new(tex.outputs['Alpha'], color.inputs[0])
        links.new(tex.outputs['Color'], color.inputs[2])
        textures.append(color)
    xy = nodes.new('ShaderNodeSeparateXYZ')
    links.new(coords.outputs[0], xy.inputs[0])
    lower_rim = nodes.new('ShaderNodeMath')
    lower_rim.operation = 'LESS_THAN'
    lower_rim.inputs[1].default_value = 1 - 227 / 256
    links.new(xy.outputs['Y'], lower_rim.inputs[0])
    pigment = nodes.new('ShaderNodeMixRGB')
    links.new(lower_rim.outputs[0], pigment.inputs[0])
    links.new(textures[0].outputs[0], pigment.inputs[1])
    links.new(textures[1].outputs[0], pigment.inputs[2])
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = .055
    contact = nodes.new('ShaderNodeMixRGB')
    contact.blend_type = 'MULTIPLY'
    contact.inputs[0].default_value = .36
    links.new(pigment.outputs[0], contact.inputs[1])
    links.new(ao.outputs['Color'], contact.inputs[2])
    paint = nodes.new('ShaderNodeEmission')
    paint.name = 'Clean stone pigment with live contact'
    links.new(contact.outputs[0], paint.inputs['Color'])
    path = nodes.new('ShaderNodeLightPath')
    weight = nodes.new('ShaderNodeMath')
    weight.operation = 'MULTIPLY'
    weight.inputs[1].default_value = .96
    links.new(path.outputs['Is Camera Ray'], weight.inputs[0])
    mix = nodes.new('ShaderNodeMixShader')
    links.new(weight.outputs[0], mix.inputs[0])
    links.new(physical.outputs[0], mix.inputs[1])
    links.new(paint.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    obj['stone_pigment'] = 'Generated clean top; original unobstructed lower rim; dynamic AO'

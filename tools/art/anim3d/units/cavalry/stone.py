"""Generated occlusion pigment on the actual beveled stone, with live contact AO."""
import bpy
from bpy_extras.object_utils import world_to_camera_view


def stone_pigment(scene, assets):
    ob = bpy.data.objects['Stationary cream stone']
    # Match original token disc bounds, while retaining a physical solid disc.
    from mathutils import Vector
    right = scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    ob.location += right*.022
    ob.scale.x *= .975
    ob.scale.y *= .975
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = ob
    for mod in list(ob.modifiers):
        if mod.type == 'BEVEL':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    uv = ob.data.uv_layers.new(name='Registered stone pigment')
    for i, loop in enumerate(ob.data.loops):
        q = world_to_camera_view(scene, scene.camera, ob.matrix_world @ ob.data.vertices[loop.vertex_index].co)
        uv.data[i].uv = (q.x, q.y)
    mat = ob.data.materials[0]
    n, links = mat.node_tree.nodes, mat.node_tree.links
    shader = n.get('Principled BSDF')
    tex = n.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(assets/'stone-pigment.png'), check_existing=True)
    tex.extension = 'EXTEND'
    coord = n.new('ShaderNodeUVMap'); coord.uv_map = uv.name
    links.new(coord.outputs[0], tex.inputs['Vector'])
    # Paint carries broad illumination; AO supplies new moving hoof shadows.
    ao = n.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .16
    ao.inputs['Color'].default_value = (1, 1, 1, 1)
    shade = n.new('ShaderNodeMixRGB'); shade.blend_type = 'MULTIPLY'; shade.inputs[0].default_value = .75
    links.new(tex.outputs['Color'], shade.inputs[1]); links.new(ao.outputs['Color'], shade.inputs[2])
    pigment = n.new('ShaderNodeEmission'); links.new(shade.outputs[0], pigment.inputs['Color'])
    ray = n.new('ShaderNodeLightPath')
    blend = n.new('ShaderNodeMixShader')
    links.new(ray.outputs['Is Camera Ray'], blend.inputs[0])
    links.new(shader.outputs[0], blend.inputs[1]); links.new(pigment.outputs[0], blend.inputs[2])
    links.new(blend.outputs[0], n.get('Material Output').inputs['Surface'])

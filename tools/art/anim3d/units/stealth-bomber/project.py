"""Frozen finished-surface UVs; camera-only paint never lights adjacent geometry."""
import bpy
from bpy_extras.object_utils import world_to_camera_view


def apply_projection(scene, camera, assets, front):
    texture = bpy.data.images.load(str(assets / 'projection.png'))
    fill = bpy.data.images.load(str(assets / 'painted-fill.png'))
    source_mask = bpy.data.images.load(str(assets / 'projection-mask.png'))
    source_mask.colorspace_settings.name = 'Non-Color'
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or 'bomb-' in ob.name or 'prop blade' in ob.name:
            continue
        old = ob.data.materials[0]
        mat = old.copy()
        mat.name = ob.name + ' painted'
        ob.data.materials[0] = mat
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        physical = nodes.get('Principled BSDF')
        output = nodes.get('Material Output')
        physical.inputs['Emission Strength'].default_value = 0
        pigment = nodes.new('ShaderNodeEmission')
        pigment.name = 'Camera pigment'
        mix_shader = nodes.new('ShaderNodeMixShader')
        camera_ray = nodes.new('ShaderNodeLightPath')
        strength = nodes.new('ShaderNodeMath')
        strength.operation = 'MULTIPLY'
        strength.inputs[1].default_value = .94
        links.new(camera_ray.outputs['Is Camera Ray'], strength.inputs[0])
        links.new(strength.outputs[0], mix_shader.inputs[0])
        links.new(physical.outputs[0], mix_shader.inputs[1])
        links.new(pigment.outputs[0], mix_shader.inputs[2])
        links.new(mix_shader.outputs[0], output.inputs['Surface'])
        is_stone = ob.name == 'GEO-stationary cream base'
        if is_stone or 'support' in ob.name:
            strength.inputs[1].default_value = .985
        uv = ob.data.uv_layers.new(name='RestPainting')
        weights = ob.data.color_attributes.new(name='Facing', type='FLOAT_COLOR', domain='CORNER')
        normal = ob.matrix_world.to_3x3().inverted().transposed()
        for loop in ob.data.loops:
            vert = ob.data.vertices[loop.vertex_index]
            world = ob.matrix_world @ vert.co
            q = world_to_camera_view(scene, camera, world)
            uv.data[loop.index].uv = (q.x, q.y)
            weight = max(0, min(1, ((normal @ vert.normal).normalized().dot(front) - .001) / .06))
            if weight and not is_stone:
                hit, loc, _, _, hit_ob, _ = scene.ray_cast(deps, world + front * 20, -front, distance=20.01)
                if hit and hit_ob != ob and (loc - world).length > .015:
                    weight = 0
            weights.data[loop.index].color = (weight, weight, weight, 1)
        uvnode = nodes.new('ShaderNodeUVMap')
        uvnode.uv_map = 'RestPainting'
        image = nodes.new('ShaderNodeTexImage')
        image.image = bpy.data.images.load(str(assets / 'stone-projection.png')) if is_stone else texture
        image.extension = 'CLIP'
        links.new(uvnode.outputs[0], image.inputs[0])
        facing = nodes.new('ShaderNodeVertexColor')
        facing.layer_name = 'Facing'
        factor = nodes.new('ShaderNodeMath')
        factor.operation = 'MULTIPLY'
        links.new(facing.outputs['Color'], factor.inputs[0])
        mask_image = nodes.new('ShaderNodeTexImage')
        mask_image.image = source_mask
        links.new(uvnode.outputs[0], mask_image.inputs[0])
        coverage = nodes.new('ShaderNodeMath')
        coverage.operation = 'MULTIPLY'
        links.new(image.outputs['Alpha'], coverage.inputs[0])
        links.new(mask_image.outputs['Color'], coverage.inputs[1])
        links.new(coverage.outputs[0], factor.inputs[1])
        mix = nodes.new('ShaderNodeMixRGB')
        links.new(factor.outputs[0], mix.inputs[0])
        mix.inputs[1].default_value = old.diffuse_color
        if 'composite' in old.name:
            tx = nodes.new('ShaderNodeTexImage')
            tx.image = fill
            tx.projection = 'BOX'
            tx.projection_blend = .3
            coord = nodes.new('ShaderNodeTexCoord')
            links.new(coord.outputs['Generated'], tx.inputs[0])
            links.new(tx.outputs['Color'], mix.inputs[1])
        links.new(image.outputs['Color'], mix.inputs[2])
        color = mix.outputs[0]
        if is_stone:
            # Live local contact, with no painted ghost of the upright support.
            ao = nodes.new('ShaderNodeAmbientOcclusion')
            ao.inputs['Distance'].default_value = .16
            shade = nodes.new('ShaderNodeMixRGB')
            shade.blend_type = 'MULTIPLY'
            shade.inputs[0].default_value = .22
            links.new(color, shade.inputs[1])
            links.new(ao.outputs['Color'], shade.inputs[2])
            color = shade.outputs[0]
        links.new(color, physical.inputs['Base Color'])
        links.new(color, pigment.inputs['Color'])
        ob['projection'] = 'finished surface, frozen UV, facing and visibility masked'

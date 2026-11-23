"""Frozen finished-surface UVs; camera-only paint never lights adjacent geometry."""
import bpy
from bpy_extras.object_utils import world_to_camera_view


def apply_projection(scene, camera, assets, front):
    texture = bpy.data.images.load(str(assets / 'projection.png'))
    fill = bpy.data.images.load(str(assets / 'painted-fill.png'))
    occluded = bpy.data.images.load(str(assets / 'occlusion-fill.png'))
    source_mask = bpy.data.images.load(str(assets / 'projection-mask.png'))
    source_mask.colorspace_settings.name = 'Non-Color'
    stone_mask = bpy.data.images.load(str(assets / 'stone-mask.png'))
    stone_mask.colorspace_settings.name = 'Non-Color'
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or 'bomb-' in ob.name:
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
        is_base = ob.name == 'GEO-stationary cream base'
        stone_color = None
        if is_base:
            # Frozen paint only on the exposed rim and outer top. The missing
            # support footprint stays clean and receives live contact shading.
            strength.inputs[1].default_value = .94
            geom = nodes.new('ShaderNodeNewGeometry')
            xyz = nodes.new('ShaderNodeSeparateXYZ')
            links.new(geom.outputs['Normal'], xyz.inputs[0])
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position = .05
            ramp.color_ramp.elements[0].color = (.70, .49, .25, 1)
            ramp.color_ramp.elements[1].position = .75
            ramp.color_ramp.elements[1].color = (.92, .73, .46, 1)
            links.new(xyz.outputs['Z'], ramp.inputs[0])
            ao = nodes.new('ShaderNodeAmbientOcclusion')
            ao.inputs['Distance'].default_value = .35
            shade = nodes.new('ShaderNodeMixRGB')
            shade.blend_type = 'MULTIPLY'
            shade.inputs[0].default_value = .32
            grain = nodes.new('ShaderNodeTexNoise')
            grain.inputs['Scale'].default_value = 75
            grain_mix = nodes.new('ShaderNodeMixRGB')
            grain_mix.blend_type = 'MULTIPLY'
            grain_mix.inputs[0].default_value = .09
            links.new(ramp.outputs['Color'], grain_mix.inputs[1])
            links.new(grain.outputs['Fac'], grain_mix.inputs[2])
            links.new(grain_mix.outputs[0], shade.inputs[1])
            links.new(ao.outputs['Color'], shade.inputs[2])
            stone_color = grain_mix.outputs[0]
        uv = ob.data.uv_layers.new(name='RestPainting')
        weights = ob.data.color_attributes.new(name='Facing', type='FLOAT_COLOR', domain='CORNER')
        normal = ob.matrix_world.to_3x3().inverted().transposed()
        for loop in ob.data.loops:
            vert = ob.data.vertices[loop.vertex_index]
            world = ob.matrix_world @ vert.co
            q = world_to_camera_view(scene, camera, world)
            uv.data[loop.index].uv = (q.x, q.y)
            weight = max(0, min(1, ((normal @ vert.normal).normalized().dot(front) - .001) / .06))
            # Convex glazing and small mechanical parts overlap their real
            # frames/hubs. Vertex ray masks there smear the occluder's boundary
            # across a whole face, producing blue/white bands in visible paint.
            attached = any(name in ob.name for name in
                           ('glazing','cockpit','dorsal turret','spinner','prop blade','silver cowl'))
            if weight and not is_base and not attached:
                hit, loc, _, _, hit_ob, _ = scene.ray_cast(deps, world + front * 20, -front, distance=20.01)
                if hit and hit_ob != ob and (loc - world).length > .015:
                    weight = 0
            weights.data[loop.index].color = (weight, weight, weight, 1)
        uvnode = nodes.new('ShaderNodeUVMap')
        uvnode.uv_map = 'RestPainting'
        image = nodes.new('ShaderNodeTexImage')
        image.image = texture
        image.extension = 'CLIP'
        links.new(uvnode.outputs[0], image.inputs[0])
        paint_color = image.outputs['Color']
        paint_alpha = image.outputs['Alpha']
        facing = nodes.new('ShaderNodeVertexColor')
        facing.layer_name = 'Facing'
        factor = nodes.new('ShaderNodeMath')
        factor.operation = 'MULTIPLY'
        links.new(facing.outputs['Color'], factor.inputs[0])
        mask_image = nodes.new('ShaderNodeTexImage')
        mask_image.image = stone_mask if is_base else source_mask
        links.new(uvnode.outputs[0], mask_image.inputs[0])
        coverage = nodes.new('ShaderNodeMath')
        coverage.operation = 'MULTIPLY'
        if not is_base and 'prop blade' not in ob.name:
            hidden = nodes.new('ShaderNodeTexImage')
            hidden.image = occluded
            hidden.extension = 'CLIP'
            links.new(uvnode.outputs[0], hidden.inputs[0])
            # Use generated pixels only where the original rotating blade was
            # removed. Original source paint remains the authority elsewhere.
            merged = nodes.new('ShaderNodeMixRGB')
            links.new(mask_image.outputs['Color'], merged.inputs[0])
            links.new(hidden.outputs['Color'], merged.inputs[1])
            links.new(paint_color, merged.inputs[2])
            alpha = nodes.new('ShaderNodeMixRGB')
            links.new(mask_image.outputs['Color'], alpha.inputs[0])
            links.new(hidden.outputs['Alpha'], alpha.inputs[1])
            links.new(paint_alpha, alpha.inputs[2])
            paint_color, paint_alpha = merged.outputs[0], alpha.outputs[0]
        links.new(paint_alpha, coverage.inputs[0])
        if not is_base:
            coverage.inputs[1].default_value = 1
        else:
            links.new(mask_image.outputs['Color'], coverage.inputs[1])
        links.new(coverage.outputs[0], factor.inputs[1])
        mix = nodes.new('ShaderNodeMixRGB')
        links.new(factor.outputs[0], mix.inputs[0])
        mix.inputs[1].default_value = old.diffuse_color
        if stone_color:
            links.new(stone_color, mix.inputs[1])
        if 'olive' in old.name:
            tx = nodes.new('ShaderNodeTexImage')
            tx.image = fill
            tx.projection = 'BOX'
            tx.projection_blend = .3
            coord = nodes.new('ShaderNodeTexCoord')
            links.new(coord.outputs['Generated'], tx.inputs[0])
            links.new(tx.outputs['Color'], mix.inputs[1])
        links.new(paint_color, mix.inputs[2])
        color = mix.outputs[0]
        if is_base:
            links.new(color, shade.inputs[1])
            color = shade.outputs[0]
        links.new(color, physical.inputs['Base Color'])
        links.new(color, pigment.inputs['Color'])
        ob['projection'] = ('masked stone rim, clean support footprint, live AO' if is_base
                            else 'finished surface, frozen UV, facing and visibility masked')

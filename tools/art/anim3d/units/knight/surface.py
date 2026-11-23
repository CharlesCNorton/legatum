"""Finish painted surfaces before UV capture; keep the live skinning rig."""
import bpy


def finish(objects):
    records = []
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type == 'CURVE':
            bpy.ops.object.convert(target='MESH')
        if obj.data.shape_keys:
            mixed = obj.shape_key_add(name='Frozen static anatomy', from_mix=True)
            coords = [v.co.copy() for v in mixed.data]
            obj.shape_key_clear()
            for v, co in zip(obj.data.vertices, coords):
                v.co = co
        arms = [(m, m.show_viewport, m.show_render) for m in obj.modifiers
                if m.type == 'ARMATURE']
        for m, _, _ in arms:
            m.show_viewport = m.show_render = False
        applied = []
        for m in list(obj.modifiers):
            if m.type == 'ARMATURE' or not m.show_viewport:
                continue
            # Native human topology is retained for inverse-skin fitting.
            if m.type == 'SUBSURF' and obj.name == 'Rider MPFB CC0 anatomy':
                continue
            if m.type == 'SUBSURF':
                m.levels = m.render_levels
                if not m.levels:
                    obj.modifiers.remove(m)
                    continue
            applied.append(m.type)
            bpy.ops.object.modifier_apply(modifier=m.name)
        for m, viewport, render in arms:
            m.show_viewport, m.show_render = viewport, render
        records.append({'object': obj.name, 'vertices': len(obj.data.vertices),
                        'applied': applied})
    bpy.context.view_layer.update()
    return records


def pigment(nodes, links, physical, colour, factor):
    """Painted illumination is visible to camera rays, never a scene lamp."""
    emission = nodes.new('ShaderNodeEmission')
    emission.label = 'Original painted illumination'
    links.new(colour, emission.inputs['Color'])
    ray = nodes.new('ShaderNodeLightPath')
    mask = nodes.new('ShaderNodeMath')
    mask.operation = 'MULTIPLY'
    links.new(ray.outputs['Is Camera Ray'], mask.inputs[0])
    links.new(factor, mask.inputs[1])
    mix = nodes.new('ShaderNodeMixShader')
    mix.label = 'Camera-only painting; physical shadows'
    links.new(mask.outputs[0], mix.inputs[0])
    links.new(physical, mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    return mix.outputs[0]

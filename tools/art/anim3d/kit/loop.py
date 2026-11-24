"""Periodic residual correction on a baked cloth mesh, after the simulation.

The captured skeleton is untouched. Keep the first pose and subtract the
cloth's one-cycle drift with a smooth endpoint envelope. UVs, weights and
topology survive; the result remains real geometry in every render path.
"""
import bpy


def close_cloth_loop(scene, ob, start, end):
    assert end > start
    cloth = next(m for m in ob.modifiers if m.type == 'CLOTH')
    assert cloth.point_cache.is_baked, 'Close loops only after cloth baking'
    assert ob.modifiers.get('Periodic cloth closure') is None, 'Rebuild from the clean master'
    index = list(ob.modifiers).index(cloth)+1
    later = [(m, m.show_viewport) for m in list(ob.modifiers)[index:]]
    try:
        for m, _ in later:
            m.show_viewport = False
        def points(frame):
            scene.frame_set(frame)
            ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = ev.to_mesh()
            try:
                return [ev.matrix_world @ v.co for v in mesh.vertices]
            finally:
                ev.to_mesh_clear()
        first, last = points(start), points(end)
        assert len(first) == len(last) == len(ob.data.vertices)
        inverse = ob.matrix_world.inverted().to_3x3()
        offsets = [inverse @ (a-b) for a, b in zip(first, last)]
    finally:
        for m, visible in later:
            m.show_viewport = visible
    attribute = ob.data.attributes.new('Periodic cloth offset', 'FLOAT_VECTOR', 'POINT')
    for value, offset in zip(attribute.data, offsets):
        value.vector = offset
    group = bpy.data.node_groups.new('Periodic baked cloth', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    source = group.nodes.new('NodeGroupInput')
    output = group.nodes.new('NodeGroupOutput')
    named = group.nodes.new('GeometryNodeInputNamedAttribute')
    named.data_type = 'FLOAT_VECTOR'
    named.inputs['Name'].default_value = attribute.name
    scale = group.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    scale.inputs['Scale'].default_value = 0
    scale.inputs['Scale'].keyframe_insert('default_value', frame=start)
    scale.inputs['Scale'].default_value = 1
    scale.inputs['Scale'].keyframe_insert('default_value', frame=end)
    # Zero endpoint slope: close the residual without a correction impulse.
    for layer in group.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'BEZIER'
                        key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'
    position = group.nodes.new('GeometryNodeSetPosition')
    group.links.new(source.outputs['Geometry'], position.inputs['Geometry'])
    group.links.new(named.outputs['Attribute'], scale.inputs[0])
    group.links.new(scale.outputs['Vector'], position.inputs['Offset'])
    group.links.new(position.outputs['Geometry'], output.inputs['Geometry'])
    modifier = ob.modifiers.new('Periodic cloth closure', 'NODES')
    modifier.node_group = group
    ob.modifiers.move(len(ob.modifiers)-1, index)
    scene.frame_set(start)
    bpy.context.view_layer.update()
    return {'start': start, 'end': end, 'vertices': len(offsets),
            'max_correction_m': max(v.length for v in offsets),
            'method': 'post-cloth periodic residual, smooth endpoint envelope'}

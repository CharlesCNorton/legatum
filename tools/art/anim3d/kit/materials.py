"""Keep unseen painted fills readable under the projection's display transform."""


def painted_fill(nodes, links, physical, colour, amount=.65):
    """Camera-only pigment with live AO; physical rays still see the old BSDF.

    The input is the existing generated fill or original MPFB skin texture,
    never the projected figure. This keeps backsides coherent in raised-arm
    and fallen poses without painting through the body or adding a billboard.
    """
    import bpy
    shade = nodes.new('ShaderNodeGroup')
    shade.node_tree = painterly_group()
    shade.inputs[0].default_value = .65
    links.new(colour, shade.inputs[1])
    pigment = nodes.new('ShaderNodeEmission')
    pigment.label = 'Generated fill pigment, camera only'
    links.new(shade.outputs['Color'], pigment.inputs['Color'])
    ray = nodes.new('ShaderNodeLightPath')
    factor = nodes.new('ShaderNodeMath')
    factor.operation = 'MULTIPLY'
    factor.inputs[1].default_value = amount
    links.new(ray.outputs['Is Camera Ray'], factor.inputs[0])
    blend = nodes.new('ShaderNodeMixShader')
    blend.label = 'Painted unseen surface with physical response'
    links.new(factor.outputs[0], blend.inputs[0])
    links.new(physical, blend.inputs[1])
    links.new(pigment.outputs[0], blend.inputs[2])
    return blend.outputs[0]


def painterly_group():
    """Shared Cycles pigment/cavity group; camera gating remains outside it.

    Input order is stable for existing per-material seam and coverage edits.
    This preserves the established appearance; it is not the Eevee ramp shader.
    """
    import bpy
    name = 'Legatum painterly cavity pigment v1'
    group = bpy.data.node_groups.get(name)
    if group:
        return group
    group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    for name, kind, default in [('Cavity amount', 'NodeSocketFloat', .65),
                                 ('Pigment', 'NodeSocketColor', (.5,.5,.5,1))]:
        socket = group.interface.new_socket(name=name, in_out='INPUT', socket_type=kind)
        socket.default_value = default
    group.interface.new_socket(name='Color', in_out='OUTPUT', socket_type='NodeSocketColor')
    n, links = group.nodes, group.links
    incoming = n.new('NodeGroupInput'); outgoing = n.new('NodeGroupOutput')
    ao = n.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .08; ao.samples = 8
    multiply = n.new('ShaderNodeMixRGB'); multiply.blend_type = 'MULTIPLY'
    links.new(incoming.outputs[0], multiply.inputs[0]); links.new(incoming.outputs[1], multiply.inputs[1])
    links.new(ao.outputs['Color'], multiply.inputs[2]); links.new(multiply.outputs[0], outgoing.inputs['Color'])
    return group

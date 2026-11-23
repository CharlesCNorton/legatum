"""Keep unseen painted fills readable under the projection's display transform."""


def painted_fill(nodes, links, physical, colour, amount=.65):
    """Camera-only pigment with live AO; physical rays still see the old BSDF.

    The input is the existing generated fill or original MPFB skin texture,
    never the projected figure. This keeps backsides coherent in raised-arm
    and fallen poses without painting through the body or adding a billboard.
    """
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.label = 'Live cavities on unseen painted surfaces'
    ao.inputs['Distance'].default_value = .08
    ao.samples = 8
    shade = nodes.new('ShaderNodeMixRGB')
    shade.blend_type = 'MULTIPLY'
    shade.inputs[0].default_value = .65
    links.new(colour, shade.inputs[1])
    links.new(ao.outputs['Color'], shade.inputs[2])
    pigment = nodes.new('ShaderNodeEmission')
    pigment.label = 'Generated fill pigment, camera only'
    links.new(shade.outputs[0], pigment.inputs['Color'])
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

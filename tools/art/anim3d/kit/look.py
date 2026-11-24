"""Eevee node helpers for the painted look: emission only, light as a value.

The look is applied at render time to a master or clip opened read-only:
materials and lights are replaced, nothing is saved, and geometry, weights,
UVs, cloth caches, actions and the camera are untouched. That keeps look work
independent of form and motion work.

Mechanisms, each of which cost the Spearman look lane a round to find:
- A sun of strength 1 returns 1/pi on white diffuse in Eevee. Use pi to get 1.0.
- An unlinked Normal socket ignores `default_value` and means "geometry
  normal". Link a Combine XYZ to feed a constant.
- A diffuse BSDF whose normal is the key direction is fully lit unless
  something blocks the light: Shader to RGB of it is a cast-shadow-only term.
  Use it to let shadows travel over projected paint without relighting form
  the painting already contains.
- ColorRamp elements re-sort when a position is assigned in place. Remove all
  but one and add the rest in order.
- Shader to RGB is Eevee-only: run with `--gpu-backend metal` through the gate.

Graph is copied from units/spearman/look.py on fable/unit-anim-3d-spearman-a
(239540b5), where it rendered the art director's preferred materials on
2026-11-24 (rest plus 40 frames in about 55 s). NOT YET RUN FROM THE KIT.
"""
import math

import bpy

SUN_STRENGTH = math.pi


class Graph:
    """Small node-graph builder on one material; replaces whatever was there."""

    def __init__(self, material):
        material.use_nodes = True
        self.tree = material.node_tree
        self.tree.nodes.clear()
        self.n, self.l = self.tree.nodes, self.tree.links

    def node(self, kind, **props):
        node = self.n.new(kind)
        for key, value in props.items():
            setattr(node, key, value)
        return node

    def math(self, op, a, b=None, c=None, clamp=False):
        node = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for socket, value in zip(node.inputs, (a, b, c)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                self.l.new(value, socket)
        return node.outputs[0]

    def mix(self, factor, a, b, blend='MIX'):
        node = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=True)
        for socket, value in ((node.inputs[0], factor), (node.inputs[6], a), (node.inputs[7], b)):
            if isinstance(value, (int, float, tuple)):
                socket.default_value = value
            else:
                self.l.new(value, socket)
        return node.outputs[2]

    def dot(self, vector, constant):
        node = self.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        self.l.new(vector, node.inputs[0])
        node.inputs[1].default_value = constant
        return node.outputs['Value']

    def image(self, path, vector, colourspace='sRGB', extension='EXTEND'):
        node = self.node('ShaderNodeTexImage', extension=extension, interpolation='Cubic')
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.image.colorspace_settings.name = colourspace
        self.l.new(vector, node.inputs['Vector'])
        return node

    def ramp(self, factor, stops, interpolation='EASE'):
        """`stops` is [(position, linear RGBA), ...] in increasing position."""
        node = self.node('ShaderNodeValToRGB')
        ramp = node.color_ramp
        ramp.interpolation = interpolation
        while len(ramp.elements) > 1:
            ramp.elements.remove(ramp.elements[-1])
        ramp.elements[0].position, ramp.elements[0].color = stops[0]
        for position, colour in stops[1:]:
            ramp.elements.new(position).color = colour
        self.l.new(factor, node.inputs['Fac'])
        return node.outputs['Color']

    def lit(self, normal=None, constant_normal=None):
        """White diffuse -> Shader to RGB -> value: the key light's response.

        With `constant_normal` set to the direction toward the key, the result
        is 1 in light and falls only where a shadow is cast.
        """
        diffuse = self.node('ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
        if constant_normal is not None:
            vector = self.node('ShaderNodeCombineXYZ')
            for socket, value in zip(vector.inputs, constant_normal):
                socket.default_value = value
            self.l.new(vector.outputs[0], diffuse.inputs['Normal'])
        elif normal is not None:
            self.l.new(normal, diffuse.inputs['Normal'])
        to_rgb = self.node('ShaderNodeShaderToRGB')
        self.l.new(diffuse.outputs[0], to_rgb.inputs[0])
        bw = self.node('ShaderNodeRGBToBW')
        self.l.new(to_rgb.outputs['Color'], bw.inputs[0])
        return bw.outputs[0]

    def emit(self, colour):
        emission = self.node('ShaderNodeEmission')
        self.l.new(colour, emission.inputs['Color'])
        output = self.node('ShaderNodeOutputMaterial')
        self.l.new(emission.outputs[0], output.inputs['Surface'])


def linear(c):
    return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4


def ramp_stops(palette):
    """kit.part_paint.palette output -> stops for Graph.ramp (linear RGBA)."""
    return [(position, tuple(linear(v/255) for v in colour)+(1,))
            for position, colour in zip(palette['positions'], palette['colours'])]


def key_sun(scene, direction, angle_degrees=24.0, name='Painted key'):
    """One sun whose light travels along -`direction` (a world-space vector
    pointing from the subject toward the light). Strength pi: white diffuse
    facing it returns 1.0 through Shader to RGB.
    """
    from mathutils import Vector
    data = bpy.data.lights.new(name, 'SUN')
    data.energy = SUN_STRENGTH
    data.angle = math.radians(angle_degrees)
    sun = bpy.data.objects.new(name, data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
    return sun

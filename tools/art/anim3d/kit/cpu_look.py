"""Explicit CPU diagnostic for an Eevee painted graph, never a final renderer.

Shader-to-RGB has no Cycles equivalent. Substitute the geometric sun cosine;
keep real AO, frozen UVs and pigment. Cast shadows are absent. Always label
this proxy and recheck the final Eevee output on the host.
"""
from .look import Graph


def graph_for_sun(direction):
    class CPUProxy(Graph):
        def lit(self, normal=None, constant_normal=None):
            if constant_normal is not None:
                return self.math('ADD', 1., 0.)
            normal = normal or self.node('ShaderNodeNewGeometry').outputs['Normal']
            return self.math('MAXIMUM', self.dot(normal, tuple(direction)), 0.)
    return CPUProxy

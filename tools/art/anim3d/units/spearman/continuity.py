"""Render-time sewn-surface pigment; masks are frozen in undeformed mesh space.

No re-projection, new UVs, per-frame fitting, geometry or pose changes. The
channels describe actual sole undersides, inward skirt faces and rear shoulder
cloth. Visible hero paint stays intact except the real leather sole edge.
"""
import math

ATTRIBUTE = 'Spearman sewn surface masks'


def smooth(lo, hi, value):
    t = min(1., max(0., (value-lo)/(hi-lo)))
    return t*t*(3-2*t)


def prepare(scene, classify):
    report = {}
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        part = classify(ob)
        if part not in ('skin', 'tunic', 'skirt', 'sandal_l', 'sandal_r'):
            continue
        mesh = ob.data
        # Cache normals before adding a colour attribute invalidates them.
        faces = [(tuple(p.normal), list(p.loop_indices)) for p in mesh.polygons]
        coords = [tuple(v.co) for v in mesh.vertices]
        attr = mesh.color_attributes.get(ATTRIBUTE) or mesh.color_attributes.new(
            name=ATTRIBUTE, type='FLOAT_COLOR', domain='CORNER')
        totals = [0., 0., 0., 0.]
        for normal, loops in faces:
            nx, ny, nz = normal
            for i in loops:
                vertex = mesh.loops[i].vertex_index
                x, y, z = coords[vertex]
                sole = lining = shoulder = foot = 0.
                if ob.name.startswith(('Leather sandal sole ', 'Sandal welt ')):
                    # Keep the painted vertical sidewall: darkening it made
                    # the already-thick rest sole look like a slab. Only the
                    # underside and its downward bevel need new pigment.
                    sole = 1-smooth(-.65, -.05, nz)
                elif part == 'skirt':
                    # Closed skirt strips have separate inward faces; freezing
                    # their radial normal avoids darkening the cream front.
                    radial = (nx*x+ny*y)/max(math.hypot(x, y), .001)
                    lining = 1-smooth(-.45, .05, radial)
                elif part == 'tunic':
                    shoulder = smooth(-.10, .02, y)*smooth(1.25, 1.37, z)
                elif ob.name.startswith('MPFB anatomical male'):
                    weights = sum(g.weight for g in mesh.vertices[vertex].groups
                                  if ob.vertex_groups[g.group].name in ('foot_l', 'foot_r', 'ball_l', 'ball_r'))
                    foot = smooth(.3, .8, weights)*(1-smooth(.07, .14, z))
                values = (sole, lining, shoulder, foot)
                attr.data[i].color = values
                totals = [a+b for a, b in zip(totals, values)]
        report[ob.name] = totals
    return report


def pigment(g, part, colour, unseen, light, lin3, palettes):
    attr = g.node('ShaderNodeVertexColor', layer_name=ATTRIBUTE)
    split = g.node('ShaderNodeSeparateColor')
    g.l.new(attr.outputs['Color'], split.inputs[0])
    # Leather soles never become skin or stone when the foot rolls. The top
    # retains the registered straps; a restrained brown range belongs below.
    if part.startswith('sandal') or part == 'skin':
        leather = g.ramp(light, [(.0, lin3((61, 35, 20))), (.5, lin3((100, 65, 38))),
                                 (1., lin3((139, 99, 61)))])
        mask = split.outputs[0] if part.startswith('sandal') else g.math('MULTIPLY', unseen, attr.outputs['Alpha'])
        return g.mix(mask, colour, leather)
    if part == 'skirt':
        linen = g.ramp(light, [(.0, lin3((64, 40, 24))), (.5, lin3((108, 77, 45))),
                               (1., lin3((151, 118, 77)))])
        return g.mix(g.math('MULTIPLY', unseen, split.outputs[1]), colour, linen)
    if part == 'tunic':
        palette = palettes['cloak']
        wool = g.ramp(light, [(p, lin3(c)) for p, c in zip(palette['positions'], palette['colours'])])
        return g.mix(g.math('MULTIPLY', unseen, split.outputs[2]), colour, wool)
    return colour

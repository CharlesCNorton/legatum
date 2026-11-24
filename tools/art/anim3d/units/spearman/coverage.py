"""Frozen painted coverage for sleeves, upper skin and both sides of the cloak.

Called after the round-9 projection/underpaint. No geometry or motion edits.
Broad form paint is saved on the mesh; it cannot swim when cloth bounds change.
"""
import heapq
import math

import numpy as np

PAINT = 'R10b garment coverage'
BODY = 'MPFB anatomical male • original topology'
SLEEVE = 'Linen tunic shoulder sleeves'
CLOAK = 'Cloak • simulated wool'


def linear(rgb):
    x = np.asarray(rgb, dtype=float) / 255
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)


def smooth(a, b, x):
    t = min(1., max(0., (x-a)/(b-a)))
    return t*t*(3-2*t)


def paint_surface(ob, pixels, kind):
    mesh = ob.data
    uv = mesh.uv_layers['Painting camera rest']
    mask = mesh.color_attributes['Painting visibility']
    h, w = pixels.shape[:2]
    count = len(mesh.vertices)
    colors = np.zeros((count, 3))
    trusted = np.zeros(count, dtype=bool)
    sums = np.zeros(count)
    # Retain the source's local broad colour at projection boundaries. Reject
    # skin/linen contamination on wool before extending it over the back.
    for loop in mesh.loops:
        u, v = uv.data[loop.index].uv
        if not (0 <= u < 1 and 0 <= v < 1):
            continue
        p = pixels[min(h-1, int(v*h)), min(w-1, int(u*w))]
        if mask.data[loop.index].color[0] < .94 or p[3] < .98:
            continue
        if kind == 'wool' and not (p[0] > p[1]*1.55 and p[0] > p[2]*1.7):
            continue
        i = loop.vertex_index
        # This byte-backed sRGB image exposes normalized encoded samples in
        # bpy (verified against PNG bytes); convert once for FLOAT_COLOR.
        colors[i] += linear(p[:3]*255)
        sums[i] += 1
        trusted[i] = True
    colors[trusted] /= sums[trusted, None]
    adjacent = [[] for _ in range(count)]
    for edge in mesh.edges:
        a, b = edge.vertices
        distance = (ob.matrix_world.to_3x3() @ (mesh.vertices[a].co-mesh.vertices[b].co)).length
        adjacent[a].append((b, distance))
        adjacent[b].append((a, distance))
    for _ in range(4):
        old = colors.copy()
        for i in np.flatnonzero(trusted):
            near = [j for j, _ in adjacent[i] if trusted[j]]
            if near:
                colors[i] = .5*old[i]+.5*np.mean(old[near], axis=0)
    distance = np.full(count, np.inf)
    q = []
    reach = .10 if kind == 'linen' else .12
    for i in np.flatnonzero(trusted):
        distance[i] = 0
        heapq.heappush(q, (0., int(i)))
    while q:
        d, i = heapq.heappop(q)
        if d != distance[i]:
            continue
        for j, length in adjacent[i]:
            if d+length < min(distance[j], reach):
                distance[j] = d+length
                colors[j] = colors[i]
                heapq.heappush(q, (d+length, j))
    for _ in range(4):
        old = colors.copy()
        for i in np.flatnonzero(np.isfinite(distance) & ~trusted):
            near = [j for j, _ in adjacent[i] if np.isfinite(distance[j])]
            if near:
                colors[i] = .35*old[i]+.65*np.mean(old[near], axis=0)
    # Cache normals before colour writes invalidate Blender's mesh caches.
    coordinates = [tuple(v.co) for v in mesh.vertices]
    normals = [tuple(v.normal) for v in mesh.vertices]
    attr = mesh.color_attributes.get(PAINT) or mesh.color_attributes.new(name=PAINT, type='FLOAT_COLOR', domain='CORNER')
    palette = {'linen': [(99, 65, 40), (174, 139, 91), (224, 199, 151)],
               'wool': [(58, 14, 9), (114, 29, 15), (171, 56, 27)],
               'skin': [(100, 56, 31), (174, 113, 66), (224, 169, 111)]}[kind]
    low, mid, high = [linear(c) for c in palette]
    for loop in mesh.loops:
        i = loop.vertex_index
        x, y, z = coordinates[i]
        nx, ny, nz = normals[i]
        # Broad pigment masses only. These values are frozen in rest space,
        # with the existing AO and 10% physical shader revealing moving folds.
        facing = max(0., min(1., .50+.35*nz-.30*ny-.16*nx))
        if kind == 'wool':
            facing = .28+.48*(.5+.5*math.cos(x*39))
        elif kind == 'linen':
            fold = .5+.5*math.sin(z*72+abs(x)*14)
            facing = max(0., min(1., facing*.55+fold*.45))
        fill = low*(1-2*facing)+mid*(2*facing) if facing < .5 else mid*(2-2*facing)+high*(2*facing-1)
        weight = 1-smooth(0, reach, distance[i])
        color = colors[i]*weight+fill*(1-weight)
        if kind == 'linen':
            # Continue the cinnabar collar as a rear shoulder facing. This is
            # a fixed garment boundary in rest space, below the real collar;
            # the front sleeve and exposed upper arm retain their linen/skin.
            mantle = smooth(-.28, -.16, y)*smooth(1.25, 1.34, z)
            red_shadow, red_light = linear((67, 17, 10)), linear((144, 46, 25))
            rear = red_shadow*(1-facing)+red_light*facing
            color = color*(1-mantle)+rear*mantle
        # Only upper torso/shoulder skin; never change face, legs or feet.
        region = smooth(1.15, 1.27, z)*(1-smooth(1.48, 1.58, z)) if kind == 'skin' else 1.
        region *= 1-smooth(.15, .85, mask.data[loop.index].color[0])
        attr.data[loop.index].color = (*color, region)
    return {'vertices': count, 'trusted_vertices': int(trusted.sum()),
            'continuation_vertices': int((np.isfinite(distance) & ~trusted).sum()), 'reach_m': reach}


def apply(scene, source):
    if scene.get('spearman_garment_coverage') == 10:
        raise RuntimeError('Start garment coverage from the round-9 master')
    pixels = np.empty(len(source.pixels), dtype=np.float32)
    source.pixels.foreach_get(pixels)
    pixels = pixels.reshape((source.size[1], source.size[0], 4))
    report = {}
    for name, kind in [(SLEEVE, 'linen'), (CLOAK, 'wool'), (BODY, 'skin')]:
        ob = scene.objects[name]
        report[name] = paint_surface(ob, pixels, kind)
        for mat in ob.data.materials:
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            emit = next(n for n in nodes if n.label == 'Generated fill pigment, camera only')
            shade = emit.inputs['Color'].links[0].from_node
            attr = nodes.new('ShaderNodeVertexColor'); attr.layer_name = PAINT
            blend = nodes.new('ShaderNodeMixRGB'); blend.label = 'R10b frozen broad garment and skin paint'
            links.new(attr.outputs['Alpha'], blend.inputs[0])
            links.new(shade.inputs[1].links[0].from_socket, blend.inputs[1])
            links.new(attr.outputs['Color'], blend.inputs[2])
            links.new(blend.outputs[0], shade.inputs[1])
            if kind == 'wool':
                # A double-sided cloth shell shares the surface UVs. Accept
                # only red source pigment, never the painted limb beneath it.
                tex = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image == source)
                split = nodes.new('ShaderNodeSeparateColor'); split.mode = 'RGB'
                links.new(tex.outputs['Color'], split.inputs[0])
                ratio = nodes.new('ShaderNodeMath'); ratio.operation = 'MULTIPLY'; ratio.inputs[1].default_value = 1.8
                links.new(split.outputs['Green'], ratio.inputs[0])
                red = nodes.new('ShaderNodeMath'); red.operation = 'SUBTRACT'
                links.new(split.outputs['Red'], red.inputs[0]); links.new(ratio.outputs[0], red.inputs[1])
                gate = nodes.new('ShaderNodeMapRange'); gate.clamp = True
                gate.inputs['From Min'].default_value = .005; gate.inputs['From Max'].default_value = .05
                links.new(red.outputs[0], gate.inputs['Value'])
                projected = next(n for n in nodes if n.label == 'Painted illumination, fixed rest UV')
                mix = projected.outputs[0].links[0].to_node
                factor = nodes.new('ShaderNodeMath'); factor.operation = 'MULTIPLY'
                camera_gate = mix.inputs[0].links[0].from_node
                links.new(camera_gate.inputs[0].links[0].from_socket, factor.inputs[0])
                links.new(gate.outputs[0], factor.inputs[1])
                links.new(factor.outputs[0], camera_gate.inputs[0])
            mat['spearman_garment_coverage'] = 10
    scene['spearman_garment_coverage'] = 10
    return report

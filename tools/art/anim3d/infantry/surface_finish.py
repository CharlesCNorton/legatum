"""Spearman material-only finish: frozen seam underpainting and physical texture.

No object transforms, geometry, animation, camera or lighting are changed. The
source painting's low-frequency pigment continues a short distance around each
visible surface into existing image-generated fills. Local mesh adjacency keeps
that continuation from crossing between nearby but disconnected surfaces.
"""
import heapq

import bpy
import numpy as np

SEAM_COLOUR = 'R9b seam underpaint'
SEAM_REACH = .075


def linear(rgb):
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def underpaint(ob, pixels):
    """Extend trusted paint over mesh edges, never across a ray-occluded gap.

    Multi-source Dijkstra uses a bounded geodesic distance on the original
    topology. This fills narrow unpainted wedges without copying an arm onto a
    nearby shield or projecting front paint through to its disconnected back.
    """
    mesh = ob.data
    uv = mesh.uv_layers.get('Painting camera rest')
    mask = mesh.color_attributes.get('Painting visibility')
    if uv is None or mask is None:
        return False
    height, width = pixels.shape[:2]
    count = len(mesh.vertices)
    colors = np.zeros((count, 3), dtype=np.float64)
    valid = np.zeros(count, dtype=bool)
    for loop in mesh.loops:
        u, v = uv.data[loop.index].uv
        if not (0 <= u < 1 and 0 <= v < 1):
            continue
        p = pixels[min(height-1, int(v*height)), min(width-1, int(u*width))]
        if mask.data[loop.index].color[0] > .94 and p[3] > .98:
            colors[loop.vertex_index] = linear(p[:3])
            valid[loop.vertex_index] = True
    if not np.any(valid):
        return False
    # Smooth only the continuation undercoat, never the original image texture.
    adjacent = [[] for _ in range(count)]
    for edge in mesh.edges:
        a, b = edge.vertices
        distance = (ob.matrix_world.to_3x3() @
                    (mesh.vertices[a].co-mesh.vertices[b].co)).length
        adjacent[a].append((b, distance))
        adjacent[b].append((a, distance))
    for _ in range(2):
        previous = colors.copy()
        for i in np.flatnonzero(valid):
            neighbors = [j for j, _ in adjacent[i] if valid[j]]
            if neighbors:
                colors[i] = .5*previous[i]+.5*np.mean(previous[neighbors], axis=0)
    distances = np.full(count, np.inf)
    queue = []
    for index in np.flatnonzero(valid):
        i = int(index)
        distances[i] = 0
        heapq.heappush(queue, (0., i))
    while queue:
        distance, i = heapq.heappop(queue)
        if distance != distances[i]:
            continue
        for j, length in adjacent[i]:
            candidate = distance+length
            if candidate < distances[j] and candidate < SEAM_REACH:
                distances[j] = candidate
                colors[j] = colors[i]
                heapq.heappush(queue, (candidate, j))
    # Blur propagated regions to avoid nearest-seed bands around the seam.
    for _ in range(3):
        previous = colors.copy()
        for i in np.flatnonzero(np.isfinite(distances) & ~valid):
            neighbors = [j for j, _ in adjacent[i] if np.isfinite(distances[j])]
            if neighbors:
                colors[i] = .4*previous[i]+.6*np.mean(previous[neighbors], axis=0)
    attr = mesh.color_attributes.get(SEAM_COLOUR) or mesh.color_attributes.new(
        name=SEAM_COLOUR, type='FLOAT_COLOR', domain='CORNER')
    for loop in mesh.loops:
        i = loop.vertex_index
        t = min(1., distances[i]/SEAM_REACH)
        weight = 1-t*t*(3-2*t)
        attr.data[loop.index].color = (*colors[i], weight)
    return True


def math_node(nodes, links, operation, a, b):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for socket, value in zip(node.inputs, (a, b)):
        if isinstance(value, (float, int)):
            socket.default_value = value
        else:
            links.new(value, socket)
    return node.outputs[0]


def finish_material(mat, seam):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    fill_pigment = next((n for n in nodes if n.label == 'Generated fill pigment, camera only'), None)
    if bsdf is None or fill_pigment is None:
        return False
    name = mat.name.lower()
    kind = next((k for k in ('bronze', 'linen', 'wool', 'leather', 'skin') if k in name), None)
    if kind is None:
        return False
    coords = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.label = 'R9b brush-scale surface variation'
    noise.inputs['Scale'].default_value = 54 if kind == 'bronze' else 95
    noise.inputs['Detail'].default_value = 3
    links.new(coords.outputs['Generated'], noise.inputs['Vector'])
    height = noise.outputs['Fac']
    if kind in {'linen', 'wool'}:
        warp = nodes.new('ShaderNodeTexWave')
        warp.bands_direction = 'X'
        weft = nodes.new('ShaderNodeTexWave')
        weft.bands_direction = 'Z'
        for wave in (warp, weft):
            wave.inputs['Scale'].default_value = 180 if kind == 'linen' else 125
            wave.inputs['Distortion'].default_value = 2
            links.new(coords.outputs['Generated'], wave.inputs['Vector'])
        height = math_node(nodes, links, 'MULTIPLY', warp.outputs['Fac'], weft.outputs['Fac'])
        bsdf.inputs['Sheen Weight'].default_value = .18
        bsdf.inputs['Sheen Roughness'].default_value = .8
    bump = nodes.new('ShaderNodeBump')
    bump.label = 'R9b restrained hammer / weave / grain'
    bump.inputs['Strength'].default_value = .16 if kind == 'bronze' else .12
    bump.inputs['Distance'].default_value = .0008 if kind == 'bronze' else .00035
    if bsdf.inputs['Normal'].is_linked:
        links.new(bsdf.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
    links.new(height, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    # Retain the existing baked AO/curvature and scanned roughness. Skin is
    # matte painted flesh; metal remains metallic, with stronger worn rims.
    if kind == 'bronze':
        bsdf.inputs['Metallic'].default_value = 0 if 'patina' in name else 1
        if 'polished' in name:
            for link in list(bsdf.inputs['Roughness'].links):
                links.remove(link)
            bsdf.inputs['Roughness'].default_value = .28
    elif kind == 'skin':
        bsdf.inputs['Roughness'].default_value = .72
        bsdf.inputs['Specular IOR Level'].default_value = .22
        bsdf.inputs['Subsurface Weight'].default_value = .015
    # Keep the original generated fill and its AO in the distant unseen region.
    shade = fill_pigment.inputs['Color'].links[0].from_node
    original_fill = shade.inputs[1].links[0].from_socket
    pigment = original_fill
    if seam:
        attr = nodes.new('ShaderNodeVertexColor')
        attr.layer_name = SEAM_COLOUR
        # Generated/physical surface detail continues through the low-frequency
        # undercoat. Do not run the whole source texture across unseen polygons.
        brush = nodes.new('ShaderNodeMixRGB')
        brush.blend_type = 'MULTIPLY'
        brush.inputs[0].default_value = .35
        grain = nodes.new('ShaderNodeRGBToBW')
        links.new(original_fill, grain.inputs[0])
        grain_range = nodes.new('ShaderNodeMapRange')
        grain_range.inputs['From Min'].default_value = .025
        grain_range.inputs['From Max'].default_value = .55
        grain_range.inputs['To Min'].default_value = .86
        grain_range.inputs['To Max'].default_value = 1.14
        grain_range.clamp = True
        links.new(grain.outputs[0], grain_range.inputs['Value'])
        links.new(attr.outputs['Color'], brush.inputs[1])
        links.new(grain_range.outputs['Result'], brush.inputs[2])
        blend = nodes.new('ShaderNodeMixRGB')
        blend.label = 'R9b geodesic paint-to-fill seam'
        links.new(attr.outputs['Alpha'], blend.inputs[0])
        links.new(original_fill, blend.inputs[1])
        links.new(brush.outputs[0], blend.inputs[2])
        pigment = blend.outputs[0]
    links.new(pigment, shade.inputs[1])
    shade.inputs[0].default_value = .35
    # 90% camera pigment matches the projected layer's 96% at the seam, while
    # live AO and the remaining PBR keep folds, cavities and metal relief.
    unseen = next(n for n in nodes if n.label == 'Painted unseen surface with physical response')
    unseen.inputs[0].links[0].from_node.inputs[1].default_value = .90
    mat['spearman_surface_finish'] = 9
    return True


def apply(scene, source):
    if scene.get('spearman_surface_finish') == 9:
        raise RuntimeError('Surface finish already applied: start from clean projection')
    pixels = np.empty(len(source.pixels), dtype=np.float32)
    source.pixels.foreach_get(pixels)
    pixels = pixels.reshape((source.size[1], source.size[0], 4))
    objects = materials = 0
    for ob in scene.objects:
        if ob.type != 'MESH' or ob.hide_render or ob.name == 'Stationary cream stone':
            continue
        relevant = [m for m in ob.data.materials if m and m.use_nodes and
                    any(n.label == 'Generated fill pigment, camera only' for n in m.node_tree.nodes)]
        if not relevant:
            continue
        seam = underpaint(ob, pixels)
        objects += int(seam)
        for mat in relevant:
            materials += int(finish_material(mat, seam))
    scene['spearman_surface_finish'] = 9
    scene['spearman_surface_method'] = 'Frozen geodesic seam underpaint; existing generated fills; camera-only pigment; physical microtexture'
    print('SURFACE_FINISH', objects, 'seam attributes;', materials, 'materials')
    return {'seam_objects': objects, 'materials': materials, 'reach_m': SEAM_REACH}

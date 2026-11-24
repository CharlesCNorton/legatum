"""Frozen geodesic continuation; no image reprojection during animation."""
import heapq
import numpy as np

def linear(rgb):
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def underpaint(ob, pixels, reach=.075, attribute="R9b seam underpaint"):
    SEAM_REACH, SEAM_COLOUR = reach, attribute
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



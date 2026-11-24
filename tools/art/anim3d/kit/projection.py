"""Freeze hero-camera coordinates and visibility on original topology.

The input evaluated points must retain original vertex indexing. Visibility
thresholds are unit presets, not generally safe tolerances for every mesh.
"""
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def freeze_projection(ob, points, normals, sc, tree, image, registration,
                      visibility_tolerance=.018, relief_tolerance=.14,
                      relief_prefixes=()):
    x0, y0, px0, py0, sx, sy, canvas = registration
    view = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    uv = ob.data.uv_layers.get('Painting camera rest') or ob.data.uv_layers.new(name='Painting camera rest')
    mask = ob.data.color_attributes.get('Painting visibility') or ob.data.color_attributes.new(name='Painting visibility', type='FLOAT_COLOR', domain='CORNER')
    weights = []
    for p, normal in zip(points, normals):
        hit, _, _, distance = tree.ray_cast(p+view*10, -view, 10.02)
        visible = hit is not None and (hit-p).length < visibility_tolerance
        # Relief can occlude adjacent shield vertices. The whole front shell
        # carries the same paint beneath it; do not punch PBR wedges into it.
        if ob.name.startswith(relief_prefixes):
            visible = hit is not None and (hit-p).length < relief_tolerance
        # Ray visibility rejects hidden backs. Absolute facing also supports
        # double-sided cloth and open armour shells without painting through them.
        facing = abs(normal.dot(view))
        weight = max(0, min(1, (facing-.02)/.18)) if visible else 0
        weights.append(weight)
    for loop in ob.data.loops:
        p = world_to_camera_view(sc, sc.camera, points[loop.vertex_index])
        # Full-resolution painting -> the game's padded 256px reference canvas.
        u = (x0+(p.x*canvas-px0)*sx)/image.size[0]
        v = 1-(y0+((1-p.y)*canvas-py0)*sy)/image.size[1]
        uv.data[loop.index].uv = (u, v)
        w = weights[loop.vertex_index]
        mask.data[loop.index].color = (w, w, w, 1)
    return uv, mask, round(sum(weights)/max(1, len(weights)), 3)

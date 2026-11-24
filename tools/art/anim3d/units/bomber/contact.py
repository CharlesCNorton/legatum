"""World-space mesh-surface contact for the wreck and the deformed stone.

Sample triangle interiors as well as vertices; a bounding-box or one vertex at
the nominal disc height can miss both a sloping belly and raised support rubble.
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def wreck_contact():
    deps = bpy.context.evaluated_depsgraph_get()
    vertices, faces = [], []
    for name in ('GEO-stationary cream base', 'GEO-curved stationary stone support'):
        ob = bpy.data.objects[name].evaluated_get(deps)
        mesh = ob.to_mesh()
        mesh.calc_loop_triangles()
        offset = len(vertices)
        vertices.extend(ob.matrix_world @ v.co for v in mesh.vertices)
        faces.extend(tuple(offset+i for i in tri.vertices) for tri in mesh.loop_triangles)
        ob.to_mesh_clear()
    stone = BVHTree.FromPolygons(vertices, faces, all_triangles=True)
    gaps = []
    for name in ('GEO-fuselage', 'GEO-near nacelle', 'GEO-far nacelle',
                 'GEO-near wing', 'GEO-far wing'):
        ob = bpy.data.objects[name].evaluated_get(deps)
        mesh = ob.to_mesh()
        mesh.calc_loop_triangles()
        points = [ob.matrix_world @ v.co for v in mesh.vertices]
        # Interior and edge samples detect faces crossing a small stone footprint.
        for tri in mesh.loop_triangles:
            a, b, c = [points[i] for i in tri.vertices]
            for u, v in ((1/3,1/3),(.5,0),(0,.5),(.5,.5)):
                pt = a*(1-u-v)+b*u+c*v
                hit, _, _, _ = stone.ray_cast(Vector((pt.x,pt.y,10)), Vector((0,0,-1)), 30)
                if hit is not None:
                    gaps.append((pt.z-hit.z, name, tuple(pt), tuple(hit)))
        for pt in points:
            hit, _, _, _ = stone.ray_cast(Vector((pt.x,pt.y,10)), Vector((0,0,-1)), 30)
            if hit is not None:
                gaps.append((pt.z-hit.z, name, tuple(pt), tuple(hit)))
        ob.to_mesh_clear()
    assert gaps, 'wreck misses actual stone surfaces'
    gap, name, point, stone_point = min(gaps)
    return {'gap':gap, 'object':name, 'point':point, 'stone_point':stone_point,
            'samples':len(gaps), 'method':'evaluated triangles against stone BVH'}

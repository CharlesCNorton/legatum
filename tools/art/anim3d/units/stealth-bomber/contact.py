"""Sample evaluated triangles over the disc, including face interiors.

Vertex-only contact can miss a large triangle crossing through a small disc.
This bounded sampling is a render audit, not a general collision solver.
"""
import bpy
from mathutils import Vector


def disc_clearance(scene, objects, base):
    top = max((base.matrix_world @ Vector(v)).z for v in base.bound_box)
    deps = bpy.context.evaluated_depsgraph_get()
    heights = []
    for ob in objects:
        ev = ob.evaluated_get(deps)
        mesh = ev.to_mesh()
        mesh.calc_loop_triangles()
        for tri in mesh.loop_triangles:
            a, b, c = [ev.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
            # Subdivision tracks geometric edge length, not arbitrary mesh density.
            steps = max(1, min(24, int(max((b-a).length, (c-a).length, (c-b).length) / .075) + 1))
            for i in range(steps+1):
                for j in range(steps-i+1):
                    pt = a + (b-a)*(i/steps) + (c-a)*(j/steps)
                    if (pt.xy-base.location.xy).length < .98:
                        heights.append(pt.z)
        ev.to_mesh_clear()
    return min(heights)-top if heights else None


def support_clearance(scene, body, support):
    """Vertical gap from the stand surface to the lowest wing surface above it."""
    from mathutils.bvhtree import BVHTree
    deps=bpy.context.evaluated_depsgraph_get()
    ev=body.evaluated_get(deps);mesh=ev.to_mesh()
    tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices], [tuple(p.vertices) for p in mesh.polygons])
    ev.to_mesh_clear()
    ev=support.evaluated_get(deps);mesh=ev.to_mesh()
    points=[ev.matrix_world@v.co for v in mesh.vertices]
    points += [ev.matrix_world@p.center for p in mesh.polygons]
    gaps=[]
    for pt in points:
        hit,_,_,_=tree.ray_cast(Vector((pt.x,pt.y,-100)),Vector((0,0,1)),200)
        if hit is not None:gaps.append(hit.z-pt.z)
    ev.to_mesh_clear()
    return min(gaps) if gaps else None

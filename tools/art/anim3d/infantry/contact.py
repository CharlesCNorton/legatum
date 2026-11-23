"""Read evaluated articulated sandal geometry, shared by bake and validation."""
import bpy


def sole_points(side):
    ob=bpy.data.objects['Leather sandal sole '+side]
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.to_mesh()
    points=[ob.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    return points


def landmarks(side, points=None):
    ob=bpy.data.objects['Leather sandal sole '+side]
    points=sole_points(side) if points is None else points
    return {name: points[int(ob[name+'_vertex'])] for name in ['toe','heel']}

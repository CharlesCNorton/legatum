"""Read evaluated articulated sandal geometry, shared by bake and validation."""
import bpy


def sole_points(side, prefix="Leather sandal sole "):
    ob=bpy.data.objects[prefix+side]
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.to_mesh()
    points=[ob.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    return points


def landmarks(side, points=None, prefix="Leather sandal sole "):
    ob=bpy.data.objects[prefix+side]
    points=sole_points(side, prefix) if points is None else points
    return {name: points[int(ob[name+'_vertex'])] for name in ['toe','heel']}


def seat_rest_guard(rig, target_height, sides=('l', 'r'), prefix='Leather sandal sole '):
    """Translate the complete fitted guard onto its actual evaluated sole plane.

    Call before projection/neutral capture, never on a retargeted walk. Does not
    change the foot's rotation, bind, weights, topology or local proportions.
    Callers still check each foot: one translation cannot fix an uneven stance.
    """
    before = {side: min(p.z for p in sole_points(side, prefix)) for side in sides}
    delta = target_height-min(before.values())
    rig.location.z += delta
    bpy.context.view_layer.update()
    return {'root_shift_m': delta, 'before': before,
            'after': {side: min(p.z for p in sole_points(side, prefix)) for side in sides}}

"""Measure actual hoof soles and transfer licensed source contact trajectories."""
import bpy
from mathutils import Vector

NAMES = ('front.L','front.R','back.L','back.R')


def hooves(horse):
    states = [(m,m.show_viewport) for m in horse.modifiers if m.type=='SUBSURF']
    for m,_ in states:
        m.show_viewport = False
    bpy.context.view_layer.update()
    obj = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    ids = {i for p in horse.data.polygons if horse.data.materials[p.material_index].name=='Horn hooves' for i in p.vertices}
    result = {}
    for name in NAMES:
        family,side = name.split('.')
        prefixes = ('Front','FF.') if family=='front' else ('Back','FFB.')
        selected = [i for i in ids if any(horse.vertex_groups[g.group].name.endswith('.'+side)
                    and horse.vertex_groups[g.group].name.startswith(prefixes) and g.weight>.2
                    for g in horse.data.vertices[i].groups)]
        assert selected,name
        points = [obj.matrix_world@mesh.vertices[i].co for i in selected]
        z = min(p.z for p in points)
        sole = [p for p in points if p.z<z+.025]
        centre = sum(sole,Vector())/len(sole)
        result[name] = {'z':z,'centre':list(centre)}
    obj.to_mesh_clear()
    for m,state in states:
        m.show_viewport = state
    bpy.context.view_layer.update()
    return result


def transfer_contacts(arm, horse, source, source_rest, painted_rest):
    """Transfer source sole paths without changing any source foot rotation.

    Source x/y trajectories receive constant rest offsets. Source z retains its
    original stance/swing timing above the .112m disc. Translations taper into
    the upper limbs; this is positional retargeting, not a new authored gait.
    """
    current = hooves(horse)
    offsets = {}
    targets = {}
    floor = min(v['z'] for v in source.values())
    for name in NAMES:
        target = Vector(source[name]['centre'])
        origin = Vector(source_rest[name]['centre'])
        rest = Vector(painted_rest[name]['centre'])
        actual = Vector(current[name]['centre'])
        delta = Vector((target.x-origin.x+rest.x-actual.x,
                        target.y-origin.y+rest.y-actual.y,
                        .112+source[name]['z']-floor-current[name]['z']))
        offsets[name] = delta
        targets[name] = actual+delta
    original = {p.name:p.matrix.copy() for p in arm.pose.bones}
    inverse = arm.matrix_world.to_3x3().inverted()
    for p in sorted(arm.pose.bones,key=lambda p:len(p.parent_recursive)):
        name = p.name
        if not name.endswith(('.L','.R')):
            continue
        side = name[-1]
        family = 'front' if name.startswith(('Front','IKFront','FF.')) else 'back' if name.startswith(('Back','IKBack','FFB.')) else None
        if family is None or 'Shoulder' in name:
            continue
        strength = .35 if name.startswith(('BackLeg.','FrontUpperLeg.')) else .60 if name.startswith('BackUpperLeg.') else .80 if 'LowerLeg' in name else 1.
        matrix = original[name].copy()
        matrix.translation += inverse@(offsets[family+'.'+side]*strength)
        p.matrix = matrix
        bpy.context.view_layer.update()
    measured = hooves(horse)
    position_error = max((Vector(measured[n]['centre'])-targets[n]).length for n in NAMES)
    rotation_error = max(original[p.name].to_quaternion().rotation_difference(p.matrix.to_quaternion()).angle
                         for p in arm.pose.bones if p.name.startswith(('FF.','FFB.')))
    assert position_error<.005, ('Sole trajectory transfer',position_error)
    assert rotation_error<.001, ('Source foot orientation changed',rotation_error)
    return {'offsets':{n:list(v) for n,v in offsets.items()},
            'sole_position_error_m':position_error,'foot_rotation_error_rad':rotation_error}

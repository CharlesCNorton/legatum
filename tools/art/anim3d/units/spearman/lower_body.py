"""Anatomical lower-leg volume and leather construction, before frozen paint.

All fitting uses rig/rest coordinates, never the camera. The human feet, sole
contact vertices, skin weights and bind matrices are unchanged. Locomotion
continues to calibrate from the original rest/roll mapping.
"""
import json
import math

import bpy
from mathutils import Matrix, Vector


def calf_volume(point, bone):
    axis = (bone.tail_local - bone.head_local).normalized()
    distance = (point - bone.head_local).dot(axis)
    t = distance / bone.length
    if not .02 < t < .94:
        return point
    # Round both transverse axes; fade into the knee and Achilles. A foot or
    # toe vertex never enters this field, regardless of camera or guard pose.
    fade = math.sin(math.pi * (t - .02) / .92) ** .7
    center = bone.head_local + axis * distance
    return point + (point - center) * (.30 * fade)


def fit_legs(scene, rig):
    body = bpy.data.objects['MPFB anatomical male • original topology']
    assert body.data.shape_keys is None, 'Freeze the working macro mix first'
    changed = {}
    for ob in list(scene.objects):
        if ob.type != 'MESH':
            continue
        skin = ob == body or ob.name.startswith('Contoured greave ')
        if not skin:
            continue
        # Shell/body coordinates are in armature rest space. Chased decoration
        # stays at its existing radius rather than floating outside the shell.
        to_rig = rig.matrix_world.inverted() @ ob.matrix_world
        inverse = to_rig.inverted()
        count = 0
        for v in ob.data.vertices:
            p = to_rig @ v.co
            side = 'l' if p.x > 0 else 'r'
            # Foot/ball vertices are an explicit exclusion, even at the ankle.
            if any(ob.vertex_groups[g.group].name.startswith(('foot_', 'ball_'))
                            and g.weight > .001 for g in v.groups):
                continue
            q = calf_volume(p, rig.data.bones['calf_' + side])
            if (q-p).length > 1e-8:
                v.co = inverse @ q
                count += 1
        ob.data.update()
        changed[ob.name] = count
    return changed


def brace(rig):
    """Close calf/ankle gaps with a fixed-length rest-guard two-bone solve.

    Turn the guard's whole foot/ball pair about the vertical anatomical axis,
    preserving ankle/toe roll and scale. This is BEFORE source calibration, not
    a post-retarget correction. The move mapping resets the guard legs to the
    original bind and therefore never inherits these guard-only turns.
    Bring the overextended spear-side ankle 25mm inward, keeping sole height.
    This is a guard-pose edit only; no bind or source animation is modified.
    """
    report = {}
    for side in ('l', 'r'):
        upper, lower = [rig.pose.bones[n + '_' + side] for n in ('thigh', 'calf')]
        feet = [(rig.pose.bones[n + '_' + side], rig.pose.bones[n + '_' + side].matrix.copy())
                for n in ('foot', 'ball')]
        if side == 'r':
            for _, matrix in feet:
                matrix.translation.x += .025
        pivot = feet[0][1].translation.copy()
        yaw = math.radians(55 if side == 'l' else -12)
        turn = Matrix.Translation(pivot) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Translation(-pivot)
        feet = [(bone, turn @ matrix) for bone, matrix in feet]
        target = feet[0][1].translation.copy()
        origin = upper.head.copy()
        axis = target - origin
        length = axis.length
        a, b = upper.bone.length, lower.bone.length
        assert abs(a-b) < length < a+b, (side, length, a+b)
        axis.normalize()
        along = (a*a - b*b + length*length) / (2*length)
        pole = Vector((.34, -.40, .48) if side == 'l' else (-.43, -.40, .48)) - origin
        pole = (pole - axis*pole.dot(axis)).normalized()
        knee = origin + axis*along + pole*math.sqrt(max(0, a*a-along*along))
        old_knee = lower.head.copy()
        for bone, direction in ((upper, knee-origin), (lower, target-knee)):
            rest = bone.bone.matrix_local.to_quaternion()
            swing = (rest @ Vector((0, 1, 0))).rotation_difference(direction.normalized())
            matrix = (swing @ rest).to_matrix().to_4x4()
            matrix.translation = bone.head
            bone.matrix = matrix
            bpy.context.view_layer.update()
        for bone, matrix in feet:
            bone.matrix = matrix
            bpy.context.view_layer.update()
        report[side] = {'knee_shift_m': (lower.head-old_knee).length,
                        'ankle_gap_m': (lower.tail-feet[0][0].head).length,
                        'guard_yaw_degrees': math.degrees(yaw)}
    return report


def add_welt(scene, rig):
    """A 6mm leather overhang above the existing sole; no foot reshaping.

    Bind the new continuous beveled rim with the same foot/ball transition as
    the original sandal. The original underside and its contact IDs are kept.
    """
    for side in ('l', 'r'):
        sole = bpy.data.objects['Leather sandal sole ' + side]
        # Soles were authored as a 61 x 142 mm ellipse in anatomical XY.
        center_x = rig.data.bones['foot_' + side].head_local.x
        center_y = rig.data.bones['foot_' + side].head_local.y - .07
        top = max(v.co.z for v in sole.data.vertices)
        verts, faces = [], []
        rings = 64
        section = 8
        for i in range(rings):
            angle = 2*math.pi*i/rings
            normal = Vector((math.cos(angle)/.061, math.sin(angle)/.142, 0)).normalized()
            edge = Vector((center_x+.061*math.cos(angle), center_y+.142*math.sin(angle), top-.003))
            for j in range(section):
                phase = 2*math.pi*j/section
                verts.append(edge + normal*(.002+.004*math.cos(phase)) + Vector((0, 0, .003*math.sin(phase))))
        for i in range(rings):
            for j in range(section):
                faces.append((i*section+j, ((i+1)%rings)*section+j,
                              ((i+1)%rings)*section+(j+1)%section, i*section+(j+1)%section))
        mesh = bpy.data.meshes.new('Layered leather welt ' + side)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        ob = bpy.data.objects.new('Sandal welt ' + side, mesh)
        scene.collection.objects.link(ob)
        mesh.materials.append(sole.data.materials[0])
        for face in mesh.polygons:
            face.use_smooth = True
        foot, ball = [rig.data.bones[n+'_'+side] for n in ('foot', 'ball')]
        axis = (ball.tail_local-ball.head_local).normalized()
        groups = [ob.vertex_groups.new(name=b.name) for b in (foot, ball)]
        for v in mesh.vertices:
            t = max(0, min(1, ((v.co-ball.head_local).dot(axis)+.025)/.055))
            w = t*t*(3-2*t)
            for group, weight in zip(groups, (1-w, w)):
                group.add([v.index], weight, 'REPLACE')
        ob.parent = rig
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = Matrix.Identity(4)
        mod = ob.modifiers.new('Anatomical sandal toe flex', 'ARMATURE')
        mod.object = rig
        ob['construction'] = '6mm leather edge; original sole/contact and human foot unchanged'


def apply(scene):
    assert not scene.get('spearman_lower_body_round'), 'Start from the clean projection input'
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    changed = fit_legs(scene, rig)
    stance = brace(rig)
    add_welt(scene, rig)
    scene['spearman_lower_body_round'] = '10a'
    scene['spearman_lower_body_receipt'] = json.dumps({'calf_vertices': changed, 'stance': stance})
    bpy.context.view_layer.update()
    print('LOWER_BODY_10A', scene['spearman_lower_body_receipt'], flush=True)
    from shell_fit import apply as fit_shells
    fit_shells(scene)

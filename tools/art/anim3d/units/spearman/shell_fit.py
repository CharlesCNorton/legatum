"""R11a sleeve tailoring and greave coverage, before frozen projection.

Edit real surfaces in anatomical rest coordinates. Human foot/ball vertices,
soles, skin weights, bind matrices and the R10 guard are never changed here.
"""
import json
import math

import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def smoothstep(a, b, value):
    t = max(0., min(1., (value-a)/(b-a)))
    return t*t*(3-2*t)


def section(point, bone):
    axis = (bone.tail_local-bone.head_local).normalized()
    length = (point-bone.head_local).dot(axis)
    center = bone.head_local+axis*length
    return length/bone.length, center, point-center


def fit_greaves(scene, rig):
    changed = {}
    for ob in scene.objects:
        body = ob.name == 'MPFB anatomical male • original topology'
        shell = ob.name.startswith('Contoured greave ')
        if not (body or shell):
            continue
        to_rig = rig.matrix_world.inverted() @ ob.matrix_world
        inverse = to_rig.inverted()
        count = 0
        for v in ob.data.vertices:
            if body and any(ob.vertex_groups[g.group].name.startswith(('foot_', 'ball_'))
                            and g.weight > .001 for g in v.groups):
                continue
            point = to_rig @ v.co
            side = 'l' if point.x > 0 else 'r'
            t, center, radial = section(point, rig.data.bones['calf_'+side])
            envelope = smoothstep(.02, .15, t)*(1-smoothstep(.89, 1.0, t))
            if not envelope:
                continue
            if body:
                # The R10 body grew by 30% along with its open front plate.
                # Tuck its side/back into the armour instead of growing both.
                result = center+radial*(1-.18*envelope)
            else:
                # The shell's foot weights must NOT exclude the ankle plate.
                # It is armour, not a foot: keep the anatomical foot untouched.
                gain = .07+.16*smoothstep(.3, .85, t)
                result = center+radial*(1+gain*envelope)
            if (result-point).length > 1e-8:
                v.co = inverse @ result
                count += 1
        ob.data.update()
        changed[ob.name] = count
    return changed


def seat_shin_contours(scene, rig):
    """Fit shin volumes inward, tapering to the unchanged planted ankle.

    The painting's outer calf is tighter than R10 despite its fuller ankle.
    A uniform radial increase therefore overhangs both outer contours. Fit the
    complete shin cross-section in the fixed rest view, retaining camera depth.
    Foot geometry and the authored foot/ball transforms are excluded.
    """
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}
    right = scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    for ob in scene.objects:
        body = ob.name == 'MPFB anatomical male • original topology'
        if ob.type != 'MESH' or not (body or ob.name.startswith(('Contoured greave ', 'Greave chased spiral '))):
            continue
        skinned = any(m.type == 'ARMATURE' for m in ob.modifiers)
        for v in ob.data.vertices:
            if body and any(ob.vertex_groups[g.group].name.startswith(('foot_', 'ball_'))
                            and g.weight > .001 for g in v.groups):
                continue
            skin = Matrix.Identity(4)
            if skinned:
                weights = [(transforms[ob.vertex_groups[g.group].name], g.weight) for g in v.groups
                           if ob.vertex_groups[g.group].name in transforms]
                total = sum(w for _, w in weights)
                if total > .001:
                    skin = sum((m*(w/total) for m, w in weights), Matrix(((0,)*4,)*4))
            world = ob.matrix_world @ skin @ v.co
            uv = world_to_camera_view(scene, scene.camera, world)
            x, y = uv.x*256, (1-uv.y)*256
            envelope = smoothstep(175, 185, y)*(1-smoothstep(205, 216, y))
            if not envelope:
                continue
            if x < 128:
                center = 110-(y-180)*.28
                dx = (3.0-.20*(x-center))*envelope
            else:
                center = 149+(y-180)*.24
                dx = (-3.5-.20*(x-center))*envelope
            v.co = skin.inverted_safe() @ ob.matrix_world.inverted() @ (world+right*(dx*scene.camera.data.ortho_scale/256))
        ob.data.update()


def apply(scene):
    assert not scene.get('spearman_shell_round'), 'Start from clean projection input'
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    receipt = {'sleeve': 'dropped: marginal colour gain with silhouette regression',
               'greave_vertices': fit_greaves(scene, rig)}
    seat_shin_contours(scene, rig)
    scene['spearman_shell_round'] = '11a'
    scene['spearman_shell_receipt'] = json.dumps(receipt)
    bpy.context.view_layer.update()
    print('SHELL_11A', scene['spearman_shell_receipt'], flush=True)

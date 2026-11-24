"""Fable-b lower-body mass: fuller thighs, calves, greaves and feet.

The painting is a heroic miniature: its greaves are about half again as wide as
the anatomical MPFB calf and its sandalled feet a third larger. Ankle and knee
positions already register with the painting, so the stance reads narrow only
because the limbs are thin. This pass edits REST geometry (before the painting
UVs are frozen): a radial scale about each leg bone's rest axis, weighted by the
vertex's own skin weight, so every clip inherits it through normal skinning.
No bone, weight, pose, sole plane or landmark index changes. Feet scale about
the point under the ankle on the sole plane, so soles stay on the stone.
"""
import bpy
from mathutils import Vector

THIGH, KNEE, ANKLE = 1.16, 1.46, 1.26
FOOT = Vector((1.30, 1.28, 1.12))
SKIN = .8
OUTER = 1.5


def calf_scale(t):
    # t: 0 at the knee joint, 1 at the ankle. Widest over the knee cap and belly.
    t = max(0., min(1., t))
    u = max(0., (t-.45)/.55)
    return KNEE+(ANKLE-KNEE)*u*u*(3-2*u)


def bulk_legs(scene):
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    bones = rig.data.bones
    inverse = rig.matrix_world.inverted()
    # Rest sole plane, from the real sandal soles in armature rest space.
    sole_z = {}
    for side in 'lr':
        ob = bpy.data.objects['Leather sandal sole '+side]
        m = inverse @ ob.matrix_world
        sole_z[side] = min((m @ v.co).z for v in ob.data.vertices)
    changed = {}
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        skinned = any(m.type == 'ARMATURE' for m in ob.modifiers)
        if skinned:
            assert not ob.data.shape_keys, ob.name+': bake shape keys before bulk_legs'
            names = {g.index: g.name for g in ob.vertex_groups}
            to_arm = inverse @ ob.matrix_world
            back = to_arm.inverted()
            count = 0
            body = ob.name.startswith('MPFB anatomical')
            for vertex in ob.data.vertices:
                p = to_arm @ vertex.co
                move = Vector()
                for g in vertex.groups:
                    name = names[g.group]
                    if g.weight < 1e-4 or name[-2:] not in ('_l', '_r'):
                        continue
                    side = name[-1]
                    part = name[:-2]
                    if part in ('thigh', 'calf'):
                        bone = bones[name]
                        axis = (bone.tail_local-bone.head_local)
                        length = axis.length
                        axis.normalize()
                        rel = p-bone.head_local
                        along = rel.dot(axis)
                        radial = rel-axis*along
                        scale = THIGH+(KNEE-THIGH)*max(0., min(1., (along/length-.72)/.28)) if part == 'thigh' else calf_scale(along/length)
                        if body:
                            # The skin stays inside the bronze: an anatomical calf scaled
                            # as far as its greave shows as a bare lobe behind the shell.
                            scale = 1+(scale-1)*SKIN
                        # Inner contours already register with the painting; the outer
                        # ones were proud of it. Grow toward the midline, front and back.
                        if part == 'calf' and radial.length > 1e-6:
                            outward = radial.normalized().x*(1 if side == 'l' else -1)
                            scale = 1+(scale-1)*(1-OUTER*max(0., outward))
                        move += radial*(scale-1)*g.weight
                    elif part in ('foot', 'ball'):
                        ankle = bones['foot_'+side].head_local
                        centre = Vector((ankle.x, ankle.y, sole_z[side]))
                        rel = p-centre
                        move += Vector((rel.x*(FOOT.x-1), rel.y*(FOOT.y-1), rel.z*(FOOT.z-1)))*g.weight
                if move.length > 1e-7:
                    vertex.co = back @ (p+move)
                    count += 1
            if count:
                ob.data.update()
                changed[ob.name] = count
        elif ob.parent == rig and ob.parent_type == 'BONE' and ob.parent_bone.startswith('calf_'):
            # Rigid chased ornament riding the greave: same field in the posed calf frame.
            pose = rig.pose.bones[ob.parent_bone]
            head = rig.matrix_world @ pose.head
            tail = rig.matrix_world @ pose.tail
            axis = (tail-head)
            length = axis.length
            axis.normalize()
            world = ob.matrix_world
            back = world.inverted()
            for vertex in ob.data.vertices:
                p = world @ vertex.co
                rel = p-head
                along = rel.dot(axis)
                radial = rel-axis*along
                scale = calf_scale(along/length)
                if radial.length > 1e-6:
                    local = (rig.matrix_world.inverted().to_3x3() @ radial).normalized()
                    rest_out = (pose.matrix.to_3x3().inverted() @ local)
                    rest_out = (pose.bone.matrix_local.to_3x3() @ rest_out).x*(1 if ob.parent_bone.endswith('_l') else -1)
                    scale = 1+(scale-1)*(1-OUTER*max(0., rest_out))
                vertex.co = back @ (p+radial*(scale-1))
            ob.data.update()
            changed[ob.name] = len(ob.data.vertices)
    scene['spearman_stance_round'] = 'fable-b'
    bpy.context.view_layer.update()
    print('STANCE_FABLE_B', len(changed), 'meshes', sum(changed.values()), 'vertices', sorted(changed)[:12])


def flare_cloak(scene, screen_sculpt):
    """Spear-side cloak edge: the painting's wool hangs outside the spear arm
    from the elbow to the knee and lower between the legs. Screen-space fit in
    the guard pose, returned through each vertex's blended skin transform (the
    round-9a method), before the painting UVs are frozen."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Matrix
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}
    ob = bpy.data.objects['Cloak • simulated wool']
    count = 0
    for vertex in ob.data.vertices:
        influences = [(transforms[ob.vertex_groups[g.group].name], g.weight) for g in vertex.groups
                      if ob.vertex_groups[g.group].name in transforms]
        total = sum(w for _, w in influences)
        if total < .001:
            continue
        skin = sum((m*(w/total) for m, w in influences), Matrix(((0,)*4,)*4))
        posed = skin @ vertex.co
        camera = world_to_camera_view(scene, scene.camera, ob.matrix_world @ posed)
        p = Vector((camera.x*256, (1-camera.y)*256))
        smooth = lambda a, b, x: (lambda t: t*t*(3-2*t))(max(0., min(1., (x-a)/(b-a))))
        # Left (spear-side) edge: widest at hip height, fading at shoulder and hem.
        edge = smooth(124, 104, p.x)*smooth(108, 140, p.y)*(1-.5*smooth(185, 215, p.y))
        # Centre hem between the legs hangs about four pixels lower.
        hem = smooth(120, 135, p.x)*(1-smooth(150, 166, p.x))*smooth(170, 195, p.y)
        delta = Vector((-6.0*edge, 4.0*hem))
        if delta.length < .01:
            continue
        vertex.co = skin.inverted_safe() @ screen_sculpt(ob, posed, p+delta)
        count += 1
    ob.data.update()
    bpy.context.view_layer.update()
    print('CLOAK_FLARE_FABLE_B', count, 'vertices')

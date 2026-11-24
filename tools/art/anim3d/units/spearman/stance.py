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

THIGH, KNEE, MID, ANKLE = 1.12, 1.18, 1.0, 1.20
FOOT = Vector((1.32, 1.30, 1.18))
SHAFT = 1.75
BASE = .965
BAND = .008
SKIN = .5
SPEAR_SIDE_TRIM = .32
OUTER = 1.5


def calf_scale(t):
    # t: 0 at the knee joint, 1 at the ankle. Measured against the painting at
    # 256 px: a 14 px knee cap, a 9 px shin, a slightly heavier ankle.
    t = max(0., min(1., t))
    if t < .5:
        u = t/.5
        return KNEE+(MID-KNEE)*u*u*(3-2*u)
    u = (t-.5)/.5
    return MID+(ANKLE-MID)*u*u*(3-2*u)


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
                        if part == 'calf' and radial.length > 1e-6:
                            # Both painted shins sit about 1.5 px toward the spear side of
                            # the modelled ones between knee and ankle (rows 190-202).
                            u = max(0., min(1., along/length))
                            scale -= SPEAR_SIDE_TRIM*max(0., radial.normalized().x)*(4*u*(1-u))**.5
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
    # The chased spirals were seated on the old greave and now float beside the
    # fuller shell as rings; the projected painting already carries that
    # ornament. Hidden by visibility, never by scale.
    for ob in scene.objects:
        if ob.name.startswith('Greave chased spiral'):
            ob.hide_render = True
            ob.hide_viewport = True
    # The painted dory is a stout pole about four pixels wide at 256 px; the
    # modelled shaft was a two-pixel line. Radius only; paint is the look lane's.
    for ob in scene.objects:
        if ob.type == 'CURVE' and ob.name.startswith(('Ash dory shaft', 'Spear bronze ferrule', 'Iron spear butt')):
            ob.data.bevel_depth *= SHAFT
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
        edge = smooth(124, 104, p.x)*smooth(108, 140, p.y)*(1-.6*smooth(198, 222, p.y))
        # Centre hem between the legs hangs about four pixels lower.
        hem = smooth(120, 135, p.x)*(1-smooth(150, 166, p.x))*smooth(170, 195, p.y)
        delta = Vector((-4.5*edge, 5.0*hem))
        # Level hem behind the legs: the painted wool ends near y 190 in three
        # shallow scallops; the modelled tail sloped down past the shield-side
        # greave and widened both shins in silhouette.
        import math
        line = 191+2.0*math.cos((p.x-128)/27*2*math.pi)
        over = p.y+delta.y-line
        if over > 0 and 99 < p.x < 172:
            delta.y -= over*.9
        if delta.length < .01:
            continue
        vertex.co = skin.inverted_safe() @ screen_sculpt(ob, posed, p+delta)
        count += 1
    ob.data.update()
    bpy.context.view_layer.update()
    print('CLOAK_FLARE_FABLE_B', count, 'vertices')


def brace_feet(scene):
    """Shield-side foot turned out, as painted: the two sandals diverge on the
    stone. A yaw about the vertical through the ankle keeps the sole flat. Guard
    pose only; the walk's feet come from the retarget and are not touched."""
    import math
    from mathutils import Matrix
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    for name, angle in [('foot_l', math.radians(38)), ('foot_r', math.radians(10))]:
        bone = rig.pose.bones[name]
        pivot = bone.head.copy()
        bone.matrix = Matrix.Translation(pivot) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Translation(-pivot) @ bone.matrix
        bpy.context.view_layer.update()
    # The painted disc is a little smaller than the modelled one.
    base = bpy.data.objects['Stationary cream stone']
    top = max(v.co.z for v in base.data.vertices)
    for v in base.data.vertices:
        v.co.x *= BASE
        v.co.y *= BASE
        if v.co.z < top-.001:
            v.co.z -= BAND
    base.data.update()
    bpy.context.view_layer.update()

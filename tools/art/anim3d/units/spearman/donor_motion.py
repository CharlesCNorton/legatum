"""KayKit CC0 reactions, calibrated in full reference rotations onto MPFB.

The action owns joint rotations. The target's guard is the reference; root
height follows donor contact rather than the cartoon donor's short proportions.
No target foot rotations are authored. Idle/move still use Quaternius.
"""
import hashlib
import os
import bpy
from mathutils import Matrix, Vector
from kit.retarget import apply_matrices
from motion import curve

from kit.retarget_presets import KAYKIT_MAP as MAP, KAYKIT_ACTIONS


def prepare(rig, root, clip, phases):
    scene = bpy.context.scene
    path = root/'assets/kaykit-character-animations-1.1/Rig_Medium_General.glb'
    expected = '5f725c0f745f36078c7238968cd5c04843cbc6260689eb6e7f5e2bbd7ffdd7ad'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    neutral = {p.name: p.matrix.copy() for p in rig.pose.bones}
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = set(bpy.data.objects)-before
    source = next(o for o in imported if o.type == 'ARMATURE')
    for track in source.animation_data.nla_tracks:
        track.mute = True
    name = os.environ.get('SPEARMAN_DONOR_ACTION', KAYKIT_ACTIONS[clip])
    action = bpy.data.actions[name]
    source.animation_data.action = action
    source.animation_data.action_slot = action.slots[0]
    first, last = action.frame_range
    scene.frame_set(int(first))
    reference = {n: source.pose.bones[n].matrix.copy() for n in set(MAP.values())}
    hip0 = source.pose.bones['hips'].head.copy()
    arm_reference = {p.name:p.rotation_quaternion.copy() for p in source.pose.bones
                     if p.name.startswith(('upperarm.', 'lowerarm.', 'wrist.', 'hand.'))}
    constraints, helpers = [], []
    neutral_basis = {p.name:p.matrix_basis.copy() for p in rig.pose.bones}
    for target, origin in MAP.items():
        helper = bpy.data.objects.new('KAY reference '+target, None)
        scene.collection.objects.link(helper)
        helper.parent = source
        helper.parent_type = 'BONE'
        helper.parent_bone = origin
        helper.matrix_parent_inverse = Matrix.Identity(4)
        source_ref, target_ref = reference[origin], neutral[target]
        if clip == 'death' and target.startswith(('thigh_', 'calf_', 'foot_', 'ball_')):
            source_ref = source.data.bones[origin].matrix_local
            target_ref = rig.data.bones[target].matrix_local.copy()
            swing = (target_ref.to_3x3()@Vector((0,1,0))).rotation_difference(
                source_ref.to_3x3()@Vector((0,1,0)))
            position = target_ref.translation.copy()
            target_ref = swing.to_matrix().to_4x4()@target_ref
            target_ref.translation = position
        helper.matrix_basis = (Matrix.Translation((0, -source.data.bones[origin].length, 0))
                               @ source_ref.inverted() @ target_ref)
        constraint = rig.pose.bones[target].constraints.new('COPY_ROTATION')
        constraint.target = helper
        constraint.owner_space = constraint.target_space = 'WORLD'
        constraints.append((rig.pose.bones[target], constraint))
        helpers.append(helper)
    scale = sum(rig.data.bones[n+'_l'].length for n in ('thigh', 'calf')) / sum(
        source.data.bones[n+'.l'].length for n in ('upperleg', 'lowerleg'))
    foot0 = min(source.pose.bones['foot.'+s].head.z for s in ('l', 'r'))
    target_foot0 = min(neutral['foot_'+s].translation.z for s in ('l', 'r'))
    source_foot0 = {s:source.pose.bones['foot.'+s].head.z for s in ('l','r')}
    target_foot0_world = {s:(rig.matrix_world@neutral['foot_'+s].translation).z for s in ('l','r')}
    frames = []
    for phase in phases:
        # First recoil, knee yield, then spend four samples on the actual fall.
        donor_phase = (curve(phase, [0, .10, .25, .51, .55, .58, .61, .65, .82, .82])
                       if clip == 'death' else curve(phase, [0, .12, .48, 1]))
        if clip == 'death':
            blend = min(1.,phase/.18)
            blend = blend*blend*(3-2*blend)
            for p,c in constraints:
                if p.name.startswith(('thigh_', 'calf_', 'foot_', 'ball_')):
                    c.influence = blend
                    p.location = neutral_basis[p.name].translation*(1-blend)
        f = first+(last-first)*donor_phase
        scene.frame_set(int(f), subframe=f-int(f))
        # Blend source-local arm deltas toward the donor's own initial carry.
        # The falling/recoiling torso still transports both attached arms.
        for bone, rotation in arm_reference.items():
            p = source.pose.bones[bone]
            p.rotation_quaternion = rotation.slerp(p.rotation_quaternion, .30)
        bpy.context.view_layer.update()
        matrices = {p.name: p.matrix.copy() for p in rig.pose.bones}
        root_offset = (source.pose.bones['hips'].head-hip0)*scale
        if clip == 'hit':
            # Keep the guarded legs planted; torso recoil comes from the donor.
            # The source's step-back is inappropriate on a stationary stone.
            root_offset = Vector()
            for target in matrices:
                if target.startswith(('thigh_', 'calf_', 'foot_', 'ball_')):
                    matrices[target] = neutral[target].copy()
            if phase >= 1 or phase <= 0:
                matrices = {n: m.copy() for n, m in neutral.items()}
                root_offset = Vector()
        else:
            # Match vertical source contact using the actual retargeted ankle,
            # accounting for the very different source pelvis/leg proportions.
            desired = target_foot0 + (min(source.pose.bones['foot.'+s].head.z for s in ('l', 'r'))-foot0)*scale
            root_offset.z = desired-min(matrices['foot_'+s].translation.z for s in ('l', 'r'))
        frames.append({'matrices': matrices, 'root': root_offset,
                       'ankle_height': {s:target_foot0_world[s]+(source.pose.bones['foot.'+s].head.z-source_foot0[s])*scale
                                        for s in ('l','r')}})
    for p, constraint in constraints:
        p.constraints.remove(constraint)
    for ob in helpers+list(imported):
        bpy.data.objects.remove(ob, do_unlink=True)
    apply_matrices(rig, neutral)
    scene.frame_set(1)
    return frames, {'provider': 'KayKit Character Animations Free 1.1', 'action': name,
                    'license': 'CC0-1.0', 'sha256': expected, 'map': MAP,
                    'method': 'reference/roll calibrated WORLD Copy Rotation; source contact height',
                    'source_frames': [first, last], 'leg_scale': scale}


def delivery_samples(scene, rig, shield, first, last, count):
    """Spend the ten-frame budget on measured body/attached-shield travel.

Select existing dense donor poses; never interpolate a new human performance.
The last two samples hold. Contact and cloth still run at their original 24 Hz.
"""
    rows = []
    for frame in range(first, last+1):
        scene.frame_set(frame)
        rows.append((frame, rig.matrix_world@rig.pose.bones['head'].head,
                     rig.matrix_world@rig.pose.bones['pelvis'].head,
                     shield.matrix_world.to_quaternion().copy()))
    head_travel, shield_travel = [0.], [0.]
    for a,b in zip(rows,rows[1:]):
        head_travel.append(head_travel[-1]+(a[1]-b[1]).length+.15*(a[2]-b[2]).length)
        shield_travel.append(shield_travel[-1]+a[3].rotation_difference(b[3]).angle)
    # Minimize the worst delivered head displacement or shield angle.
    # Cumulative arc length alone overweights harmless motion between frames.
    # Squared arc length breaks equal endpoint-cost ties to preserve staging.
    import math
    n = len(rows)
    previous = {0:(0.,0.)}
    parents = []
    for step in range(count-2):
        current, parent = {}, {}
        for end in range(step+1,n):
            choices = []
            for begin,score in previous.items():
                if begin >= end:
                    continue
                cost = max((rows[end][1]-rows[begin][1]).length/.38,
                           rows[end][3].rotation_difference(rows[begin][3]).angle/math.radians(30))
                arc = max((head_travel[end]-head_travel[begin])/.38,
                          (shield_travel[end]-shield_travel[begin])/math.radians(30))
                choices.append(((max(score[0],cost),score[1]+arc*arc),begin))
            if choices:
                current[end],parent[end] = min(choices)
        previous = current
        parents.append(parent)
    indices = [n-1]
    for parent in reversed(parents):
        indices.append(parent[indices[-1]])
    frames = [rows[i][0] for i in reversed(indices)]
    assert len(set(frames)) == count-1, 'Death sampling repeated an active pose'
    return frames+[frames[-1]]


def clear_sandals(rig):
    """Ground the evaluated straps as well as the sole after contact IK.

On a bent death foot a strap can become the lowest surface. Translate ankle
contacts through IK, holding the donor's foot rotation and rigid bone lengths.
"""
    from kit.retarget import contact_ik
    base = bpy.data.objects['Stationary cream stone']
    floor = max((base.matrix_world@v.co).z for v in base.data.vertices)+.001
    inverse = base.matrix_world.inverted()
    radius = max((v.co.x*v.co.x+v.co.y*v.co.y)**.5 for v in base.data.vertices)-.015
    for _ in range(4):
        corrections = {}
        dg = bpy.context.evaluated_depsgraph_get()
        for side in ('l','r'):
            lift = 0.
            for ob in bpy.context.scene.objects:
                if ob.type != 'MESH' or not ob.name.startswith(('Sandal', 'Leather sandal')) or 'foot_'+side not in ob.vertex_groups:
                    continue
                evaluated=ob.evaluated_get(dg)
                mesh=evaluated.to_mesh()
                for vertex in mesh.vertices:
                    point=ob.matrix_world@vertex.co
                    local=inverse@point
                    plane=floor if local.x*local.x+local.y*local.y<radius*radius else .006
                    lift=max(lift,plane-point.z)
                evaluated.to_mesh_clear()
            if lift>.00002:
                corrections[side]=Vector((0,0,lift))
        if not corrections:
            break
        contact_ik(rig,corrections)

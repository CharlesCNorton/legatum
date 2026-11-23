"""Blender constraint retarget of CC0 Quaternius actions onto MPFB.

Offsets are calibrated once in rest/reference poses, including bone roll. Blender
then evaluates full rotations (not reconstructed joint direction/FK). Foot
rotation is never edited after retargeting. The mannequin is not rendered.
"""
import hashlib
import json
import statistics
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ACTIONS = {'idle': 'Idle_Loop', 'move': 'Walk_Loop',
           'hit': 'Hit_Chest', 'death': 'Death01'}
MAP = {'pelvis': 'DEF-hips', 'spine_01': 'DEF-spine.001',
       'spine_02': 'DEF-spine.002', 'spine_03': 'DEF-spine.003',
       'neck_01': 'DEF-neck', 'head': 'DEF-head'}
for side, suffix in [('l', 'L'), ('r', 'R')]:
    for target, source in [('clavicle', 'shoulder'), ('upperarm', 'upper_arm'),
                           ('lowerarm', 'forearm'), ('hand', 'hand'),
                           ('thigh', 'thigh'), ('calf', 'shin'),
                           ('foot', 'foot'), ('ball', 'toe')]:
        MAP[target+'_'+side] = 'DEF-'+source+'.'+suffix


def apply_matrices(rig, matrices):
    # Blender's own pose-to-local conversion takes the sampled parent matrix
    # explicitly. Assigning p.matrix repeatedly otherwise reads stale evaluated
    # parents and compounds transforms down the chain in background baking.
    for p in rig.pose.bones:
        args = {'parent_matrix': matrices[p.parent.name],
                'parent_matrix_local': p.parent.bone.matrix_local} if p.parent else {}
        p.matrix_basis = p.bone.convert_local_to_pose(
            matrices[p.name], p.bone.matrix_local, invert=True, **args)
    bpy.context.view_layer.update()


def stabilize_walk(rig, frames, phases, scale):
    """Small root contact correction; never alter retargeted bone rotations.

The in-place source has slightly unequal stance speeds. Lock flat planted
ankles to one virtual ground speed, blend the root offset across toe-off, and
retain the captured swing/roll. Landing frames still moving forward are not
classified as planted. The closing frame anchors the loop to its starting pose.
"""
    active = [i for i,p in enumerate(phases) if i>=24]
    minima = {s:min(frames[i]['source_feet'][s][2] for i in active) for s in ['l','r']}
    planted = {s:[] for s in ['l','r']}
    velocities = []
    for side in ['l','r']:
        for i in active:
            nxt = i+1 if i+1<len(frames) else 25
            point, following = frames[i]['source_feet'][side], frames[nxt]['source_feet'][side]
            flag = point[2] < minima[side]+.015 and following[1] > point[1]
            planted[side].append(flag)
            if flag and nxt==i+1 and following[2]<minima[side]+.015:
                velocities.append((following[1]-point[1])*24*scale)
    speed = statistics.median(velocities)
    offsets = {}
    for side in ['l','r']:
        anchor = None
        for i, flag in zip(active,planted[side]):
            if not flag:
                anchor = None
                continue
            position = frames[i]['matrices']['foot_'+side].translation + frames[i]['root']
            if anchor is None:
                anchor = (i,position.copy())
            offset = anchor[1]+Vector((0,speed*(i-anchor[0])/24,0))-position
            offset.z = 0
            offsets[i] = offset
    offsets[24] = Vector((0,0,0))
    offsets[len(frames)-1] = Vector((0,0,0))
    keys = sorted(offsets)
    for i in active:
        if i not in offsets:
            a = max(k for k in keys if k<i)
            b = min(k for k in keys if k>i)
            t = (i-a)/(b-a); t = t*t*(3-2*t)
            offsets[i] = offsets[a].lerp(offsets[b],t)
        frames[i]['root'] += offsets[i]
    maximum = max(v.length for v in offsets.values())
    assert maximum < .04, f'Contact correction too large: {maximum:.4f}m; fix rest mapping'
    return {'virtual_forward_speed_m_s': speed, 'max_root_xy_correction_m': maximum,
            'planted': {str(i+1): {side: planted[side][j] for side in planted} for j,i in enumerate(active)}}


def prepare(rig, root, clip, phases):
    """Sample Blender's constraint graph, return visual target matrices per phase."""
    scene = bpy.context.scene
    source_path = root/'assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf'
    for name, expected in {
        'AnimationLibrary_Godot_Standard.gltf': '0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765',
        'AnimationLibrary_Godot_Standard.bin': '6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c',
    }.items():
        assert hashlib.sha256((source_path.parent/name).read_bytes()).hexdigest() == expected, name
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(source_path))
    imported = set(bpy.data.objects)-before
    source = next(o for o in imported if o.type == 'ARMATURE')
    for track in source.animation_data.nla_tracks:
        track.mute = True
    action = bpy.data.actions[ACTIONS[clip]]
    source.animation_data.action = action
    source.animation_data.action_slot = action.slots[0]
    first, last = action.frame_range
    carry = None
    if clip == 'move':
        # A spear/shield carrier cannot swing both arms as an unarmed walker.
        # Layer the open idle's arms with Blender NLA; no new hand-authored gait.
        carry = source.copy()
        scene.collection.objects.link(carry)
        imported.add(carry)
        carry.animation_data_clear()
        carry.animation_data_create()
        track = carry.animation_data.nla_tracks.new()
        idle = bpy.data.actions['Idle_Loop']
        strip = track.strips.new('Open idle carrying arms', int(first), idle)
        strip.action_slot = idle.slots[0]
        strip.action_frame_start, strip.action_frame_end = idle.frame_range
        strip.frame_end = last
    scene.frame_set(int(first))
    bpy.context.view_layer.update()
    reference = {n: source.pose.bones[n].matrix.copy() for n in MAP.values()}
    neutral = {p.name: p.matrix.copy() for p in rig.pose.bones}
    constraints, helpers = [], []
    for target, origin in MAP.items():
        if target not in rig.pose.bones:
            continue
        p = rig.pose.bones[target]
        donor = carry if carry and target.startswith(('clavicle_', 'upperarm_', 'lowerarm_', 'hand_')) else source
        # Upper body stays in its weapon-bearing guard, with the complete source
        # delta layered on it. Locomotion legs use anatomical rest, not the
        # painting's braced stance. Both mappings include complete bone rolls.
        locomotion_leg = clip == 'move' and target.startswith(('thigh_', 'calf_', 'foot_', 'ball_'))
        source_ref = source.data.bones[origin].matrix_local if locomotion_leg else donor.pose.bones[origin].matrix.copy()
        target_ref = p.bone.matrix_local.copy() if locomotion_leg else neutral[target]
        if locomotion_leg:
            # MPFB's anatomical rest has spread legs; the source is a straight
            # T-pose. Match the limb axes in the calibration pose, retaining the
            # target roll, rather than carrying that spread into every step.
            target_axis = target_ref.to_3x3() @ Vector((0,1,0))
            source_axis = source_ref.to_3x3() @ Vector((0,1,0))
            swing = target_axis.rotation_difference(source_axis)
            position = target_ref.translation.copy()
            target_ref = swing.to_matrix().to_4x4() @ target_ref
            target_ref.translation = position
        offset = source_ref.inverted() @ target_ref
        helper = bpy.data.objects.new('RETARGET '+target, None)
        scene.collection.objects.link(helper)
        helper.parent = donor
        helper.parent_type = 'BONE'
        helper.parent_bone = origin
        helper.matrix_parent_inverse = Matrix.Identity(4)
        helper.matrix_basis = Matrix.Translation((0, -source.data.bones[origin].length, 0)) @ offset
        helpers.append(helper)
        constraint = p.constraints.new('COPY_ROTATION')
        constraint.name = 'Quaternius rest-space rotation'
        constraint.target = helper
        constraint.owner_space = constraint.target_space = 'WORLD'
        constraints.append((p, constraint))
    hip0 = reference['DEF-hips'].translation.copy()
    # Leg-length scale preserves captured stride and vertical displacement.
    scale = sum(rig.data.bones[n+'_l'].length for n in ['thigh', 'calf']) / sum(source.data.bones[n].length for n in ['DEF-thigh.L', 'DEF-shin.L'])
    frames = []
    for phase in phases:
        frame = first+(last-first)*max(0, min(1, phase))
        scene.frame_set(int(frame), subframe=frame-int(frame))
        bpy.context.view_layer.update()
        hip = source.pose.bones['DEF-hips'].head.copy()
        frames.append({'matrices': {p.name: p.matrix.copy() for p in rig.pose.bones},
                       'root': (hip-hip0)*scale,
                       'source_feet': {s: list(source.pose.bones['DEF-foot.'+s.upper()].head) for s in ['l', 'r']},
                       'source_toes': {s: list(source.pose.bones['DEF-toe.'+s.upper()].head) for s in ['l', 'r']}})
    contact = stabilize_walk(rig,frames,phases,scale) if clip=='move' else None
    for p, constraint in constraints:
        p.constraints.remove(constraint)
    for ob in helpers+list(imported):
        bpy.data.objects.remove(ob, do_unlink=True)
    apply_matrices(rig, neutral)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return frames, {'provider': 'Quaternius Universal Animation Library Standard',
                    'action': ACTIONS[clip], 'arm_layer': 'Idle_Loop via Blender NLA' if carry else None, 'license': 'CC0-1.0',
                    'method': 'Blender COPY_ROTATION WORLD, calibrated reference/rest matrices including roll',
                    'source_frames': [first, last], 'leg_scale': scale,
                    'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    'map': MAP, 'contact': contact, 'samples': [{'phase': phase, 'ankles': f['source_feet'], 'toes': f['source_toes']} for phase,f in zip(phases,frames)]}

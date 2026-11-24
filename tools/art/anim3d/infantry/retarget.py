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
from contact import landmarks
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'units/spearman'))
from motion import source_phase, hit_envelope

import os
ACTIONS = {'idle': 'Idle_Loop', 'move': os.environ.get('MOVE_ACTION', 'Walk_Loop'),
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
    """Lock heel strike, flat stance AND toe-off, including wraparound support.

Use evaluated sandal landmarks, a single fitted virtual speed and small native
IK corrections. Source rotations are immutable. Cyclic support intervals keep
a foot planted across the loop boundary instead of resetting its contact.
"""
    count=len(frames)-25
    indices=list(range(24,24+count))
    flags={}; segments={}; source_speeds=[]
    for side in ['l','r']:
        ankle_min=min(frames[i]['source_feet'][side][2] for i in indices)
        toe_min=min(frames[i]['source_toes'][side][2] for i in indices)
        flags[side]=[]
        for j,i in enumerate(indices):
            nxt=indices[(j+1)%count]
            ankle=frames[i]['source_feet'][side]; toe=frames[i]['source_toes'][side]
            na=frames[nxt]['source_feet'][side]; nt=frames[nxt]['source_toes'][side]
            # Rest-space source blending introduces a small stance-height arc.
            # Classify its near-floor interval, then solve the *actual* target
            # sole to the unchanged 2mm floor / 1mm slip validation limits.
            contact=(ankle[2]<ankle_min+.015 and na[1]>ankle[1]) or (toe[2]<toe_min+.012 and nt[1]>toe[1])
            flags[side].append(contact)
            if contact and toe[2]<toe_min+.012 and nt[2]<toe_min+.012:
                source_speeds.append((nt[1]-toe[1])*24*scale)
        starts=[j for j in range(count) if flags[side][j] and not flags[side][(j-1)%count]]
        assert len(starts)==1,(side,starts)
        segment=[];j=starts[0]
        while flags[side][j%count]:
            segment.append(j);j+=1
            assert len(segment)<count,'Walking foot never leaves ground'
        segments[side]=segment
    source_speed=statistics.median(source_speeds)
    def fit(speed):
        result={}
        for side,segment in segments.items():
            offsets={};anchor=None
            for step in segment:
                i=indices[step%count]
                points={mode:point+frames[i]['root'] for mode,point in frames[i]['sole_landmarks'][side].items()}
                mode=min(points,key=lambda m:points[m].z);point=points[mode]
                if anchor is None:anchor=(step,point.copy(),mode)
                elif mode!=anchor[2]:anchor=(step,point+offsets[(step-1)%count],mode)
                offset=anchor[1]+Vector((0,speed*(step-anchor[0])/24,0))-point
                offset.z=0;offsets[step%count]=offset
            # A constant registration offset does not change motion. Center the
            # corrections rather than privileging the arbitrary first frame.
            center=Vector(((min(v.x for v in offsets.values())+max(v.x for v in offsets.values()))/2,
                           (min(v.y for v in offsets.values())+max(v.y for v in offsets.values()))/2,0))
            offsets={j:v-center for j,v in offsets.items()}
            first,last=segment[0],segment[-1]
            gap=count-len(segment)+1
            for k in range(1,gap):
                t=k/gap;t=t*t*(3-2*t)
                offsets[(last+k)%count]=offsets[last%count].lerp(offsets[first%count],t)
            result[side]=offsets
        return result
    candidates=[source_speed*(.75+i*.005) for i in range(101)]
    speed=min(candidates,key=lambda v:max(o.length for side in fit(v).values() for o in side.values()))
    offsets=fit(speed);root_max=0;ik_max=0
    for j,i in enumerate(indices+[len(frames)-1]):
        phase=j%count
        root_offset=(offsets['l'][phase]+offsets['r'][phase])*.5
        frames[i]['root']+=root_offset
        frames[i]['foot_corrections']={side:offsets[side][phase]-root_offset for side in ['l','r']}
        root_max=max(root_max,root_offset.length)
        ik_max=max(ik_max,max(v.length for v in frames[i]['foot_corrections'].values()))
    for i in range(24):
        frames[i]['root']=frames[24]['root'].copy()
        frames[i]['foot_corrections']=frames[24]['foot_corrections']
    assert max(root_max,ik_max)<.05,('Contact correction too large',root_max,ik_max)
    return {'source_ankle_speed_m_s':source_speed,'virtual_forward_speed_m_s':speed,
            'max_root_xy_correction_m':root_max,'max_foot_ik_correction_m':ik_max,
            'planted':{str(i+1):{side:flags[side][j%count] for side in flags}
                       for j,i in enumerate(indices+[len(frames)-1])}}


def contact_ik(rig, corrections):
    """Blender two-bone IK translates the contact, retaining source foot rolls."""
    controls=[];constraints=[]
    for side,offset in corrections.items():
        foot=rig.pose.bones['foot_'+side]
        target=bpy.data.objects.new('CONTACT ankle '+side,None)
        rotation=bpy.data.objects.new('CONTACT source rotation '+side,None)
        for ob in [target,rotation]:bpy.context.scene.collection.objects.link(ob)
        target.location=rig.matrix_world @ foot.head+offset
        rotation.matrix_world=rig.matrix_world @ foot.matrix
        ik=rig.pose.bones['calf_'+side].constraints.new('IK')
        ik.target=target;ik.chain_count=2;ik.use_stretch=False
        keep=foot.constraints.new('COPY_ROTATION');keep.target=rotation
        keep.owner_space=keep.target_space='WORLD'
        controls.extend([target,rotation]);constraints.extend([(rig.pose.bones['calf_'+side],ik),(foot,keep)])
    bpy.context.view_layer.update()
    visual={p.name:p.matrix.copy() for p in rig.pose.bones}
    for p,constraint in constraints:p.constraints.remove(constraint)
    for ob in controls:bpy.data.objects.remove(ob,do_unlink=True)
    apply_matrices(rig,visual)


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
    if clip == 'move':
        # Attenuate the COMPLETE source action in its own rest space, before
        # reference calibration/retargeting. This reduces the high stepping of
        # the stylized donor without inventing a gait or editing target feet.
        source.animation_data.action = None
        track = source.animation_data.nla_tracks.new()
        walk = track.strips.new('Restrained open walk', int(first), action)
        walk.action_slot = action.slots[0]
        walk.blend_type = 'REPLACE'
        walk.use_animated_influence = True
        walk.influence = .92
        walk.keyframe_insert(data_path='influence', frame=first)
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
    if clip == 'move':
        # Remove the painted guard's local ankle translations as well as its
        # rotations before building the matched T-pose. They are not anatomy.
        for p in rig.pose.bones:
            if p.name.startswith(('thigh_','calf_','foot_','ball_')):p.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
    constraints, helpers = [], []
    for target, origin in MAP.items():
        if target not in rig.pose.bones:
            continue
        p = rig.pose.bones[target]
        donor = carry if carry and target.startswith(('clavicle_', 'upperarm_', 'lowerarm_', 'hand_')) else source
        # Upper body stays in its weapon-bearing guard, with the complete source
        # delta layered on it. Locomotion legs use anatomical rest, not the
        # painting's braced stance. Both mappings include complete bone rolls.
        locomotion_leg = (clip == 'move' and target.startswith(('thigh_', 'calf_', 'foot_', 'ball_'))) or clip=='death'
        source_ref = source.data.bones[origin].matrix_local if locomotion_leg else donor.pose.bones[origin].matrix.copy()
        target_ref = p.bone.matrix_local.copy() if locomotion_leg else neutral[target]
        if locomotion_leg and target.startswith(('thigh_','calf_','foot_','ball_','upperarm_','lowerarm_','hand_')):
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
        motion_phase=source_phase(clip, phase)
        frame = first+(last-first)*max(0, min(1, motion_phase))
        hit_weight=1
        if clip=='hit':
            hit_weight=hit_envelope(phase)
            for p,constraint in constraints:constraint.influence=hit_weight
        if clip=='death':
            blend=max(0,min(1,phase/.18));blend=blend*blend*(3-2*blend)
            for p,constraint in constraints:constraint.influence=blend
            for p in rig.pose.bones:
                p.location=Matrix(json.loads(rig['neutral_pose'])[p.name]).translation*(1-blend)
        scene.frame_set(int(frame), subframe=frame-int(frame))
        bpy.context.view_layer.update()
        hip = source.pose.bones['DEF-hips'].head.copy()
        frames.append({'matrices': {p.name: p.matrix.copy() for p in rig.pose.bones},
                       'root': (hip-hip0)*scale*hit_weight,
                       'sole_landmarks': {s:landmarks(s) for s in ['l','r']},
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
                    'action': ACTIONS[clip], 'source_action_influence': .92 if clip=='move' else 1,
                    'timing': 'r9c impact then settle; source rotations retained',
                    'arm_layer': 'Idle_Loop via Blender NLA' if carry else None, 'entry_blend_fraction': .18 if clip=='death' else 0, 'exit_blend_fraction': .70 if clip=='hit' else 0, 'license': 'CC0-1.0',
                    'method': 'Blender COPY_ROTATION WORLD, calibrated reference/rest matrices including roll',
                    'source_frames': [first, last], 'leg_scale': scale,
                    'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    'map': MAP, 'contact': contact, 'samples': [{'phase': phase, 'ankles': f['source_feet'], 'toes': f['source_toes']} for phase,f in zip(phases,frames)]}

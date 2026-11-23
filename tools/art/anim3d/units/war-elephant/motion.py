"""Sample the pinned CC0 quadruped, compensating its -Y forward / +Z up axes.

Only source motion data is retained. The horse mesh never enters the elephant
master. Fitted elephant feet use source swing timing with stationary contacts,
necessary for an in-place miniature on a fixed stone.
"""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

SHA = 'fbddb2c97179eca896ec69c985cd9cc74540484510776c400df64e088e9f2414'
ACTIONS = {'idle':'Idle', 'move':'Walk', 'hit':'Idle_HitReact_Left', 'death':'Death'}
FEET = {'front.near':'IKFrontLeg.L', 'front.far':'IKFrontLeg.R',
        'back.near':'IKBackLeg.L', 'back.far':'IKBackLeg.R'}


def sample(root, clips):
    path = root/'assets/horseman/Horse.glb'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SHA, 'Changed CC0 motion input'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    result = {}
    for clip, action_name in ACTIONS.items():
        rig.animation_data.action = None
        for bone in rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        action = bpy.data.actions['AnimalArmature|'+action_name]
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        count, _, loop = clips[clip]
        start, end = action.frame_range
        frames = []
        for i in range(count+int(loop)):
            t = i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1)
            f = start+(end-start)*t
            bpy.context.scene.frame_set(math.floor(f), subframe=f%1)
            bpy.context.view_layer.update()
            points = {}
            for name in ['Back','Body','Head',*FEET.values()]:
                p = rig.matrix_world @ rig.pose.bones[name].head
                points[name] = [-p.y,-p.x,p.z]
            frames.append(points)
        result[clip] = frames
    # Height and longitudinal motion drive the fitted target; all source
    # timings/values are recorded so adaptation can be reviewed independently.
    out = root/'masters/war-elephant/source-motion.json'
    out.write_text(json.dumps({'source_sha256':SHA,'actions':ACTIONS,'samples':result},indent=2)+'\n')
    return result


def move_targets(frames, index):
    result = {}
    for leg, name in FEET.items():
        values = [f[name] for f in frames]
        floor = min(p[2] for p in values)
        lift = max(0,frames[index][name][2]-floor)
        centre = sum(p[0] for p in values[:-1])/(len(values)-1)
        # Keep the planted sole fixed. The source swing arc is scaled to the
        # elephant's shorter stride; there is no post-retarget foot yaw patch.
        swing = min(1,lift/.08)
        swing = swing*swing*(3-2*swing)
        result[leg] = Vector(((frames[index][name][0]-centre)*.22*swing,0,lift*.32))
    return result

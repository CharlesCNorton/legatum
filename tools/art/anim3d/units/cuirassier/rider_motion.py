"""CC0 seated upper-body retarget; the saddle constrains pelvis and legs.

Adapted from the project's inspected keshig lane. Bone reference axes and rolls
are compensated before applying motion; no foot orientation patch is used.
"""
import bpy, hashlib, os
from pathlib import Path
from mathutils import Quaternion

def sample_rider(rig, clip, count, loop):
    root = Path(os.environ['ANIM_ROOT'])/'assets/quaternius-ual'
    pins = {
        'AnimationLibrary_Godot_Standard.gltf': '0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765',
        'AnimationLibrary_Godot_Standard.bin': '6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c',
        'LICENSE': 'a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499',
    }
    for name, digest in pins.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(root/'AnimationLibrary_Godot_Standard.gltf'))
    added = set(bpy.data.objects)-before
    source = next(o for o in added if o.type == 'ARMATURE')
    for track in source.animation_data.nla_tracks: track.mute = True
    action_name = {'hit':'Hit_Chest', 'death':'Death01'}.get(clip, 'Sitting_Idle_Loop')
    action = next(a for a in bpy.data.actions if a.name == action_name or a.name.endswith('|'+action_name))
    source.animation_data.action = action; source.animation_data.action_slot = action.slots[0]
    mapping = {'spine_01':'DEF-spine.001', 'spine_02':'DEF-spine.002',
               'spine_03':'DEF-spine.003', 'neck_01':'DEF-neck', 'head':'DEF-head'}
    scene = bpy.context.scene
    scene.frame_set(int(action.frame_range[0])); bpy.context.view_layer.update()
    reference = {s:source.pose.bones[s].matrix_basis.to_quaternion() for s in mapping.values()}
    samples = []
    for i in range(count+int(loop)):
        t = i/count if loop else min(i/(count-2 if clip == 'death' else count-1), 1)
        f = action.frame_range[0]+t*(action.frame_range[1]-action.frame_range[0])
        scene.frame_set(int(f), subframe=f%1); bpy.context.view_layer.update()
        deltas = {}
        for name, src in mapping.items():
            delta = reference[src].inverted() @ source.pose.bones[src].matrix_basis.to_quaternion()
            basis = rig.data.bones[name].matrix_local.to_quaternion().inverted() @ source.data.bones[src].matrix_local.to_quaternion()
            weight = .25 if clip in ('idle', 'move', 'attack') else .6
            if clip=='death' and name in ('head','neck_01'):weight=.25
            deltas[name] = Quaternion().slerp(basis @ delta @ basis.inverted(), weight)
        samples.append(deltas)
    for ob in added: bpy.data.objects.remove(ob, do_unlink=True)
    return action_name, samples

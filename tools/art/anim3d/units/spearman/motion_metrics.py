"""Read-only body/equipment diagnostics for a saved, baked motion candidate.

Run with Blender through the gate. ANIM_ROOT selects the candidate; every row
retains its frame number. Numerical changes describe motion, not art approval.
"""
import hashlib
import json
import os
from pathlib import Path
import bpy
from mathutils import Vector

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
result = {}
for clip in ['move', 'death', 'hit', 'attack']:
    path = master/'clips'/clip/(clip+'.blend')
    if not path.exists():
        continue
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    shield = bpy.data.objects['Aspis control']
    frames = json.loads(scene['sample_frames'])
    rows = []
    cape_positions = []
    shield_rotations = []
    for frame in frames:
        scene.frame_set(frame)
        hand = rig.matrix_world @ rig.pose.bones['lowerarm_l'].tail
        points = {name: list(rig.matrix_world @ rig.pose.bones[name].head)
                  for name in ['head', 'pelvis', 'foot_l', 'foot_r']}
        points['shield_grip_distance_m'] = (shield.matrix_world.translation-hand).length
        points['frame'] = frame
        shield_rotations.append(shield.matrix_world.to_quaternion().copy())
        cape = bpy.data.objects['Cloak • simulated wool']
        evaluated = cape.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        cape_positions.append([cape.matrix_world @ v.co for v in mesh.vertices])
        evaluated.to_mesh_clear()
        rows.append(points)
    pins = cape.vertex_groups['Shoulder pins']
    pin_data = [(v.index, g.weight) for v in cape.data.vertices
                for g in v.groups if g.group == pins.index]
    result[clip] = {
        'cloth_pins_sha256': hashlib.sha256(json.dumps(pin_data).encode()).hexdigest(),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'rows': rows,
        'max_head_step_m': max((Vector(a['head'])-Vector(b['head'])).length
                              for a, b in zip(rows, rows[1:])),
        'head_vertical_range_m': max(r['head'][2] for r in rows)-min(r['head'][2] for r in rows),
        'max_ankle_height_m': max(r[s][2] for r in rows for s in ['foot_l', 'foot_r']),
        'shield_grip_distance_range_m': max(r['shield_grip_distance_m'] for r in rows)
                                      - min(r['shield_grip_distance_m'] for r in rows),
        'held_terminal_pose': rows[-1] == rows[-2],
        'max_shield_rotation_step_degrees': max(a.rotation_difference(b).angle*180/3.141592653589793
                                               for a,b in zip(shield_rotations,shield_rotations[1:])),
        'late_cape_max_vertex_travel_m': max((a-b).length for a,b in zip(cape_positions[-3],cape_positions[-1])),
    }
result['_receipt'] = {
    'blender': bpy.app.version_string,
    'build': bpy.app.build_hash.decode(),
    'master_sha256': hashlib.sha256((master/'spearman.blend').read_bytes()).hexdigest(),
    'painting_sha256': hashlib.sha256(Path('app/src/assets/units/spearman-256.png').read_bytes()).hexdigest(),
    'camera_matrix': [list(row) for row in scene.camera.matrix_world],
    'ortho_scale': scene.camera.data.ortho_scale,
    'view_transform': scene.view_settings.view_transform,
    'source_sha256': {name: hashlib.sha256((root/'assets/quaternius-ual'/name).read_bytes()).hexdigest()
                      for name in ['AnimationLibrary_Godot_Standard.gltf', 'AnimationLibrary_Godot_Standard.bin', 'LICENSE']},
}
path = root/'review/3d-v2/spearman-motion-weight.json'
path.write_text(json.dumps(result, indent=2))
print(path, flush=True)

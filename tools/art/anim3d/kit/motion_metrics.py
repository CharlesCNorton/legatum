"""Read-only motion diagnostics on a saved, baked clip: body, equipment, cloth.

Generalised from units/spearman/motion_metrics.py (round 10c). Contact audits
do not show weight or naturalness; these numbers describe what the delivered
samples do between frames. They are descriptions, not an art score:

- largest head step between delivered samples (ragdoll snap);
- highest ankle (feet-up recoil in a fall);
- attached equipment: grip distance range (did it stay in the hand) and the
  largest rotation step between delivered samples (does it flip);
- late cloth travel into the held final pose (is the cape still moving).

Spearman death, round 9 -> 10c: head step 1.277 -> 0.655 m, ankle 0.848 ->
0.355 m, shield grip range 1.142 m -> 0.0000002 m, shield rotation step
137.5 -> 83.0 degrees (still too large), late cape travel 0.419 -> 0.146 m.

Run through the `blender` gate with the clip .blend already open.
"""
import math

import bpy
from mathutils import Vector


def sample(scene, rig, frames, bones=('head', 'pelvis', 'foot_l', 'foot_r'),
           equipment=None, cloth=None):
    """Collect per-frame positions. `equipment` maps a label to (object, grip
    bone, 'head'|'tail'); `cloth` is an optional cloth object.
    """
    rows, rotations, cloth_positions = [], {name: [] for name in (equipment or {})}, []
    for frame in frames:
        scene.frame_set(frame)
        row = {'frame': frame}
        for name in bones:
            row[name] = list(rig.matrix_world @ rig.pose.bones[name].head)
        for label, (ob, bone, end) in (equipment or {}).items():
            grip = rig.matrix_world @ getattr(rig.pose.bones[bone], end)
            row[label+'_grip_distance_m'] = (ob.matrix_world.translation-grip).length
            rotations[label].append(ob.matrix_world.to_quaternion().copy())
        if cloth is not None:
            evaluated = cloth.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            cloth_positions.append([cloth.matrix_world @ v.co for v in mesh.vertices])
            evaluated.to_mesh_clear()
        rows.append(row)
    return rows, rotations, cloth_positions


def summarise(rows, rotations, cloth_positions, feet=('foot_l', 'foot_r'), settle=2):
    """Reduce samples to the headline numbers. `settle`: how many samples
    before the last to measure late cloth travel from (Spearman: 2).
    """
    report = {'max_head_step_m': max((Vector(a['head'])-Vector(b['head'])).length
                                     for a, b in zip(rows, rows[1:])),
              'head_vertical_range_m': max(r['head'][2] for r in rows)-min(r['head'][2] for r in rows),
              'max_ankle_height_m': max(r[s][2] for r in rows for s in feet),
              'held_terminal_pose': {k: v for k, v in rows[-1].items() if k != 'frame'}
                                    == {k: v for k, v in rows[-2].items() if k != 'frame'}}
    for label, quats in rotations.items():
        key = label+'_grip_distance_m'
        report[label+'_grip_distance_range_m'] = max(r[key] for r in rows)-min(r[key] for r in rows)
        report['max_'+label+'_rotation_step_degrees'] = max(
            math.degrees(a.rotation_difference(b).angle) for a, b in zip(quats, quats[1:]))
    if cloth_positions:
        report['late_cloth_max_vertex_travel_m'] = max(
            (a-b).length for a, b in zip(cloth_positions[-1-settle], cloth_positions[-1]))
    return report


def warnings(report, head_step=.8, rotation_step=45):
    """Flags worth a look in the strip. Starting thresholds from Spearman: the
    round-9 ragdoll death had a 1.28 m head step; the 83 degree shield step in
    round 10 still reads as a hinge flip.
    """
    found = []
    if report['max_head_step_m'] > head_step:
        found.append(f"head moves {report['max_head_step_m']:.2f} m between two delivered samples")
    for key, value in report.items():
        if key.endswith('_rotation_step_degrees') and value > rotation_step:
            found.append(f'{key} = {value:.1f}')
    return found

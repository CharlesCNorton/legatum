"""Donor-preserving swing clearance and hip weight shift (Blender)."""
import math

def shape_walk(rig, phase, planted, *, sway_m=.012, clearance_scale=2/3):
    """Lower the donor's swing arc; shift hips over support with feet fixed.

    Translation-only two-bone IK retains the retargeted foot/ball rotations.
    Measure clearance relative to the support sole before the final floor solve,
    so its root-height correction does not undo the lower swing arc.
    """
    import bpy
    from mathutils import Vector
    from kit.contact import sole_points
    from kit.retarget import contact_ik
    heights = {s: min(p.z for p in sole_points(s)) for s in ('l', 'r')}
    rotations = {n: rig.pose.bones[n].matrix.to_3x3().copy()
                 for n in ('foot_l', 'foot_r', 'ball_l', 'ball_r')}
    support = [heights[s] for s in heights if planted.get(s)]
    floor = min(support or heights.values())
    sway = sway_m * math.sin(2 * math.pi * phase)
    rig.location.x += sway
    bpy.context.view_layer.update()
    offsets = {s: Vector((-sway, 0, 0 if planted.get(s) else
                         -max(0, heights[s]-floor)*(1-clearance_scale))) for s in heights}
    contact_ik(rig, offsets)
    error = max(abs(rotations[n][i][j]-rig.pose.bones[n].matrix[i][j])
                for n in rotations for i in range(3) for j in range(3))
    assert error < 1e-5, ('walk shaping changed donor foot rotation', error)
    return {'hip_sway_amplitude_m': sway_m, 'swing_clearance_scale': clearance_scale,
            'max_swing_lowering_m': max(-v.z for v in offsets.values()),
            'max_foot_rotation_matrix_error': error}


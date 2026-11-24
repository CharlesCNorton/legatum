"""Walk-cycle feet check: sample the real soles, then measure contact.

Generalised from units/spearman/feet.py (rounds 9-10). `sample_dense` needs
Blender and a baked move clip; `measure`, `step_width` and `failures` are plain
Python over the sampled rows, so they can be tested and rerun without Blender.

The sprite walks in place, so a planted foot slides backward at the virtual
travel speed. Slip is measured after adding that travel back. Contact is read
from heel and toe landmarks on the evaluated sole, never from the ankle bone:
an ankle rolls forward over a planted sole (about 100 mm on Spearman) with no
slip at all.

Rows: [{'frame': f, 'feet': {'l': {...}, 'r': {...}}}] with per foot
`planted`, `ankle` [x,y,z], `sole_z`, `contact_mode` ('heel'|'toe'),
`contact_point` [x,y,z], `heading` (degrees from travel) and
`heading_projection_m` (toe-heel length on the ground).
"""
import math

# Enforced on Spearman since round 9. Tighten when a defect slips through;
# never loosen one to pass. Values in metres or degrees.
LIMITS = {'max_sole_contact_slip_m': .001, 'max_planted_floor_error_m': .002,
          'max_planted_heading_degrees': 10, 'max_readable_heading_degrees': 10,
          'loop_seam_m': .003, 'max_root_xy_correction_m': .05,
          'max_foot_ik_correction_m': .05, 'max_sole_translation_m': .04}
READABLE_FOOTPRINT_M = .08
SIDES = ('l', 'r')


def sample_dense(scene, rig, planted, first=25, sole_prefix='Leather sandal sole ',
                 foot_bone='foot_'):
    """Sample every frame from `first` to the scene end. `planted` is the
    retarget's contact table: {str(frame): {'l': bool, 'r': bool}}.
    Returns (rows, loop seam in metres).
    """
    from .contact import landmarks, sole_points
    rows = []
    for frame in range(first, scene.frame_end+1):
        scene.frame_set(frame)
        entry = {'frame': frame, 'feet': {}}
        for side in SIDES:
            points = sole_points(side, sole_prefix)
            marks = landmarks(side, points, sole_prefix)
            toe, heel = marks['toe'], marks['heel']
            direction = toe-heel
            mode = 'toe' if toe.z < heel.z else 'heel'
            entry['feet'][side] = {
                'planted': planted.get(str(frame), {}).get(side, False),
                'ankle': list(rig.matrix_world @ rig.pose.bones[foot_bone+side].head),
                'sole_z': min(v.z for v in points), 'contact_mode': mode,
                'contact_point': list(toe if mode == 'toe' else heel),
                'heading_projection_m': math.hypot(direction.x, direction.y),
                'heading': math.degrees(math.atan2(direction.x, -direction.y))}
        rows.append(entry)
    ends = {}
    for frame in (first, scene.frame_end):
        scene.frame_set(frame)
        ends[frame] = {side: rig.matrix_world @ rig.pose.bones[foot_bone+side].head for side in SIDES}
    seam = max((ends[first][side]-ends[scene.frame_end][side]).length for side in SIDES)
    return rows, seam


def measure(rows, speed, floor_z, first=25, fps=24, forward=(0, -1)):
    """Contact metrics for an in-place cycle with virtual travel `speed` (m/s)
    along `forward` (x, y). `floor_z` is the sole's rest contact height (base
    top plus sole clearance; Spearman 0.106).
    """
    def travelled(point, frame):
        distance = speed*(frame-first)/fps
        return point[0]+forward[0]*distance, point[1]+forward[1]*distance

    slip, roll, gaps, headings, readable, raw = [], [], [], [], [], []
    for side in SIDES:
        anchor = sole_anchor = mode = None
        for row in rows:
            foot = row['feet'][side]
            raw.append(abs(foot['heading']))
            if foot['heading_projection_m'] >= READABLE_FOOTPRINT_M:
                readable.append(abs(foot['heading']))
            if not foot['planted']:
                anchor = sole_anchor = mode = None
                continue
            ankle = travelled(foot['ankle'], row['frame'])
            anchor = anchor or ankle
            roll.append(math.dist(ankle, anchor))
            point = travelled(foot['contact_point'], row['frame'])
            if sole_anchor is None or mode != foot['contact_mode']:
                sole_anchor = point
            slip.append(math.dist(point, sole_anchor))
            mode = foot['contact_mode']
            gaps.append(abs(foot['sole_z']-floor_z))
            headings.append(abs(foot['heading']))
    assert gaps, 'No planted samples: the contact table is missing or the gait never lands'
    return {'virtual_forward_speed_m_s': speed, 'max_ankle_roll_travel_m': max(roll),
            'max_sole_contact_slip_m': max(slip), 'max_planted_floor_error_m': max(gaps),
            'max_planted_heading_degrees': max(headings), 'dense_frames': len(rows),
            'planted_samples': len(gaps), 'max_raw_foot_yaw_degrees': max(raw),
            'max_readable_heading_degrees': max(readable) if readable else 0.0}


def step_width(rows, rest_width=None, lateral=0):
    """Lateral distance between the ankles over the cycle (axis `lateral`: 0 = x
    when travel is along y). With `rest_width` (ankle spacing in the rest
    guard) also gives the ratio: a walk whose feet nearly touch under a unit
    that stands wide reads as knock-kneed (art director, Spearman round 10;
    target about 60% of the rest stance).
    """
    widths = [abs(row['feet']['l']['ankle'][lateral]-row['feet']['r']['ankle'][lateral]) for row in rows]
    report = {'min_m': min(widths), 'mean_m': sum(widths)/len(widths), 'max_m': max(widths)}
    if rest_width:
        report['mean_over_rest'] = report['mean_m']/rest_width
    return report


def swing_lift(rows, floor_z):
    """Highest sole clearance of each foot while it is off the ground."""
    return {side: max((row['feet'][side]['sole_z']-floor_z for row in rows
                       if not row['feet'][side]['planted']), default=0.0) for side in SIDES}


def failures(checks, limits=LIMITS):
    """Names of exceeded or missing limits; an empty list passes."""
    return [f'{name}: {checks.get(name)} exceeds {limit}' for name, limit in limits.items()
            if name not in checks or checks[name] > limit]

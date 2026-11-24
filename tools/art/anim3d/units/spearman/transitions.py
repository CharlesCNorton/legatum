"""Choose a delivered walk entry without modifying the captured performance."""
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from kit.contact import sole_points


def pixels(scene, points, size=160):
    projected = [world_to_camera_view(scene, scene.camera, p) for p in points]
    return [Vector((p.x*size, (1-p.y)*size)) for p in projected]


def foot_error(scene, reference, current):
    """Full corresponding sole vertices, not a center hiding toe/heel jumps."""
    result = {}
    for side in 'lr':
        a, b = reference[side], current[side]
        assert len(a) == len(b), 'Sole topology changed across clips'
        pa, pb = pixels(scene, a), pixels(scene, b)
        result[side] = {
            'max_vertex_px160': max((p-q).length for p, q in zip(pa, pb)),
            'center_px160': (sum(pa, Vector((0, 0)))/len(pa)
                             - sum(pb, Vector((0, 0)))/len(pb)).length,
            'max_vertex_mm': 1000*max((p-q).length for p, q in zip(a, b)),
        }
    return result


def choose_move_entry(scene, samples, guard_soles):
    """Rotate a cycle's sample order to balance guarded entry and exit.

    Every original frame survives exactly once, with identical spacing and
    wrap interval. No bone rotation, foot translation, camera, atlas anchor or
    cloth cache is changed. This reduces a hard cut; it is not a claim that a
    locomotion pose and the painted guard are identical.
    """
    rows = []
    for frame in samples:
        scene.frame_set(frame)
        row = foot_error(scene, guard_soles, {s: sole_points(s) for s in 'lr'})
        rows.append({'frame': frame, 'feet': row,
                     'score': max(f['max_vertex_px160'] for f in row.values())})
    # Entry-only selection improved 23 -> 9 px but worsened the exit. Keep
    # both boundaries in the objective, without changing any captured pose.
    scores = [max(row['score'], rows[i-1]['score']) for i, row in enumerate(rows)]
    candidates = [i for i, row in enumerate(rows)
                  if row['score'] <= rows[0]['score']
                  and rows[i-1]['score'] <= rows[-1]['score']]
    index = min(candidates, key=lambda i: scores[i])
    return samples[index:]+samples[:index], {
        'method': 'cyclic sample permutation only; donor and contact unchanged',
        'offset': index, 'before': rows[0], 'after': rows[index],
        'exit_before': rows[-1], 'exit_after': rows[index-1],
        'balanced_scores': scores, 'candidates': rows}

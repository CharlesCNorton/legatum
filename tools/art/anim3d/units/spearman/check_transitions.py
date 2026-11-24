"""Measure complete sole geometry and delivered boundaries at native 160 px.

Do not equate a cyclic source's duplicate endpoint with a seamless hard cut
between idle and locomotion. Report both, including every idle exit phase.
"""
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.contact import sole_points
from transitions import foot_error, pixels
root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
report, poses = {}, {}


def cloak_points():
    ob = bpy.data.objects['Cloak • simulated wool']
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    points = [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    return points


for clip in ('rest', 'idle', 'attack', 'move'):
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    samples = [1] if clip == 'rest' else json.loads(scene['sample_frames'])
    rows = []
    for frame in samples:
        scene.frame_set(frame)
        rows.append({s: sole_points(s) for s in 'lr'})
    poses[clip] = rows
    info = {'sample_frames': samples}
    if clip in ('idle', 'move'):
        # Dense duplicate endpoint: a real loop, separate from last->first
        # delivery travel (which should equal an ordinary frame interval).
        scene.frame_set(25)
        first = {s: sole_points(s) for s in 'lr'}
        cloak_first = pixels(scene, cloak_points())
        scene.frame_set(scene.frame_end)
        info['dense_loop'] = foot_error(scene, first, {s: sole_points(s) for s in 'lr'})
        info['cloak_loop_max_px160'] = max((a-b).length for a, b in zip(
            cloak_first, pixels(scene, cloak_points())))
        assert info['cloak_loop_max_px160'] <= .1, (clip, 'cloth loop remains open', info)
        info['delivered_steps'] = [foot_error(scene, a, b) for a, b in zip(rows, rows[1:]+rows[:1])]
        assert max(v['max_vertex_mm'] for v in info['dense_loop'].values()) <= 3
        if clip == 'move':
            period = scene.frame_end-25
            steps = [(b-a) % period for a, b in zip(samples, samples[1:]+samples[:1])]
            assert len(set(steps)) == 1, ('Uneven move loop timing', steps)
            info['cyclic_frame_intervals'] = steps
            info['selection'] = json.loads(scene.get('move_entry', '{}'))
    report[clip] = info

boundaries = {}
for label, row in [('attack entry', poses['attack'][0]), ('attack exit', poses['attack'][-1]),
                   ('move entry', poses['move'][0]), ('move exit', poses['move'][-1])]:
    errors = foot_error(scene, poses['idle'][0], row)
    boundaries[label] = {'from_idle_0': errors,
        'from_every_idle_phase': [foot_error(scene, idle, row) for idle in poses['idle']]}
    if label.startswith('attack'):
        assert max(v['max_vertex_mm'] for v in errors.values()) <= 2, (label, errors)
report['boundaries'] = boundaries
report['move_hard_cut_seamless_160'] = max(
    v['max_vertex_px160'] for v in boundaries['move entry']['from_idle_0'].values()) <= 1
report['note'] = ('Move sample order may rotate; source pose/foot rotations/contact remain untouched. '
                  'A residual over 1 px is explicitly unresolved, even if loop/contact gates pass.')
(master/'transitions.json').write_text(json.dumps(report, indent=2)+'\n')
print('TRANSITIONS_OK', json.dumps({k:v['from_idle_0'] for k,v in boundaries.items()}))
print('MOVE_HARD_CUT_SEAMLESS_160', report['move_hard_cut_seamless_160'])

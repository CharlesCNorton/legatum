"""R15c: matched CPU phase A/B and dense geometry invariants, isolated files only."""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.ab import invariant
from kit.contact import sole_points
from transitions import foot_error, pixels
import look

def candidate_move_entry(scene, samples, guard_soles):
    """Sample an equal-cadence cycle at the best existing dense integer phase.

    R14 considered only rotations of eight delivered samples. The contact-
    solved action and baked cloth have 32 integer phases: choose among those,
    never interpolate new poses, alter foot rotations or change cycle speed.
    Minimize the WORST of entry and exit. This can trade a smaller entry for
    a slightly larger exit; retain both values instead of claiming two wins.
    """
    start, end = 25, scene.frame_end
    period = end-start
    count = len(samples)
    assert period % count == 0, 'Walk requires integer dense sample spacing'
    step = period//count
    assert all((b-a) % period == step
               for a, b in zip(samples, samples[1:]+samples[:1]))
    rows = []
    for frame in range(start, end):
        scene.frame_set(frame)
        feet = foot_error(scene, guard_soles, {s: sole_points(s) for s in 'lr'})
        rows.append({'frame': frame, 'feet': feet,
                     'score': max(f['max_vertex_px160'] for f in feet.values())})
    scores = [max(row['score'], rows[(i-step) % period]['score'])
              for i, row in enumerate(rows)]
    # Deterministic tie break: total boundary error, then earliest source phase.
    index = min(range(period), key=lambda i: (
        scores[i], rows[i]['score']+rows[(i-step) % period]['score'], i))
    previous = min((f-start for f in samples), key=lambda i: scores[i])
    selected = [start+(index+i*step) % period for i in range(count)]
    return selected, {
        'method': 'uniform dense integer phase; donor action and contact unchanged',
        'phase_start': selected[0], 'frame_interval': step, 'frame_count': count,
        'before': rows[samples[0]-start], 'after': rows[index],
        'exit_before': rows[samples[-1]-start], 'exit_after': rows[(index-step) % period],
        'r14_grid_best': {'entry': rows[previous], 'exit': rows[(previous-step) % period],
                         'worst_px160': scores[previous]},
        'worst_px160': scores[index], 'balanced_scores': scores, 'candidates': rows}


root = Path(os.environ['ANIM_ROOT'])
assert root.name == 'spearman-r15c', 'Use the isolated R15c root'
master = root/'masters/spearman-3d-v2'
before = root.parent/'spearman-r14-merge/masters/spearman-3d-v2'
out = root/'preview'
out.mkdir(exist_ok=True)
report = {}


def dense_snapshot(scene):
    rig = next(o for o in scene.objects if o.type == 'ARMATURE' and len(o.pose.bones) == 53)
    cloak = bpy.data.objects['Cloak • simulated wool']
    rows = []
    for frame in range(25, scene.frame_end+1):
        scene.frame_set(frame)
        ev = cloak.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        cloth = pixels(scene, [ev.matrix_world @ v.co for v in mesh.vertices])
        ev.to_mesh_clear()
        rows.append({'frame': frame,
                     'bones': {p.name: [list(r) for r in p.matrix] for p in rig.pose.bones},
                     'soles': {s: [list(p) for p in sole_points(s)] for s in 'lr'},
                     'cloth': [list(p) for p in cloth]})
    return rows


bpy.ops.wm.open_mainfile(filepath=str(master/'spearman.blend'))
bpy.context.scene.frame_set(1)
guard = {s: sole_points(s) for s in 'lr'}
bpy.ops.wm.open_mainfile(filepath=str(before/'clips/move/move.blend'))
scene = bpy.context.scene
old_samples = json.loads(scene['sample_frames'])
actions = invariant(scene)['actions']
dense_before = dense_snapshot(scene)
samples, selection = candidate_move_entry(scene, old_samples, guard)
scene['sample_frames'] = json.dumps(samples)
scene['move_entry'] = json.dumps(selection)
source = json.loads(scene['motion_source'])
source['move_entry'] = selection
scene['motion_source'] = json.dumps(source)
scene.frame_set(samples[0])
bpy.ops.wm.save_as_mainfile(filepath=str(master/'clips/move/move.blend'))
metadata = json.loads((master/'clips/move/clip.json').read_text())
metadata['frames'], metadata['motion_source'] = samples, source
(master/'clips/move/clip.json').write_text(json.dumps(metadata, indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(master/'clips/move/move.blend'))
scene = bpy.context.scene
dense_after = dense_snapshot(scene)
assert dense_before == dense_after, 'Dense bones, sole vertices or combined cloth changed'
assert invariant(scene)['actions'] == actions, 'Source action changed'
report['invariants'] = {'all_53_bones_all_33_samples_identical': True,
                        'sole_vertices_all_33_samples_identical': True,
                        'evaluated_cloth_all_33_samples_identical': True,
                        'actions_identical': True,
                        'before_samples': old_samples, 'after_samples': samples}
report['selection'] = selection
report['verdict'] = 'REJECTED: smaller worst boundary, but larger exit and delivered cloth steps; production retains R14'
report['production_changed'] = False
# Full evaluated cloth displacement: geometric vertices, not a visible-edge metric.
by_frame = {row['frame']: row['cloth'] for row in dense_after}
for name, frames in [('before', old_samples), ('after', samples)]:
    steps = []
    for a, b in zip(frames, frames[1:]+frames[:1]):
        distances = sorted(((p[0]-q[0])**2+(p[1]-q[1])**2)**.5
                           for p,q in zip(by_frame[a],by_frame[b]))
        steps.append({'from': a, 'to': b, 'max_px160': max(distances),
                      'p95_px160': distances[int(.95*(len(distances)-1))]})
    report[name+'_cloth_steps'] = steps
(root/'metrics.json').write_text(json.dumps(report, indent=2)+'\n')
print('R15C_INVARIANTS', json.dumps(report['invariants']), flush=True)

# Rest, idle, attack, hit and shield-readable death are byte-preserved inputs.
for clip in ('rest', 'idle', 'attack', 'hit', 'death'):
    rel = Path('spearman.blend') if clip == 'rest' else Path(f'clips/{clip}/{clip}.blend')
    assert (before/rel).read_bytes() == (master/rel).read_bytes(), clip
for p in (before/'look').iterdir():
    if p.is_file():
        assert p.read_bytes() == (master/'look'/p.name).read_bytes(), p.name
report['unchanged_blends'] = ['rest', 'idle', 'attack', 'hit', 'death']
for version, source_root, clips in [('before', before, ('rest','idle','move','death')),
                                   ('after', master, ('move',))]:
    for clip in clips:
        path = source_root/'spearman.blend' if clip == 'rest' else source_root/f'clips/{clip}/{clip}.blend'
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        look.configure_render(scene, 'proxy', 256, 8)
        look.apply_materials(scene, 'beauty', source_root/'look', dict(look.LOOK))
        frames = [1] if clip == 'rest' else json.loads(scene['sample_frames'])
        folder = out/version/clip
        folder.mkdir(parents=True, exist_ok=True)
        done = {}
        for i, frame in enumerate(frames):
            target = folder/f'{i:02}.png'
            if frame in done:
                target.write_bytes(done[frame].read_bytes())
            else:
                look.render_frame(scene, target, frame)
            done[frame] = target
        report[version+'/'+clip] = {'blend_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'frames': frames, 'render': 'shared look path, Cycles CPU proxy, 256px, 8 samples, seed17'}
        (root/'metrics.json').write_text(json.dumps(report, indent=2)+'\n')
print('R15C_REVIEW_COMPLETE', out, flush=True)

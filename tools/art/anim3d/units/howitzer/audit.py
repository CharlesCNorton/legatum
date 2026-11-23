"""Independently reopen saved clips and verify evaluated geometry, not build claims."""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT / 'masters/howitzer'
COUNTS = {'idle': 8, 'move': 8, 'attack': 10, 'hit': 4, 'death': 10}
report = {'clips': {}, 'bakes': {}}
reference_base = None
for clip, count in COUNTS.items():
    path = MASTER / f'howitzer-{clip}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    base = bpy.data.objects['GEO-stationary cream disc']
    assert base.animation_data is None
    assert scene.camera.type == 'CAMERA'
    frames = []
    terminal = []
    for index in range(count):
        scene.frame_set(index + 1)
        deps = bpy.context.evaluated_depsgraph_get()
        base_matrix = [list(row) for row in base.matrix_world]
        if reference_base is None:
            reference_base = base_matrix
        assert base_matrix == reference_base, (clip, index, 'base moved')
        contacts = []
        for sign in [-1, 1]:
            obj = bpy.data.objects[f'GEO-Rolled steel wheel rim {sign}']
            evaluated = obj.evaluated_get(deps)
            bottom = min((evaluated.matrix_world @ v.co).z for v in evaluated.data.vertices)
            assert abs(bottom - .13) < .002, (clip, index, 'wheel contact', bottom)
            contacts.append(bottom)
            wheel=bpy.data.objects[f'RIG-wheel {sign}']
            inverse=wheel.matrix_world.inverted()
            rim_radius=max(math.hypot(q.x,q.z) for v in evaluated.data.vertices
                           for q in [inverse@(evaluated.matrix_world@v.co)])
            for part in wheel.children:
                if not any(k in part.name for k in ['Dished wheel spoke','Spoke socket']):
                    continue
                radius=max(math.hypot(q.x,q.z) for v in part.data.vertices
                           for q in [inverse@(part.matrix_world@v.co)])
                assert radius <= rim_radius+.001, (clip,index,part.name,'spoke outside rim',radius,rim_radius)
        assert all(min(abs(value) for value in obj.scale) > .001
                   for obj in scene.objects if obj.type == 'MESH')
        frames.append({'frame': index + 1, 'wheel_bottom_z': contacts})
        if clip == 'death' and index >= count - 2:
            terminal.append({obj.name: tuple(value for row in obj.matrix_world for value in row)
                             for obj in scene.objects if obj.type == 'MESH'})
    if clip == 'death':
        delta = max(abs(x - y) for name in terminal[0]
                    for x, y in zip(terminal[0][name], terminal[1][name]))
        assert delta < 1e-5, ('death terminal geometry not held', delta)
    # Cyclic motion includes a non-exported closure key. Wheels rotate a whole turn.
    if clip in ['idle', 'move']:
        scene.frame_set(1)
        first = {obj.name: obj.matrix_world.copy() for obj in scene.objects if obj.type == 'MESH'}
        scene.frame_set(count + 1)
        delta = max(abs(x - y) for obj in scene.objects if obj.type == 'MESH'
                    for a, b in zip(first[obj.name], obj.matrix_world) for x, y in zip(a, b))
        assert delta < 1e-5, (clip, 'loop geometry does not close', delta)
    report['clips'][clip] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'frames': frames}
for path in sorted((MASTER / 'textures').glob('*.png')):
    report['bakes'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
assert len(report['bakes']) == 6, 'expected three AO and three curvature maps'
report['status'] = 'PASS: reopened geometry, 40 contacts, spoke envelopes, fixed base, nondegenerate scales, cyclic closure, held death and six baked maps'
(MASTER / 'geometry-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(report['status'])

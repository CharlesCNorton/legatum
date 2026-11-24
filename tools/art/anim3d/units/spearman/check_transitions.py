"""Measure guard/attack foot continuity and the registered walk at 256 px."""
import json
import os
from pathlib import Path
import sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.contact import sole_points
root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
report = {}
for clip in ('rest', 'idle', 'attack', 'move'):
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    samples = [1] if clip == 'rest' else json.loads(scene['sample_frames'])
    rows = []
    for frame in samples:
        scene.frame_set(frame)
        row = {}
        for side in 'lr':
            points = sole_points(side)
            centre = sum(points, Vector())/len(points)
            pixel = world_to_camera_view(scene, scene.camera, centre)
            row[side] = {'sole': list(centre), 'pixel': [pixel.x*256, (1-pixel.y)*256]}
        rows.append(row)
    report[clip] = rows
errors = {}
for label, row in [('attack entry', report['attack'][0]), ('attack exit', report['attack'][-1])]:
    errors[label] = {side: (Vector(row[side]['sole'])-Vector(report['idle'][0][side]['sole'])).length*1000 for side in 'lr'}
    assert max(errors[label].values()) <= 2, (label, errors[label])
report['attack_sole_error_mm'] = errors
report['walk_registration_note'] = 'Constant world track translation; gait phases naturally differ from a standing guard. No per-frame image offsets.'
(master/'transitions.json').write_text(json.dumps(report,indent=2)+'\n')
print('TRANSITIONS_OK', json.dumps(errors))

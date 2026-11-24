"""Audit the selected render layer and frozen performances without a GPU render.

Run after the CPU ID pass and look_textures.py; palette light fitting stays on
GPU. The audit opens files read-only and does not save material replacements.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.ab import invariant
import look

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
reference = Path(os.environ.get('SPEARMAN_FROZEN_REFERENCE', str(Path.home()/'LegatumRuns/anim-pilot/masters/spearman-3d-v2')))
report = {'frozen_clips': {}, 'painted_layer': {}}
for clip in ('idle', 'attack'):
    values = []
    for folder in (reference, master):
        path = folder/'clips'/clip/(clip+'.blend')
        bpy.ops.wm.open_mainfile(filepath=str(path))
        values.append(invariant(bpy.context.scene)['actions'])
    report['frozen_clips'][clip] = {'before': values[0], 'after': values[1], 'identical': values[0] == values[1]}
    assert values[0] == values[1], (clip, 'frozen actions changed')
for clip in ('rest', 'idle', 'move', 'attack', 'hit', 'death'):
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    # Lighting is intentionally replaced; geometry, transforms, camera and all
    # actions must remain identical. Exclude old/new lights from comparison.
    def signature():
        return {o.name: (o.type, [list(r) for r in o.matrix_world],
                        hashlib.sha256(bytes(str([(tuple(v.co), [(g.group, g.weight) for g in v.groups]) for v in o.data.vertices]), 'utf8')).hexdigest() if o.type == 'MESH' else None,
                        o.data.bevel_depth if o.type == 'CURVE' else None,
                        o.data.ortho_scale if o.type == 'CAMERA' else None)
                for o in scene.objects if o.type != 'LIGHT'}
    before, actions = signature(), invariant(scene)['actions']
    look.apply_scene(scene, 'beauty')
    look.apply_materials(scene, 'beauty', master/'look', dict(look.LOOK))
    assert before == signature(), (clip, 'render-time geometry/camera changed')
    assert actions == invariant(scene)['actions'], (clip, 'render-time actions changed')
    mats = [m for m in bpy.data.materials if m.name.startswith('LOOK ')]
    assert mats and all(m.use_nodes for m in mats)
    assert all(any(n.type == 'OUTPUT_MATERIAL' for n in m.node_tree.nodes) for m in mats)
    report['painted_layer'][clip] = {'materials': len(mats), 'geometry_camera_actions_unchanged': True}
(master/'merge-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('MERGE_CHECKS', json.dumps(report), flush=True)

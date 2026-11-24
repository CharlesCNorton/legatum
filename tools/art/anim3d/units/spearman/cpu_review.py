"""Combined candidate CPU proxy: rest, all 40 frames, input/action receipts.

ANIM_ROOT must be an isolated lane root. Never writes the shipped atlas.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.ab import invariant, preview_settings, render_still
from kit.cpu_look import graph_for_sun
from continuity_preview import rest_contact
import look
from look_receipt import CODE, digest

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
out = root/'preview'
receipt = {}
clips = sys.argv[sys.argv.index('--')+1].split(',') if '--' in sys.argv else ('baseline', 'contact-before', 'rest', 'idle', 'move', 'attack', 'hit', 'death')
if (out/'receipt.json').exists(): receipt = json.loads((out/'receipt.json').read_text())
for clip in clips:
    path = master/'spearman.blend' if clip in ('rest', 'contact-before') else master/'clips'/clip/(clip+'.blend')
    look_dir = master/'look'
    if clip == 'baseline':
        reference = Path.home()/'LegatumRuns/anim-pilot/masters/spearman-3d-v2'
        path, look_dir = reference/'spearman.blend', reference/'look'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    contact = rest_contact(scene) if clip == 'rest' else None
    look.Graph = graph_for_sun(look.directions(scene)[1])
    look.apply_scene(scene, 'beauty')
    settings = preview_settings(scene, samples=8)
    look.apply_materials(scene, 'beauty', look_dir, dict(look.LOOK))
    scene.render.dither_intensity = 0
    samples = [1] if clip in ('rest', 'baseline', 'contact-before') else json.loads(scene['sample_frames'])
    directory = out/clip; directory.mkdir(parents=True, exist_ok=True)
    done = {}
    for i, frame in enumerate(samples):
        target = directory/f'{i:02}.png'
        if frame in done:
            target.write_bytes(done[frame].read_bytes())
        else:
            render_still(scene, target, frame)
            done[frame] = target
    receipt[clip] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'actions': invariant(scene)['actions'], 'look_code': {str(p): digest(p) for p in CODE}, 'settings': settings, 'frames': samples,
        'proxy_limit': 'analytic sun, no cast shadow, Cycles AO, ungraded'}
    if contact is not None: receipt[clip]['rest_contact'] = contact
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('CPU_REVIEW_COMPLETE', out)

"""Render rest and all clips through the shared look path, in an isolated root.

Cycles CPU proxy only: analytical light, no Eevee cast shadow. No saved scene
or shipped atlas is modified. Optional comma-separated clips follow --.
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
from look_receipt import CODE, digest

root = Path(os.environ['ANIM_ROOT'])
assert root.resolve() != (Path.home()/'LegatumRuns/anim-pilot').resolve(), 'CPU evidence needs an isolated root'
master = root/'masters/spearman-3d-v2'
out = root/'preview'
receipt = json.loads((out/'receipt.json').read_text()) if (out/'receipt.json').exists() else {}
clips = sys.argv[sys.argv.index('--')+1].split(',') if '--' in sys.argv else ('rest', 'idle', 'move', 'attack', 'hit', 'death')
for clip in clips:
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    look.configure_render(scene, 'proxy', 256, 8)
    look.apply_materials(scene, 'beauty', master/'look', dict(look.LOOK))
    samples = [1] if clip == 'rest' else json.loads(scene['sample_frames'])
    directory = out/clip
    directory.mkdir(parents=True, exist_ok=True)
    done = {}
    for i, frame in enumerate(samples):
        target = directory/f'{i:02}.png'
        if frame in done:
            target.write_bytes(done[frame].read_bytes())
        else:
            look.render_frame(scene, target, frame)
            done[frame] = target
    receipt[clip] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'actions': invariant(scene)['actions'], 'look_code': {str(p): digest(p) for p in CODE},
        'settings': {'engine': 'CYCLES CPU', 'size': 256, 'samples': 8, 'seed': 17},
        'frames': samples, 'proxy_limit': 'analytic sun; no Eevee cast shadow; ungraded',
        'calibration': {p.name: digest(p) for p in sorted((master/'look').iterdir()) if p.suffix in ('.png', '.json')}}
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('CPU_REVIEW_COMPLETE', out)

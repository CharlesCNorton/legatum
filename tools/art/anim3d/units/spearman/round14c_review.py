"""Matched Cycles CPU evidence for lane-c seams; never save render changes."""
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
before = Path.home()/'LegatumRuns/anim-pilot/masters/spearman-3d-v2'
out = root/'preview'
receipt = {}
for version, source in [('before', before), ('after', master)]:
    for clip in ('rest', 'idle', 'move', 'attack', 'hit', 'death'):
        path = source/'spearman.blend' if clip == 'rest' else source/f'clips/{clip}/{clip}.blend'
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        look.configure_render(scene, 'proxy', 256, 8)
        look.apply_materials(scene, 'beauty', source/'look', dict(look.LOOK))
        frames = [1] if clip == 'rest' else json.loads(scene['sample_frames'])
        # Same samples of frozen clips render once: compare source fingerprints,
        # then reuse identical source frames, not an unverified look-alike.
        key = version+'/'+clip
        fingerprint = {'blend': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'actions': invariant(scene)['actions'], 'frames': frames,
                       'look': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((source/'look').iterdir())
                                if p.suffix in ('.png', '.json')}}
        folder = out/version/clip
        folder.mkdir(parents=True, exist_ok=True)
        reuse = version == 'after' and fingerprint == receipt.get('before/'+clip)
        done = {}
        for i, frame in enumerate(frames):
            target = folder/f'{i:02}.png'
            if reuse:
                target.write_bytes((out/'before'/clip/target.name).read_bytes())
            elif frame in done:
                target.write_bytes(done[frame].read_bytes())
            else:
                look.render_frame(scene, target, frame)
            done[frame] = target
        receipt[key] = fingerprint
        (out/'r14c-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('R14C_CPU_REVIEW_READY', out)

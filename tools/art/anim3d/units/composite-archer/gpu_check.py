"""Reject stale/CPU masters; issue a receipt only after a complete host pass."""
import hashlib
import json
import os
import sys
from pathlib import Path
from PIL import Image

root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/composite-archer'
review = root / 'review/3d-v2'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for stage in ['c', 'e-idle', 'e-move', 'e-attack', 'e-hit', 'e-death']:
    report = json.loads((master / 'renders' / stage / 'manifest.json').read_text())
    assert (report['engine'], report['device'], report['resolution'], report['samples']) == ('CYCLES', 'GPU', 512, 64), f'{stage}: not GPU512/64'
    assert report['blend_sha256'] == sha(master / report['blend']), f'{stage}: stale blend'
    assert report['grade_sha256'] == sha(master / 'grade.json'), f'{stage}: stale grade'
    for i, frame in enumerate(report['frames']):
        assert frame['sha256'] == sha(master / frame['path'])
        for size in [512, 256]:
            assert Image.open(master / str(size) / stage / f'{i:02d}.png').size == (size, size)
plain = json.loads((master / 'plain-views.json').read_text())
assert plain['blend_sha256'] == sha(master / 'registered.blend')
assert (plain['device'], plain['resolution'], plain['samples']) == ('GPU', 512, 64)
for record in plain['files']:
    assert sha(master / record['path']) == record['sha256']
feet = json.loads((master / 'feet.json').read_text())
assert feet['blend_sha256'] == sha(master / 'clips/move.blend')
assert (feet['device'], feet['resolution'], feet['samples']) == ('GPU', 512, 64)
assert len(feet['files']) == 16
for record in feet['files']:
    assert sha(master / record['path']) == record['sha256']
print('PASS GPU provenance: plain, rest and all 40 clip frames at GPU512/64')
if '--receipt' in sys.argv:
    from deliver import validate
    validate()
    video = json.loads((review / f"composite-archer-round{os.environ['ROUND']}-video.json").read_text())
    assert video['codec_name'] == 'h264' and int(video['nb_frames']) == 240
    (review / f"composite-archer-gpu-round{os.environ['ROUND']}.json").write_text(json.dumps({'master_sha256': sha(master / 'composite-archer.blend'), 'pack': json.loads((master / 'pack.json').read_text()), 'audit': json.loads((master / 'audit.json').read_text()), 'video': video, 'video_sha256': sha(review / f"composite-archer-round{os.environ['ROUND']}.mp4"), 'art_approved': False}, indent=2))

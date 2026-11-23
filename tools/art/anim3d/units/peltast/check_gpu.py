"""Reject CPU/stale masters before certifying the lead's complete GPU pass."""
import hashlib
import json
import os
from pathlib import Path
import sys

from PIL import Image

root = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
master = root / 'masters/peltast'
review = root / 'review/3d-v2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = {}
for stage in ['b', 'c', 'd', 'e-idle', 'e-move', 'e-attack', 'e-hit', 'e-death']:
    manifest = json.loads((master / 'raw' / stage / 'delivery.json').read_text())
    assert (manifest['engine'], manifest['device'], manifest['resolution'],
            manifest['samples']) == ('CYCLES', 'GPU', 512, 64), f'{stage}: requires GPU512/64'
    clip = stage[2:] if stage.startswith('e-') else 'attack' if stage == 'd' else None
    blend = master / 'clips' / f'{clip}.blend' if clip else master / (
        'peltast-unpainted.blend' if stage == 'b' else 'peltast.blend')
    assert manifest['blend_sha256'] == sha(blend), f'{stage}: stale blend'
    if stage != 'b':
        assert manifest['grade_sha256'] == sha(master / 'grade.json'), f'{stage}: stale grade'
    for name in manifest['frames']:
        for size in [512, 256]:
            with Image.open(master / str(size) / stage / f'{name}.png') as image:
                assert image.size == (size, size), f'{stage}/{name}: wrong master size'
    records[stage] = manifest

if '--receipt' in sys.argv:
    validation = json.loads((review / 'peltast-validation.json').read_text())
    assert validation['checks'] == 'passed' and not validation['preview']
    audit = json.loads((review / 'peltast-audit.json').read_text())
    assert audit['passed']
    video = review / f'peltast-round{os.environ.get("ROUND", "2")}.mp4'
    assert video.is_file()
    receipt = dict(master_sha256=sha(master / 'peltast.blend'), stages=records,
                   validation=validation, audit=audit, video_sha256=sha(video),
                   art_approved=False)
    (review / f'peltast-gpu-round{os.environ.get("ROUND", "2")}.json').write_text(
        json.dumps(receipt, indent=2) + '\n')
print('GPU master provenance passed')

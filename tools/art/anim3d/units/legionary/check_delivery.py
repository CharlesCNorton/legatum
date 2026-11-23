"""Reject stale, mixed-device or incomplete final masters before GPU delivery."""
import hashlib
import json
import os
import sys
from pathlib import Path
from PIL import Image

root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/legionary'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = sha(master / 'legionary.blend')
grade = sha(master / 'grade.json')
counts = {'b': 3, 'c': 1, 'd': 4, 'e-idle': 8, 'e-move': 8,
          'e-attack': 10, 'e-hit': 4, 'e-death': 10}
baseline = None
for stage, count in counts.items():
    folder = master / 'renders' / stage
    meta = json.loads((folder / 'render.json').read_text())
    assert meta['resolution'] == 512, (stage, 'not native 512')
    settings = tuple(meta[k] for k in ('engine', 'device', 'samples', 'resolution'))
    if '--gpu' in sys.argv:
        assert settings[:2] == ('CYCLES', 'GPU'), (stage, 'not GPU')
    if baseline is None:
        baseline = settings
    assert settings == baseline, (stage, 'mixed render settings')
    clip = stage[2:] if stage.startswith('e-') else 'attack' if stage == 'd' else None
    blend = master / 'clips' / f'{clip}.blend' if clip else master / ('legionary-plain.blend' if stage == 'b' else 'legionary.blend')
    assert meta['blend_sha256'] == sha(blend), (stage, 'stale blend')
    if clip:
        assert meta['source_master_sha256'] == source, (stage, 'stale source')
    if stage != 'b':
        assert meta['grade_sha256'] == grade, (stage, 'stale grade')
    assert len(meta['raw_sha256']) == count, stage
    for name, digest in meta['raw_sha256'].items():
        assert sha(folder / 'raw' / name) == digest, (stage, name)
        for size in (512, 256):
            assert Image.open(folder / str(size) / name).size == (size, size)
print('DELIVERY_MASTERS_PASS', baseline, sum(counts.values()), 'images at each size')

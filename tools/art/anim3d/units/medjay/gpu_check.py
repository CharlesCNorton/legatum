"""Reject incomplete, stale or CPU-labelled GPU handoffs; no art approval."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters/medjay'
STAGES = ['b', 'c', 'c-details', 'd', 'e-idle', 'e-move', 'e-attack', 'e-hit', 'e-death']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_inputs():
    for name in ['plain', 'idle', 'move', 'attack', 'hit', 'death']:
        assert (MASTER / f'medjay-{name}.blend').is_file(), f'Missing master: {name}'
    assert (MASTER / 'medjay.blend').is_file(), 'Missing finished master'


def check_renders():
    from PIL import Image
    for stage in STAGES:
        folder = MASTER / 'renders' / stage
        data = json.loads((folder / 'render.json').read_text())
        assert (data['engine'], data['device'], data['resolution']) == ('CYCLES', 'GPU', 512), f'{stage}: GPU512 required'
        assert data['samples'] >= 64, f'{stage}: at least 64 samples required'
        assert sha(Path(data['blend'])) == data['blend_sha256'], f'{stage}: stale blend'
        review = json.loads((folder / 'review.json').read_text())
        assert review['raw_manifest_sha256'] == sha(folder / 'render.json')
        if stage != 'b':
            assert review['grade_sha256'] == sha(MASTER / 'grade.json')
        for i in range(len(data['frames'])):
            name = f'{i:02d}.png'
            assert sha(folder / name) == data['sha256'][name]
            assert sha(folder / 'graded' / name) == review['graded_sha256'][name]
            for size in [512, 256]:
                retained = Image.open(MASTER / str(size) / stage / name).convert('RGBA')
                expected = Image.open(folder / 'graded' / name).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
                assert retained.size == (size, size) and retained.tobytes() == expected.tobytes(), f'{stage}: stale {size} master'
    print('Verified every stage: current Cycles GPU64+/512 renders and matching 256 masters.')


if __name__ == '__main__':
    import sys
    check_inputs()
    if '--inputs-only' not in sys.argv:
        check_renders()

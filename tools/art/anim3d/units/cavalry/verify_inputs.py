"""Check immutable inputs before prepare regenerates any derived color maps."""
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
unit = Path(__file__).parent
lock = json.loads((unit/'assets.lock.json').read_text())
expected = {'Horse.glb': lock['sha256']}
expected.update({name: digest for name, digest in lock['paint_assets_sha256'].items()
                 if name.startswith('fill-') or name in ('painting-source.png', 'stone-fill-source.png')})
for name, digest in expected.items():
    path = root/'assets/cavalry'/name
    assert path.is_file(), f'Missing source input: {path}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'Changed source input: {path}'
checkpoint = root/'masters/cavalry/cavalry-unpainted.blend'
assert checkpoint.is_file(), f'Missing clean checkpoint: {checkpoint}'
print(f'INPUTS {len(expected)} immutable painting/fill/horse sources verified')

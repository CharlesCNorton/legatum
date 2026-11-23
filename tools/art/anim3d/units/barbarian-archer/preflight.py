"""Refuse modified or missing source textures before any expensive render work."""
import hashlib
import json
import os
from pathlib import Path

unit = Path(__file__).resolve().parent
root = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
for name, expected in json.loads((unit/'inputs.json').read_text()).items():
    path = root/'assets/barbarian-archer'/name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f'Source hash mismatch: {name}')
print('PASS: all pinned painting, generated fill and derived texture inputs')

"""Bind a baked build to its sources before the overnight renderer consumes it."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters/landship'
UNIT = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    paths = [UNIT / name for name in ('scene.py', 'prepare.py', 'bake.py', 'animate.py', 'assets.lock.json')]
    paths += [MASTER / name for name in ('plain.blend', 'landship.blend')]
    paths += sorted((MASTER / 'clips').glob('*.blend'))
    paths += sorted((MASTER / 'textures/baked').glob('*.png'))
    assert len(list((MASTER / 'clips').glob('*.blend'))) == 5
    for item in json.loads((UNIT / 'assets.lock.json').read_text())['files']:
        path = ROOT / item['path']
        assert digest(path) == item['sha256'], f'Changed input: {path}'
        paths.append(path)
    return {str(p): digest(p) for p in paths}


def check():
    assert json.loads((MASTER / 'build-inputs.json').read_text()) == snapshot(), 'Stale build: build, bake, animate, seal again'
    print('BUILD INPUTS PASS')


if __name__ == '__main__':
    if sys.argv[1] == 'seal':
        (MASTER / 'build-inputs.json').write_text(json.dumps(snapshot(), indent=2) + '\n')
    else:
        check()

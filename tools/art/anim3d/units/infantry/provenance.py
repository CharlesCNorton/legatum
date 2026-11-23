"""Bind a saved master to the exact geometry, material and motion inputs."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
MASTER = ROOT/'masters/infantry'
BUILD_FILES = ('scene.py', 'refine.py', 'prepare.py', 'retarget.py', 'provenance.py', 'assets.lock.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    assets = json.loads((HERE/'assets.lock.json').read_text())
    for path, expected in assets.items():
        assert digest(ROOT/path) == expected, 'Changed source asset: '+path
    return {'scripts': {name: digest(HERE/name) for name in BUILD_FILES},
            'assets': assets,
            'reference': digest(Path('app/src/assets/units/infantry-256.png'))}


def seal():
    data = inputs()
    data['master_sha256'] = digest(MASTER/'infantry.blend')
    (MASTER/'build-inputs.json').write_text(json.dumps(data, indent=2)+'\n')


def check():
    expected = json.loads((MASTER/'build-inputs.json').read_text())
    current = inputs()
    current['master_sha256'] = digest(MASTER/'infantry.blend')
    assert current == expected, 'Build inputs changed; rebuild before using this master'
    return expected


if __name__ == '__main__':
    check()
    print('Current build inputs verified')

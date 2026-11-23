"""Bind external baked masters to their build inputs before a host GPU pass."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
UNIT = Path(__file__).resolve().parent
MASTER = ROOT / 'masters/drone-swarm'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    files = {str(p.relative_to(UNIT)): sha(p) for p in
             (UNIT / name for name in ('scene.py', 'prepare.py', 'bake.py', 'assets.lock.json'))}
    for name in ('painting-source.png', 'painted-fill.png', 'projection.png'):
        files['assets/' + name] = sha(ROOT / 'assets/drone-swarm' / name)
    files['token'] = sha(Path('app/src/assets/units/drone-swarm-256.png'))
    for name in ('plain.blend', 'drone-swarm.blend'):
        files['masters/' + name] = sha(MASTER / name)
    lock = json.loads((UNIT / 'assets.lock.json').read_text())
    for asset in lock.values():
        assert sha(ROOT / asset['file']) == asset['sha256'], 'Changed licensed input: ' + asset['file']
    return files


def check():
    saved = json.loads((MASTER / 'build-inputs.json').read_text())
    current = inputs()
    assert saved == current, 'Baked master/build inputs changed; rebuild and rebake before GPU pass'
    print('Baked masters and licensed build inputs verified')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'seal':
        (MASTER / 'build-inputs.json').write_text(json.dumps(inputs(), indent=2) + '\n')
    else:
        check()

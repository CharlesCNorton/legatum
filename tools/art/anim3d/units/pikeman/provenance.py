"""Seal/check the finished master against the exact unit scripts and textures."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    root = Path(os.environ['ANIM_ROOT'])
    unit = Path(__file__).resolve().parent
    files = {'scripts/' + p.name: p for p in unit.iterdir() if p.suffix in ['.py', '.sh']}
    files.update({'assets/' + p.name: p for p in (root / 'assets/pikeman').glob('*.png')})
    files.update({'masters/' + name: root / 'masters/pikeman' / name
                  for name in ['pikeman.blend', 'plain.blend', 'bakes.json']})
    return {key: digest(path) for key, path in sorted(files.items())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    path = Path(os.environ['ANIM_ROOT']) / 'masters/pikeman/build-inputs.json'
    current = inventory()
    if args.seal:
        path.write_text(json.dumps(current, indent=2) + '\n')
        print('BUILD_SEALED', len(current), 'inputs')
    else:
        recorded = json.loads(path.read_text())
        changed = [p for p in set(current) | set(recorded) if current.get(p) != recorded.get(p)]
        assert not changed, 'Rebuild/review required; changed inputs: ' + ', '.join(changed)
        print('BUILD_INPUTS_OK', len(current))

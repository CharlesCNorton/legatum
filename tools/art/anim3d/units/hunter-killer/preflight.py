"""Bind the editable scene set to its recipe and external texture inputs."""
import hashlib
import json
import sys
from pathlib import Path
from common import MASTER, ASSETS, CLIPS

UNIT = Path(__file__).resolve().parent
RECIPES = ('common.py', 'prepare.py', 'scene.py', 'finish.py', 'animate.py', 'assets.lock.json')
SCENES = ['model.blend', 'plain.blend', 'finished.blend'] + [f'clips/{c}.blend' for c in CLIPS]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    pinned = json.loads((UNIT / 'assets.lock.json').read_text())
    for name, expected in pinned.items():
        assert digest(name) == expected, f'Changed source asset: {name}'
    return {str(UNIT / name): digest(UNIT / name) for name in RECIPES} | pinned


def main(task):
    pending = MASTER / 'build-pending'
    receipt = MASTER / 'build-inputs.json'
    if task == 'begin':
        pending.write_text(json.dumps(inputs(), indent=2))
        return
    if task == 'seal':
        current = inputs()
        assert json.loads(pending.read_text()) == current, 'Recipe changed during build; rebuild'
        files = {str(MASTER / name): digest(MASTER / name) for name in SCENES}
        files.update({str(ASSETS / name): digest(ASSETS / name)
                      for name in ('projection.png', 'stone-projection.png')})
        receipt.write_text(json.dumps({'inputs': current, 'outputs': files}, indent=2))
        pending.unlink()
        return
    assert task == 'verify'
    assert not pending.exists(), 'Incomplete build; rebuild and finish before rendering'
    report = json.loads(receipt.read_text())
    assert inputs() == report['inputs'], 'Scene recipes changed; rebuild before GPU pass'
    for name, expected in report['outputs'].items():
        assert digest(name) == expected, f'Changed scene or derived texture: {name}'
    print('Sealed recipe, inputs, derived textures and eight scene files verified.')


if __name__ == '__main__':
    main(sys.argv[1])

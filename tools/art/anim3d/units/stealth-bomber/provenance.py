"""Bind an editable master to the scripts and texture inputs that built it."""
import hashlib
import json
import os
from pathlib import Path
import sys

UNIT = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
MASTER = ROOT/'masters/stealth-bomber'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    paths = [UNIT/name for name in ('scene.py', 'project.py', 'prepare.py', 'bake.py')]
    paths += sorted((ROOT/'assets/stealth-bomber').glob('*.png'))
    return {('unit/'+p.name if p.parent == UNIT else 'assets/'+p.name): sha(p) for p in paths}


def render_signature():
    return hashlib.sha256(''.join(sha(UNIT/name) for name in ('render.py', 'contact.py')).encode()).hexdigest()


def check():
    proof = json.loads((MASTER/'build-source.json').read_text())
    assert proof['inputs'] == inputs(), 'Build sources changed: rerun render.sh build'
    for name, digest in proof['masters'].items():
        assert sha(MASTER/name) == digest, 'Changed built master: '+name
    print('Editable master and build inputs verified')


if __name__ == '__main__':
    if sys.argv[1] == 'record':
        proof = {'inputs': inputs(), 'masters': {name: sha(MASTER/name) for name in ('plain.blend', 'stealth-bomber.blend')}}
        (MASTER/'build-source.json').write_text(json.dumps(proof, indent=2)+'\n')
    else:
        check()

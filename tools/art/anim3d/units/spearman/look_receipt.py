"""Bind the painted look's calibration and code to the exact master."""
import hashlib
import json
from pathlib import Path

UNIT = Path(__file__).resolve().parent
CODE = [UNIT/'look.py', UNIT/'look_textures.py', UNIT/'continuity.py',
        UNIT.parents[1]/'kit/continuity.py', UNIT.parents[1]/'kit/look.py', UNIT.parents[1]/'kit/part_paint.py']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def state(master, folder):
    return {'master_sha256': digest(master/'spearman.blend'),
            'painting_sha256': digest(master/'spearman-source.png'),
            'reference_sha256': digest(Path('app/src/assets/units/spearman-256.png')),
            'code': {str(p.relative_to(UNIT.parents[1])): digest(p) for p in CODE},
            'calibration': {p.name: digest(p) for p in sorted(folder.iterdir())
                            if p.suffix in {'.png', '.json'} and p.name != 'receipt.json'}}

def write(master, folder):
    (folder/'receipt.json').write_text(json.dumps(state(master, folder), indent=2)+'\n')

def verify(master, folder):
    assert json.loads((folder/'receipt.json').read_text()) == state(master, folder), 'Stale look calibration; rerun prepare-look.sh'
    return digest(folder/'receipt.json')

if __name__ == '__main__':
    import os
    master = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
    write(master, master/'look')

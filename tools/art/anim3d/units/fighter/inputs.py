"""Bind the saved model to its build scripts and licensed input files."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT=Path(os.environ['ANIM_ROOT'])
UNIT=Path(__file__).resolve().parent
MASTER=ROOT/'masters/fighter'
ASSETS=ROOT/'assets/fighter'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot():
    lock=json.loads((UNIT/'assets.lock.json').read_text())
    for name,expected in lock['files'].items():
        assert digest(ASSETS/name)==expected,'Changed input: '+name
    paths=[UNIT/name for name in ('scene.py','finish.py','surfaces.py','prepare.py','assets.lock.json')]
    return {'scripts':{p.name:digest(p) for p in paths},'assets':lock['files'],
            'masters':{name:digest(MASTER/name) for name in ('fighter.blend','plain.blend')},
            'bakes':{p.name:digest(p) for p in sorted((MASTER/'textures/baked').glob('*.png'))}}

if __name__=='__main__':
    current=snapshot();path=MASTER/'build-inputs.json'
    if sys.argv[1]=='seal':
        path.write_text(json.dumps(current,indent=2)+'\n');print('Build inputs sealed')
    elif sys.argv[1]=='verify':
        assert json.loads(path.read_text())==current,'Saved model is stale; run build then finish'
        print('Saved model, build scripts, licensed inputs and six bakes verified')
    else:raise ValueError('Expected seal or verify')

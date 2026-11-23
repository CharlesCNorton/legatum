"""Fail before GPU work if packed geometry predates the texture or craft source."""
import hashlib
import json
import os
from pathlib import Path

root=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
unit=Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

expected=json.loads((unit/'assets.lock.json').read_text())['inputs']
for name,digest in expected.items():
    assert sha(root/'assets/archer'/name)==digest,('changed texture',name)
receipt=json.loads((root/'masters/archer/paint-inputs.json').read_text())
assert receipt['inputs']==expected,'Repaint master after changing texture inputs'
assert receipt['master_sha256']==sha(root/'masters/archer/archer.blend'),'Repaint master receipt is stale'
for name,digest in receipt['scripts'].items():
    assert sha(unit/name)==digest,('Repaint master after changing craft source',name)
print('ARCHER_INPUTS_PASS')

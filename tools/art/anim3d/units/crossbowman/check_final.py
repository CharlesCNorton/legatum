"""Require genuine current GPU512 and derived256 evidence for every final stage."""
import hashlib, json, os
from pathlib import Path
from PIL import Image
root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/crossbowman'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
for stage, count in {'b':3,'c':1,'d':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}.items():
    source = master / ('plain.blend' if stage == 'b' else 'clips/attack.blend' if stage == 'd' else 'clips/'+stage[2:]+'.blend' if stage.startswith('e-') else 'model.blend')
    manifest = json.loads((master/'renders/512'/stage/'render.json').read_text())
    assert manifest['device'] == 'GPU' and manifest['engine'] == 'CYCLES', ('Not GPU', stage)
    assert manifest['resolution'] == 512 and manifest['samples'] >= 64 and manifest['frames'] == count, ('Not final', stage)
    assert manifest['source_sha256'] == digest(source), ('Stale GPU source', stage)
    for size in (512,256):
        folder = master/'frames'/str(size)/stage
        info = json.loads((folder/'render.json').read_text())
        assert info['source_sha256'] == digest(source) and info['derived_resolution'] == size
        if stage != 'b':
            assert info['grade_sha256'] == digest(master/'grade.json'), ('Stale final grade',stage)
        for index in range(count):
            with Image.open(folder/f'{index:02d}.png') as image:
                assert image.size == (size,size) and image.mode == 'RGBA'
print('FINAL_MASTER_PASS: GPU512/64+, gallery256, all eight stages current')

feet=json.loads((master/'feet.json').read_text())
assert feet['device']=='GPU' and feet['source_sha256']==digest(master/'clips/move.blend')
assert len(feet['files'])==16
for f in feet['files']:assert digest(master/f['path'])==f['sha256']
print('FEET_MASTER_PASS: current GPU front/top cycle, 16 views')

"""Reject CPU/stale/incomplete evidence before issuing a GPU completion receipt."""
import os,json,hashlib,sys
from pathlib import Path
from PIL import Image
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
master=sha(M/'settler.blend')
for stage,count in {'b':3,'c':1,'c-details':1,'d':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}.items():
    manifest=json.loads((M/'renders'/stage/'render.json').read_text())
    assert (manifest['engine'],manifest['device'],manifest['resolution'],manifest['samples'])==('CYCLES','GPU',512,64),(stage,'GPU64/512 required')
    path=M/('settler-plain.blend' if stage=='b' else 'settler.blend')
    if stage=='d':path=M/'clips/attack.blend'
    if stage.startswith('e-'):path=M/'clips'/f'{stage[2:]}.blend'
    assert sha(path)==manifest['blend_sha256'],(stage,'stale blend')
    if stage!='b':assert master==manifest['master_sha256']
    for size in (512,256):
        files=list((M/f'frames-{size}'/stage).glob('*.png'));assert len(files)==count,(stage,size,'missing frames')
        for p in files:assert Image.open(p).size==(size,size)
feet=json.loads((M/'feet.json').read_text())
assert feet['source_sha256']==sha(M/'clips/move.blend'),'stale feet diagnostic'
assert feet['device']=='GPU','GPU feet diagnostic required'
for frame in feet['files']:assert sha(M/frame['path'])==frame['sha256'],'changed feet render'
if '--receipt' in sys.argv:
    validation=json.loads((M/'validation.json').read_text());video=json.loads((M/'video.json').read_text())
    assert video['atlas_sha256']==sha(Path('app/src/assets/units/anim/settler.webp'))
    receipt={'round':os.environ['ROUND'],'master_sha256':master,'validation':validation,'video':video,'art_approved':False}
    (R/'review/3d-v2'/f'settler-gpu-round{os.environ["ROUND"]}.json').write_text(json.dumps(receipt,indent=2))
print('GPU_MASTER_GATE_PASS')

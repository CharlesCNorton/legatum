"""Reject CPU/stale/upscaled masters; record success only after delivery and video."""
import hashlib
import json
import os
from pathlib import Path
import sys
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/archer'; REVIEW=R/'review/3d-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=sha(M/'archer.blend')
for stage,count in [('b',3),('c',1),('c-details',1),('d',4),('e-idle',8),('e-move',8),('e-attack',10),('e-hit',4),('e-death',10)]:
    meta=json.loads((M/'renders'/stage/'render.json').read_text())
    assert (meta['engine'],meta['device'],meta['resolution'],meta['samples'])==('CYCLES','GPU',512,64),(stage,'not GPU512/64')
    blend=M/'clips'/f'{stage[2:]}.blend' if stage.startswith('e-') else M/'clips/attack.blend' if stage=='d' else M/'archer.blend'
    assert meta['blend_sha256']==sha(blend),(stage,'stale blend')
    assert meta['source_sha256']==source,(stage,'stale source')
    for i in range(count):
        for size in (512,256):
            assert Image.open(M/f'frames-{size}'/stage/f'{i:02}.png').size==(size,size)
if '--receipt' in sys.argv:
    pack=json.loads((M/'pack.json').read_text()); validation=json.loads((REVIEW/'archer-validation.json').read_text());video=json.loads((REVIEW/'archer-video.json').read_text())
    assert validation['passed'] and not pack.get('preview',False)
    assert Path(video['path']).name==f'archer-round{os.environ.get("ROUND","2")}.mp4'
    (REVIEW/f'archer-gpu-round{os.environ.get("ROUND","2")}.json').write_text(json.dumps({'complete':True,'art_approved':False,'master_sha256':source,'pack':{k:v for k,v in pack.items() if k!='clips'},'video':video},indent=2))
print('GPU_MASTERS_PASS')

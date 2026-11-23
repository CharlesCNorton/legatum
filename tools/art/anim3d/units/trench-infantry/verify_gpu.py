"""Refuse a GPU completion receipt for CPU, stale or incomplete masters."""
import os,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/trench-infantry';V=R/'review/3d-v2'
stages={'b-plain':1,'c-textured-lit':1,'d-rig-poses':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
grade=json.loads((M/'grade.json').read_text())
assert grade['master_sha256']==digest(M/'trench-infantry.blend')
for stage,n in stages.items():
 manifest=json.loads((M/'renders'/stage/'render.json').read_text())
 assert manifest['device']=='GPU' and manifest['engine']=='CYCLES' and manifest['resolution']==512,(stage,manifest)
 assert manifest['frames']==n
 blend=M/('plain.blend' if stage=='b-plain' else 'trench-infantry.blend') if stage in ('b-plain','c-textured-lit') else M/'clips'/('attack.blend' if stage=='d-rig-poses' else stage[2:]+'.blend')
 assert manifest['blend_sha256']==digest(blend),(stage,'stale blend')
 assert manifest['samples']==int(os.environ.get('SAMPLES','48'))
 for size in (512,256):
  for i in range(n):assert Image.open(M/str(size)/stage/f'{i:02}.png').size==(size,size)
validation=json.loads((V/'trench-infantry-validation.json').read_text());assert validation['status']=='pass'
assert validation['frames']==40 and validation['quality']>=75 and validation['size']<=200000
audit=json.loads((M/'audit.json').read_text());assert audit['structural_checks']=='pass'
for suffix in ['f-restpose-compare.png','g-feet-check.png',f"round{os.environ.get('ROUND','1')}.mp4"]:assert (V/('trench-infantry-'+suffix)).stat().st_size>0
(V/f"trench-infantry-gpu-round{os.environ.get('ROUND','1')}.json").write_text(json.dumps({'status':'complete','art_approved':False,'master_sha256':hashlib.sha256((M/'trench-infantry.blend').read_bytes()).hexdigest(),'stages':stages},indent=2))
print('GPU masters, atlas, review and movie receipt verified')

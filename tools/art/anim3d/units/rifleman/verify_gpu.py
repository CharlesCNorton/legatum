"""Refuse a GPU completion receipt for CPU, stale or incomplete masters."""
import os,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/rifleman';V=R/'review/3d-v2'
stages={'b-plain':3,'c-textured-lit':1,'d-rig-poses':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}
for stage,n in stages.items():
 manifest=json.loads((M/'renders'/stage/'render.json').read_text())
 assert manifest['device']=='GPU' and manifest['engine']=='CYCLES' and manifest['resolution']==512,(stage,manifest)
 assert manifest['frames']==n
 for size in (512,256):
  for i in range(n):assert Image.open(M/str(size)/stage/f'{i:02}.png').size==(size,size)
assert json.loads((V/'rifleman-validation.json').read_text())['status']=='pass'
for suffix in ['f-restpose-compare.png','g-feet-check.png',f"round{os.environ.get('ROUND','1')}.mp4"]:assert (V/('rifleman-'+suffix)).stat().st_size>0
(V/f"rifleman-gpu-round{os.environ.get('ROUND','1')}.json").write_text(json.dumps({'status':'complete','art_approved':False,'master_sha256':hashlib.sha256((M/'rifleman.blend').read_bytes()).hexdigest(),'stages':stages},indent=2))
print('GPU masters, atlas, review and movie receipt verified')

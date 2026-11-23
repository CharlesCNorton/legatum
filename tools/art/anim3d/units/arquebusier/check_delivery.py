"""Independent GPU provenance/size gate before final packing and receipt."""
import hashlib,json,os,sys
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/arquebusier';V=R/'review/3d-v2'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
counts={'b-plain':1,'c-textured-lit':1,'d-rig-poses':4,'e-idle':8,'e-move':8,'e-attack':10,'e-hit':4,'e-death':10}
for stage,count in counts.items():
 manifest=json.loads((M/'renders'/stage/'render.json').read_text())
 assert manifest['engine']=='CYCLES' and manifest['device']=='GPU' and manifest['resolution']==512 and manifest['samples']>=48,(stage,'Not final GPU output')
 blend=M/'clips'/(stage[2:]+'.blend') if stage.startswith('e-') else M/('plain.blend' if stage=='b-plain' else 'clips/attack.blend' if stage=='d-rig-poses' else 'arquebusier.blend')
 assert manifest['blend_sha256']==digest(blend) and manifest['frames']==count,(stage,'Stale output')
 for i in range(count):
  for size in (256,512):assert Image.open(M/str(size)/stage/f'{i:02}.png').size==(size,size)
if '--receipt' in sys.argv:
 report=json.loads((V/'arquebusier-validation.json').read_text());assert report['status']=='pass'
 movie=V/f"arquebusier-round{os.environ.get('ROUND','2')}.mp4";assert movie.stat().st_size>0
 receipt={'round':os.environ.get('ROUND','2'),'master_sha256':digest(M/'arquebusier.blend'),'video_sha256':digest(movie),'validation':report,'visual_approval':False}
 (V/f"arquebusier-gpu-round{os.environ.get('ROUND','2')}.json").write_text(json.dumps(receipt,indent=2))
print('GPU512/256 provenance verified')

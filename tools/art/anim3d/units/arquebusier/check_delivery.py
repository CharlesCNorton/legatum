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
feet=json.loads((M/'feet/evidence.json').read_text())
assert feet['device']=='GPU' and feet['clip_sha256']==digest(M/'clips/move.blend'),'Stale or CPU foot review'
assert feet['resolution']==512 and feet['samples']>=48,'Foot review below final resolution/samples'
assert feet['contact']['max_support_yaw_deg']<20 and feet['contact']['max_stance_error_m']<.025,'Foot path failed'
assert feet['contact']['max_actual_shoe_yaw_deg']<20,'Actual shoe direction failed'
assert (V/'arquebusier-g-feet-check.png').is_file()
for view in ('top','front'):
 for i in range(8):
  for size in (256,512):assert Image.open(M/str(size)/'g-feet-check'/f'{view}-{i:02}.png').size==(size,size)
if '--receipt' in sys.argv:
 report=json.loads((V/'arquebusier-validation.json').read_text());assert report['status']=='pass'
 movie=V/f"arquebusier-round{os.environ.get('ROUND','3')}.mp4";assert movie.stat().st_size>0
 receipt={'round':os.environ.get('ROUND','3'),'master_sha256':digest(M/'arquebusier.blend'),'video_sha256':digest(movie),'validation':report,'visual_approval':False}
 (V/f"arquebusier-gpu-round{os.environ.get('ROUND','3')}.json").write_text(json.dumps(receipt,indent=2))
print('GPU512/256 provenance verified')

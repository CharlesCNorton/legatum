"""File contract checks independent of Blender; visual approval remains separate."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/biplane';D=R/'review/3d-v2';p=Path('app/src/assets/units/anim/biplane.webp');meta=json.loads(p.with_suffix('.json').read_text());report=json.loads((M/'validation.json').read_text())
assert p.stat().st_size<=200000 and meta['atlas']['quality']>=75
assert report['atlas_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
assert report['json_sha256']==hashlib.sha256(p.with_suffix('.json').read_bytes()).hexdigest()
assert meta['frame']=={'w':160,'h':160,'ax':73,'ay':140}
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 c=meta['clips'][clip];assert c['frames']==n and len(c['rects'])==n
 preview=os.environ.get('ALLOW_PREVIEW')=='1'
 assert report['renders'][clip]['resolution']==512 or preview,('native 512 masters required',clip)
 for size in ((256,) if preview else (256,512)):
  for i in range(n):
   im=Image.open(M/str(size)/('e-'+clip)/f'{i:02}.png');assert im.size==(size,size)
 assert (D/f'biplane-e-{clip}-strip.png').exists() and (D/f'biplane-e-{clip}.webp').exists()
for stage in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare','g-feet-check','g-decoded-atlas']:assert (D/f'biplane-{stage}.png').exists()
for name in ['tapered-fuselage','engine-cowling','upper-cambered-wing','lower-cambered-wing']:
 for kind in ['AO','curvature']:assert Image.open(M/'textures'/f'GEO-{name}-{kind}.png').size==(256,256)
if os.environ.get('REQUIRE_GPU')=='1':
 from preflight import gpu
 gpu()
print(('CPU PREVIEW' if os.environ.get('ALLOW_PREVIEW')=='1' else 'FINAL')+' PASS: atlas contract, q>=75, <=200KB, 40 trim offsets, master sizes, eight bakes, all review stages. Visual parity is not asserted.')

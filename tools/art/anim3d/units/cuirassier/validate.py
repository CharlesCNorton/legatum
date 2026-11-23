"""Validate decoded delivery, trim reconstruction, provenance, motion and death hold."""
from pathlib import Path
from PIL import Image,ImageChops
import os,json,hashlib
from delivery_common import token
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';V=R/'review/3d-v2';P=Path('app/src/assets/units/anim/cuirassier.webp');meta=json.loads(P.with_suffix('.json').read_text());atlas=Image.open(P).convert('RGBA');report=json.loads((V/'cuirassier-pack.json').read_text())
assert P.stat().st_size<=200000;assert meta['atlas']['quality']>=75;assert meta['frame']=={'w':160,'h':160,'ax':103,'ay':140}
assert report['quality']==meta['atlas']['quality']
assert report['atlas_sha256']==hashlib.sha256(P.read_bytes()).hexdigest();assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);assert atlas.getchannel('A').getextrema()==(0,255)
assert report['master_sha256']==hashlib.sha256((M/'cuirassier.blend').read_bytes()).hexdigest()
assert report['grade_sha256']==hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
result={};boxes=[]
for name,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 c=meta['clips'][name];assert c['frames']==n==len(c['rects']);frames=[];raw=[]
 assert c['fps']=={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[name]
 assert c['loop']==(name in ['idle','move'])
 manifest=json.loads((M/'renders'/f'e-{name}'/'render.json').read_text())
 assert manifest==report['sources'][name]['render']
 assert manifest['blend_sha256']==hashlib.sha256((M/'clips'/f'{name}.blend').read_bytes()).hexdigest()
 assert manifest['source_master_sha256']==report['master_sha256'] and manifest['grade_sha256']==report['grade_sha256']
 for i,r in enumerate(c['rects']):
  x,y,w,h,ox,oy=[r[k] for k in ['x','y','w','h','ox','oy']];assert 0<=ox<160 and 0<=oy<160 and ox+w<=160 and oy+h<=160;assert x>=2 and y>=2 and x+w<=atlas.width-2 and y+h<=atlas.height-2
  box=(x,y,x+w,y+h)
  for a,b,d,e in boxes:assert box==(a,b,d,e) or box[2]<=a or box[0]>=d or box[3]<=b or box[1]>=e,'Packed rectangles overlap'
  boxes.append(box);frame=Image.new('RGBA',(160,160));frame.paste(atlas.crop(box),(ox,oy));frames.append(frame)
  p=M/'renders'/f'e-{name}'/f'{i:02}.png';im=Image.open(p).convert('RGBA');raw.append(p.read_bytes());bbox=im.getchannel('A').point(lambda a:255 if a>24 else 0).getbbox();assert bbox
  assert bbox[0]>0 and bbox[1]>0 and bbox[2]<im.width and bbox[3]<im.height,f'{name} {i} touches render boundary {bbox}'
  assert hashlib.sha256(p.read_bytes()).hexdigest()==report['sources'][name]['frames'][str(i)]
  assert ImageChops.difference(frame.getchannel('A'),token(im).getchannel('A')).getbbox() is None,'Decoded alpha differs from source'
  for gutter in [(x-2,y-2,x+w+2,y),(x-2,y+h,x+w+2,y+h+2),(x-2,y,x,y+h),(x+w,y,x+w+2,y+h)]:
   assert atlas.getchannel('A').crop(gutter).getbbox() is None,'Opaque gutter'
 assert len(set(raw))>1,f'No motion: {name}'
 if name=='death':
  assert raw[-1]==raw[-2],'Death must hold identical final pixels'
  assert frames[-1].tobytes()==frames[-2].tobytes(),'Decoded death must hold too'
 result[name]={'frames':n,'motion':True,'trim_reconstruction':True,'no_boundary_clipping':True}
(V/'cuirassier-validation.json').write_text(json.dumps({'passed':True,'bytes':P.stat().st_size,'quality':meta['atlas']['quality'],'clips':result},indent=2));print('VALIDATION PASS: 40 frames; trim bounds, padding, hashes, motion, held death, quality and size')

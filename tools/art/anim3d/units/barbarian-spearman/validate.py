"""Independent provenance, trim reconstruction, alpha, bounds and timing checks."""
from pathlib import Path
import os,json,hashlib
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-spearman';O=Path('app/src/assets/units/anim')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
path=O/'barbarian-spearman.webp';meta=json.loads(path.with_suffix('.json').read_text());report=json.loads((M/'pack.json').read_text());atlas=Image.open(path).convert('RGBA')
assert path.stat().st_size<=200000 and report['quality']>=75
assert sha(path)==report['atlas_sha256'] and sha(path.with_suffix('.json'))==report['metadata_sha256']
assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']) and atlas.getchannel('A').getextrema()==(0,255)
assert meta['frame']=={'w':160,'h':160,'ax':80,'ay':137}
assert report['source_sha256']==sha(M/'barbarian-spearman.blend') and report['grade_sha256']==sha(M/'grade.json')
if os.environ.get('REQUIRE_GPU')=='1':
 assert not report['preview'],'CPU preview is not a final GPU delivery'
 for stage in ['b','c','c-details','d','g-feet']+[f'e-{c}' for c in meta['clips']]:
  settings=json.loads((M/'renders'/stage/'render.json').read_text())
  assert (settings['device'],settings['resolution'],settings['samples'])==('GPU',512,64),(stage,settings)
checks=[];used=set();coverage=Image.new('L',atlas.size)
for row,(clip,count,fps,loop) in enumerate([('idle',8,10,True),('move',8,12,True),('attack',10,14,False),('hit',4,12,False),('death',10,10,False)]):
 manifest=report['renders'][clip];assert manifest==json.loads((M/'renders'/f'e-{clip}'/'render.json').read_text())
 assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend') and manifest['source_sha256']==report['source_sha256']
 assert manifest['grade_sha256']==report['grade_sha256'];size=manifest['resolution']
 info=meta['clips'][clip];assert (info['row'],info['frames'],info['fps'],info['loop'])==(row,count,fps,loop)
 assert len(info['rects'])==count
 hashes=[];decoded=[]
 for i,rect in enumerate(info['rects']):
  x,y,w,h,ox,oy=[rect[k] for k in ['x','y','w','h','ox','oy']]
  assert x>=2 and y>=2 and x+w+2<=atlas.width and y+h+2<=atlas.height
  assert 0<=ox and ox+w<=160 and 0<=oy and oy+h<=160
  box=(x,y,x+w,y+h)
  if box not in used:
   assert coverage.crop(box).getbbox() is None,'Overlapping packed rectangles'
   coverage.paste(255,box);used.add(box)
  for n in [v for v in [512,256] if v<=size]:assert Image.open(M/str(n)/clip/f'{i:02}.png').size==(n,n)
  source=M/'renders'/f'e-{clip}'/f'{i:02}.png';assert report['frames'][f'{clip}/{i:02}']==sha(source)
  frame=Image.open(source).convert('RGBA');assert frame.size==(size,size)
  master=Image.open(M/str(size)/clip/f'{i:02}.png').convert('RGBA');assert frame.tobytes()==master.tobytes(),'Stale exported master'
  bounds=frame.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
  assert bounds and min(bounds[:2])>0 and max(bounds[2:])<size,f'{clip}/{i} clipped: {bounds}'
  original=frame.resize((160,160),Image.Resampling.BICUBIC).getchannel('A')
  restored=Image.new('RGBA',(160,160));restored.paste(atlas.crop(box),(ox,oy))
  assert ImageChops.difference(original,restored.getchannel('A')).getbbox() is None,f'{clip}/{i}: alpha mismatch'
  hashes.append(hashlib.sha256(frame.tobytes()).hexdigest());decoded.append(restored.tobytes())
 assert len(set(hashes))>1 and len(set(decoded))>1,f'{clip} has no motion'
 if clip=='death':assert hashes[-1]==hashes[-2] and decoded[-1]==decoded[-2],'Death must hold identically'
 checks.append(f'{clip}: {count} frames, timing, {size}px masters, motion, bounds, exact alpha reconstruction')
assert ImageChops.multiply(atlas.getchannel('A'),ImageChops.invert(coverage)).getbbox() is None,'Nontransparent atlas padding'
result={'passed':True,'preview':report['preview'],'checks':checks,'atlas_bytes':path.stat().st_size,'quality':report['quality'],'note':'Technical checks only; not art approval.'}
for dest in [M/'validation.json',R/'review/3d-v2/barbarian-spearman-validation.json']:dest.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

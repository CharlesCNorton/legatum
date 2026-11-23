"""Validate the actual decoded trimmed delivery and its source manifests."""
import hashlib,json,os
from pathlib import Path
from PIL import Image,ImageChops
from deliver import logical_frame,CLIPS
from check_delivery import check
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));V=R/'review/3d-v2';M=R/'masters/eagle-warrior';slug='eagle-warrior';p=Path('app/src/assets/units/anim')/slug
meta=json.loads(p.with_suffix('.json').read_text());atlas=Image.open(p.with_suffix('.webp')).convert('RGBA');report=json.loads((V/f'{slug}-pack.json').read_text());assert p.with_suffix('.webp').stat().st_size<=200000;assert report['quality']>=75;assert hashlib.sha256(p.with_suffix('.webp').read_bytes()).hexdigest()==report['atlas_sha256'];assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);assert meta['frame']['w']==meta['frame']['h']==160
assert hashlib.sha256((M/f'{slug}.blend').read_bytes()).hexdigest()==report['master_sha256'],'Stale master'
assert hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()==report['grade_sha256'],'Stale grade'
check(R,report['source_resolution'],gpu=all(v['device']=='GPU' for v in report['render_sources'].values()))
assert hashlib.sha256(p.with_suffix('.json').read_bytes()).hexdigest()==report['metadata_sha256'],'Stale metadata'
assert meta['version']==2 and meta['frame']['ax']==83.75 and meta['frame']['ay']==139.375
checks=[]
for row,(clip,n) in enumerate([('idle',8),('move',8),('attack',10),('hit',4),('death',10)]):
 c=meta['clips'][clip];assert c['frames']==len(c['rects'])==n;assert c['row']==row;assert (c['frames'],c['fps'],c['loop'])==CLIPS[clip];hashes=[];decoded_hashes=[]
 for i,r in enumerate(c['rects']):
  x,y,w,h,ox,oy=[r[k] for k in ['x','y','w','h','ox','oy']];assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height;assert 0<=ox<ox+w<=160 and 0<=oy<oy+h<=160
  reconstructed=Image.new('RGBA',(160,160));reconstructed.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));assert reconstructed.getchannel('A').getextrema()==(0,255)
  source_path=M/'graded/256'/('e-'+clip)/f'{i:02}.png'
  assert hashlib.sha256(source_path.read_bytes()).hexdigest()==report['frames_sha256'][f'{clip}/{i}'],'Stale frame'
  source=logical_frame(Image.open(source_path).convert('RGBA'))
  decoded_hashes.append(hashlib.sha256(reconstructed.tobytes()).hexdigest())
  for gutter in [(x-1,y-1,x+w+1,y),(x-1,y+h,x+w+1,y+h+1),(x-1,y,x,y+h),(x+w,y,x+w+1,y+h)]:
   assert atlas.crop(gutter).getchannel('A').getbbox() is None,'Nontransparent gutter'
  assert ImageChops.difference(source.getchannel('A'),reconstructed.getchannel('A')).getbbox() is None,'Trim reconstruction alpha mismatch'
  hashes.append(hashlib.sha256(source.tobytes()).hexdigest());bbox=source.getchannel('A').point(lambda a:255 if a>24 else 0).getbbox();assert bbox[0]>0 and bbox[1]>0 and bbox[2]<160 and bbox[3]<160,(clip,i,'clipping',bbox)
 assert len(set(hashes))>1,(clip,'no motion')
 if clip=='death':
  assert hashes[-1]==hashes[-2],'death must settle'
  assert decoded_hashes[-1]==decoded_hashes[-2],'decoded death must settle'
 checks.append(f'{clip}: {n} frames; alpha/trim/margins/motion valid')
result={'ok':True,'checks':checks,'bytes':report['bytes'],'quality':report['quality'],'source_resolution':report['source_resolution'],'gpu':all(v['device']=='GPU' for v in report['render_sources'].values()),'art_approved':False}
(V/f'{slug}-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

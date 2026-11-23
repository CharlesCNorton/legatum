"""Delivery contract, bounded alpha reconstruction, clipping, motion and provenance."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/peltast';V=R/'review/3d-v2';p=Path('app/src/assets/units/anim/peltast.webp');data=json.loads(p.with_suffix('.json').read_text());pack=json.loads((V/'peltast-pack.json').read_text());atlas=Image.open(p).convert('RGBA');counts={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
assert data['version']==2 and data['frame']['w']==data['frame']['h']==160
assert p.stat().st_size<=200000 and pack['quality']>=75
assert atlas.size==(data['atlas']['w'],data['atlas']['h']);assert hashlib.sha256(p.read_bytes()).hexdigest()==pack['atlas_sha256'];assert list(data['clips'])==list(counts)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
report={};allrects=[]
for row,(clip,n) in enumerate(counts.items()):
 delivery=json.loads((M/'raw'/f'e-{clip}'/'delivery.json').read_text())
 assert delivery['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),f'{clip}: changed blend'
 assert delivery['grade_sha256']==sha(M/'grade.json'),f'{clip}: changed grade'
 assert json.loads((M/'clips'/f'{clip}.json').read_text())['source_sha256']==sha(M/'peltast.blend'),f'{clip}: changed source master'
 c=data['clips'][clip];assert c['row']==row and c['frames']==n and len(c['rects'])==n
 frames=[]
 for i,r in enumerate(c['rects']):
  assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
  assert r['x']>=1 and r['y']>=1 and r['x']+r['w']<atlas.width and r['y']+r['h']<atlas.height
  box=(r['x'],r['y'],r['x']+r['w'],r['y']+r['h']);allrects.append(box);im=Image.new('RGBA',(160,160));im.paste(atlas.crop(box),(r['ox'],r['oy']));frames.append(im)
  path=M/'256'/f'e-{clip}'/f'{i:02}.png';assert hashlib.sha256(path.read_bytes()).hexdigest()==pack['source_sha256'][f'{clip}/{i}'];source=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
  expected=source.getchannel('A');levels=pack['alpha_levels']
  if levels<256:expected=expected.point(lambda v:round(round(v*(levels-1)/255)*255/(levels-1)))
  assert expected.tobytes()==im.getchannel('A').tobytes(),f'{clip}/{i} trim/alpha mismatch'
  assert ImageChops.difference(source.getchannel('A'),im.getchannel('A')).getextrema()[1]<=pack['alpha_max_error'],'Alpha error budget exceeded'
  bb=source.getchannel('A').point(lambda x:255 if x>12 else 0).getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<160 and bb[3]<160,f'{clip}/{i}: clipped {bb}'
  assert Image.open(M/'512'/f'e-{clip}'/f'{i:02}.png').size==(512,512),'Missing 512 master'
 hashes={hashlib.sha256(im.tobytes()).hexdigest() for im in frames};assert len(hashes)>1,f'{clip} static'
 if clip=='death':
  # Raw terminal samples must be byte-identical; atlas RGB can vary by lossy block context.
  a=Image.open(M/'256'/'e-death'/'08.png');b=Image.open(M/'256'/'e-death'/'09.png');assert a.tobytes()==b.tobytes(),'Death not held'
 report[clip]={'frames':n,'distinct_decoded_frames':len(hashes),'trim_alpha':'exact after bounded quantization','clipping':'clear'}
for i,a in enumerate(allrects):
 for b in allrects[i+1:]:assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1],'Overlapping rects'
for name in ['b-plain','c-textured-lit','c-details','d-rig-poses','f-restpose-compare']+[f'e-{c}-strip' for c in counts]:assert (V/f'peltast-{name}.png').exists(),name
result={'checks':'passed','bytes':p.stat().st_size,'quality':pack['quality'],'alpha_levels':pack['alpha_levels'],'alpha_max_error':pack['alpha_max_error'],'clips':report,'limitations':'Technical contract only; no visual quality approval or runtime integration.'};(V/'peltast-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

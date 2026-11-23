"""Read back delivered atlas: bounds, alpha, 40 frames, movement and held death."""
import json,os,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));V=R/'review/3d-v2';O=Path('app/src/assets/units/anim');meta=json.loads((O/'cavalry.json').read_text());report=json.loads((V/'cavalry-pack.json').read_text());atlas=Image.open(O/'cavalry.webp').convert('RGBA')
assert report['quality']>=75 and (O/'cavalry.webp').stat().st_size<=200000
assert hashlib.sha256((O/'cavalry.webp').read_bytes()).hexdigest()==report['atlas_sha256']
assert hashlib.sha256((O/'cavalry.json').read_bytes()).hexdigest()==report['json_sha256']
assert meta['atlas']=={'w':atlas.width,'h':atlas.height}
assert meta['frame']=={'w':160,'h':160,'ax':87,'ay':141}
assert list(meta['clips'])==['idle','move','attack','hit','death']
checks={};total=0
for row,(name,clip) in enumerate(meta['clips'].items()):
 assert clip['fps']==[10,12,14,12,10][row] and clip['loop']==(row<2)
 expected=[8,8,10,4,10][row];assert clip['frames']==len(clip['rects'])==expected and clip['row']==row;frames=[]
 for i,r in enumerate(clip['rects']):
  x,y,w,h,ox,oy=[r[k] for k in ['x','y','w','h','ox','oy']]
  assert 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height
  assert 0<ox<ox+w<160 and 0<oy<oy+h<160
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));assert im.getchannel('A').getextrema()==(0,255);frames.append(im)
  source=R/'masters/cavalry/renders'/f'e-{name}'/f'{i:02}.png'
  assert hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256'][f'{name}/{i}']
  expected_alpha=Image.open(source).convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA').getchannel('A')
  assert im.getchannel('A').tobytes()==expected_alpha.tobytes(),f'{name}/{i}: decoded alpha mismatch'
 assert len({im.tobytes() for im in frames})>1,f'{name}: no motion'
 # Lossy atlas tiles have distinct transform blocks; held source pixels must match exactly.
 if name=='death':
  assert report['source_sha256']['death/8']==report['source_sha256']['death/9']
  assert frames[-1].tobytes()==frames[-2].tobytes(),'Decoded death hold differs'
 total+=expected;checks[name]={'frames':expected,'bounds':True,'transparent':True,'motion':True}
assert total==40
(V/'cavalry-validation.json').write_text(json.dumps({'passed':True,'checks':checks,'bytes':report['bytes'],'quality':report['quality'],'art_approved':False},indent=2)+'\n');print('VALIDATED 40 trimmed frames; q>=75; <=200KB; transparent, motion, held source death')

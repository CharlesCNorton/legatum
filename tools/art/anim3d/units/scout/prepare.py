"""Prepare licensed painting and generated hidden-side fills outside git."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/scout'; M=R/'masters/scout'; M.mkdir(parents=True,exist_ok=True)
pin=Path(__file__).with_name('assets.lock.json')
if pin.exists():
 expected=json.loads(pin.read_text())
 for name in ['painting-source.png','painted-fills.png']:
  assert hashlib.sha256((A/name).read_bytes()).hexdigest()==expected[name], 'Input hash mismatch: '+name
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/scout-256.png').convert('RGBA')
b=ref.getchannel('A').getbbox(); crop=source.crop(source.getchannel('A').getbbox())
aligned=Image.new('RGBA',(1024,1024));crop=crop.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
aligned.paste(crop,(b[0]*4,b[1]*4));aligned.save(A/'projection.png')
f=Image.open(A/'painted-fills.png'); w,h=f.size
for name,rect in {'linen':(0,0,w//2,h//2),'wool':(w//2,0,w,h//2),'leather':(0,h//2,w//2,h),'skin':(w//2,h//2,w,h)}.items(): f.crop(rect).save(A/(name+'.png'))
(M/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
print('Prepared scout projection and four generated fills')
# Semantic regions preserve painted highlight/shadow pixels. Colour thresholds
# broke the cowl into gold/green islands by discarding its warm fold highlights.
from PIL import ImageDraw, ImageFilter, ImageChops
regions = {
 'wool': [[(122,50),(153,40),(166,55),(185,53),(191,64),(183,84),(160,77),(143,67)],
          [(125,67),(146,93),(136,139),(117,160),(96,164),(59,145),(54,124),(86,108)]],
 'linen': [[(121,58),(148,65),(165,78),(184,74),(189,93),(176,107),(193,124),(176,151),(151,157),(119,145),(124,117),(135,98),(113,86)]],
}
for name in ['wool','linen','skin']:
 im=aligned.copy()
 if name in regions:
  mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
  for polygon in regions[name]:d.polygon([(x*4,y*4) for x,y in polygon],fill=255)
  mask=mask.filter(ImageFilter.GaussianBlur(3))
  im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
 else:
  pixels=[]
  for index,(r,g,b,a) in enumerate(im.getdata()):
   x=(index%im.width)/4;y=(index//im.width)/4
   keep=(b>g*.57 and g<r*.83 and r>80) or (158<x<197 and 15<y<65)
   pixels.append((r,g,b,a if keep else 0))
  im.putdata(pixels)
 im.save(A/('projection-'+name+'.png'))
(M/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png') if p.name!='projection-check.png'},indent=2))

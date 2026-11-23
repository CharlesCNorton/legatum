"""Register the archived painting to the shipped token and pin external inputs."""
import hashlib,json,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/cavalry';M=R/'masters/cavalry'
source=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/cavalry-256.png').convert('RGBA');b=ref.getchannel('A').getbbox();patch=source.crop(source.getchannel('A').getbbox()).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.paste(patch,(b[0]*4,b[1]*4));out.save(A/'painting-aligned-1024.png')
# Painted fills from the mounted family's original imagegen sheet, CC BY 4.0.
# Tint the linen swatch inside the Blender material, preserving its brush texture.
# Conservative chroma masks for visible coat and blue textile colours.
for kind in ['coat','cloth','skin']:
 im=out.copy();alpha=[]
 for rr,gg,bb,aa in im.get_flattened_data():
  if kind=='cloth':valid=bb>=rr*.93 and bb>=gg*.95 and rr<150
  elif kind=='coat':valid=rr>bb*1.18 and rr>gg*1.08
  else:valid=rr>gg*1.1 and rr>bb*1.3
  alpha.append(aa if valid else 0)
 mask=Image.new('L',im.size);mask.putdata(alpha);im.putalpha(mask.filter(ImageFilter.GaussianBlur(1)));im.save(A/f'projection-{kind}.png')

# Full source pigment retains grey muzzle, narrow blaze, fetlocks and hair.
# Visibility on the actual rest mesh is tested in paint.py; no alpha cutouts.
out.save(A/'projection-horse.png')

inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.iterdir() if p.suffix in ['.png','.glb']}
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text());lock['paint_assets_sha256']={k:v for k,v in inputs.items() if k!='Horse.glb'}
assert inputs['Horse.glb']==lock['sha256'];Path(__file__).with_name('assets.lock.json').write_text(json.dumps(lock,indent=2)+'\n');(M/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
print('PREPARED cavalry painting and pinned inputs')

"""Register full painting to the committed token's alpha bounds; pin inputs."""
import os,json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/archer';A.mkdir(exist_ok=True)
src=Image.open(A/'painting-source.png').convert('RGBA');token=Image.open('app/src/assets/units/archer-256.png').convert('RGBA')
# Source is a magenta studio background. Use a soft chroma mask only for texture blending.
if src.getchannel('A').getextrema()==(255,255):
 pixels=[]
 for r,g,b,a in src.getdata():
  mag=min(r,b)-g;alpha=round(255*max(0,min(1,(70-mag)/35))) if r>100 and b>80 else 255;pixels.append((r,g,b,alpha))
 src.putdata(pixels)
bbox=src.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();tb=token.getbbox();aligned=Image.new('RGBA',(1024,1024));box=tuple(v*4 for v in tb);crop=src.crop(bbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS);aligned.paste(crop,box[:2]);aligned.save(A/'painting-aligned.png')
# Existing generated fills from mounted lane; no regeneration or hidden dependency.
for kind in ['linen','bronze','hair','coat']:
 shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'fill-{kind}.png')
records={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(A.glob('*.png'))};lock=Path(__file__).with_name('assets.lock.json')
if lock.exists():
 expected=json.loads(lock.read_text())['inputs'];assert records==expected,'External texture inputs differ from committed hashes'
(A/'inputs.json').write_text(json.dumps(records,indent=2))
print('PREPARED',src.size,bbox,tb)

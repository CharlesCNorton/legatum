"""External painting/fill inputs; keep archive masters out of Git."""
from pathlib import Path
from PIL import Image
import json, hashlib, os
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=ROOT/'assets/tagmatic-soldier'; A.mkdir(parents=True,exist_ok=True)
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for key in ['painting','painted_fills','stone_fill']:
 entry=lock[key];path=A/entry['file']
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],f'Changed input: {path}'
for name,digest in lock['motion']['files'].items():
 assert hashlib.sha256((ROOT/'assets/quaternius-ual'/name).read_bytes()).hexdigest()==digest,f'Changed motion input: {name}'
src=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/tagmatic-soldier-256.png').convert('RGBA')
b=ref.getchannel('A').getbbox(); p=src.crop(src.getchannel('A').getbbox())
p=p.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.paste(p,(b[0]*4,b[1]*4));out.save(A/'painting-aligned.png')
# Register the generated clean plate to the original stone, not its changed
# canvas. Preserve the original unoccluded lower rim. Alpha never cuts geometry.
plate=Image.open(A/'stone-fill-source.png').convert('RGBA')
bounds=plate.getchannel('A').point(lambda x:255 if x>160 else 0).getbbox()
plate=plate.crop(bounds).resize((432,140),Image.Resampling.LANCZOS)
clean=Image.new('RGBA',(1024,1024));clean.paste(plate,(256,836))
clean.paste(out.crop((256,934,688,976)),(256,934))
clean.save(A/'stone-projection.png')
im=Image.open(A/'painted-fills.png').convert('RGB');w,h=im.size
for name,box in zip(['cloth','steel','leather','gold'],[(0,0,w//2,h//2),(w//2,0,w,h//2),(0,h//2,w//2,h),(w//2,h//2,w,h)]):
 im.crop(box).resize((512,512),Image.Resampling.LANCZOS).save(A/f'fill-{name}.png')
(A/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
print('Prepared source-aligned painting and painted material fills',b)

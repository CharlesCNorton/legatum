"""Align the full painting to the shipped token; assets stay outside git."""
from pathlib import Path
import os, json, hashlib, sys
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
A=R/'assets/barbarian-spearman'; A.mkdir(parents=True,exist_ok=True)
lockfile=Path(__file__).with_name('assets.lock.json')
if '--update-lock' not in sys.argv:
 for name,digest in json.loads(lockfile.read_text()).items():
  assert hashlib.sha256((A/name).read_bytes()).hexdigest()==digest, f'Changed input: {name}'
src=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/barbarian-spearman-256.png').convert('RGBA')
box=ref.getchannel('A').getbbox(); patch=src.crop(src.getchannel('A').getbbox())
out=Image.new('RGBA',(1024,1024));out.paste(patch.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS),(box[0]*4,box[1]*4));out.save(A/'painting-aligned.png')
print('SOURCE',src.size,'TOKEN BOUNDS',box)
# Reuse the project's generated linen and hair fills, already licensed in SOURCES.md.
for name in ['linen','hair']:
 if (A/f'fill-{name}.png').exists():continue
 p=R/f'assets/horseman/fill-{name}.png'
 if not p.exists():
  atlas=Image.open(R/'assets/horseman/painted-fills.png');w,h=atlas.size
  atlas.crop((w//2,0 if name=='linen' else h//2,w,h//2 if name=='linen' else h)).save(A/f'fill-{name}.png')
 else:Image.open(p).save(A/f'fill-{name}.png')
# Register the generated clean stone plate as pigment, never silhouette geometry.
plate=Image.open(A/'stone-fill-source.png').convert('RGBA')
patch=plate.crop(plate.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox())
stone=Image.new('RGBA',(1024,1024))
stone.paste(patch.resize((580,196),Image.Resampling.LANCZOS),(215,778))
stone.save(A/'stone-fill-aligned.png')
Image.open(A/'cloth-underpaint-source.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS).save(A/'cloth-underpaint-aligned.png')
# Existing original generated pelt and leather from the barbarian archer lane.
for name in ['fur','leather']:
 if not (A/f'fill-{name}.png').exists():Image.open(R/f'assets/barbarian-archer/fill-{name}.png').save(A/f'fill-{name}.png')
lock={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}
if '--update-lock' in sys.argv:lockfile.write_text(json.dumps(lock,indent=2)+'\n')
else:assert lock==json.loads(lockfile.read_text()),'Prepared inputs differ from pinned assets'

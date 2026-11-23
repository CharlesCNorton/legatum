"""Register the original source to the shipped token and copy licensed painted fills."""
import os,json,hashlib,shutil,urllib.request
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/barbarian-musketman';A.mkdir(exist_ok=True)
if not (A/'painting-source.png').exists():
 urllib.request.urlretrieve('https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-musketman-source.png',A/'painting-source.png')
src=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/barbarian-musketman-256.png').convert('RGBA')
b=ref.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();sb=src.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();box=tuple(v*4 for v in b)
im=Image.new('RGBA',(1024,1024));im.paste(src.crop(sb).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),box[:2]);im.save(A/'projection.png')
for kind in ('linen','coat','hair','bronze'):
 if not (A/f'{kind}-fill.png').exists():shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'{kind}-fill.png')
(A/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
print('Prepared source',src.size,sb,'registered to',b)

"""Verify external art inputs and prepare projection/fill images reproducibly."""
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen

from PIL import Image

ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=ROOT/'assets/war-elephant';A.mkdir(parents=True,exist_ok=True)
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for name,record in lock.items():
    path=A/name
    if not path.exists() and 'url' in record:
        with urlopen(record['url'],timeout=60) as response:path.write_bytes(response.read())
    if not path.exists():raise RuntimeError(f'Missing external master {path}; restore the pinned generated art, do not regenerate silently')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],f'Changed input: {path}'
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/war-elephant-256.png').convert('RGBA')
box=ref.getchannel('A').getbbox();patch=source.crop(source.getchannel('A').getbbox())
out=Image.new('RGBA',(1024,1024))
out.paste(patch.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS),(box[0]*4,box[1]*4))
out.save(A/'painting-aligned.png')
im=Image.open(A/'painted-fills.png');w,h=im.size
for name,box in [('skin',(0,0,w//2,h//2)),('red',(w//2,0,w,h//2)),('wood',(0,h//2,w//2,h)),('linen',(w//2,h//2,w,h))]:
    im.crop(box).save(A/f'fill-{name}.png')
print('PREPARED verified painting, clean stone plate and four painted fills')

"""Prepare and pin reusable external art inputs; masters never enter git."""
from pathlib import Path
import os,json,hashlib,shutil
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/knight';A.mkdir(parents=True,exist_ok=True)
s=Image.open(A/'knight-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/knight-256.png').convert('RGBA');box=ref.getchannel('A').getbbox();s=s.crop(s.getchannel('A').getbbox());s=s.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);out=Image.new('RGBA',(1024,1024));out.paste(s,(box[0]*4,box[1]*4));out.save(A/'painting-aligned.png')
for name in ['linen','bronze','hair']:
 dest=A/f'fill-{name}.png'
 if not dest.exists():shutil.copyfile(R/f'assets/horseman/fill-{name}.png',dest)
files=[A/'knight-source.png',A/'painting-aligned.png',R/'assets/horseman/Horse.glb']+[A/f'fill-{n}.png' for n in ['linen','bronze','hair']]
(A/'inputs.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
print('KNIGHT_INPUTS_READY')

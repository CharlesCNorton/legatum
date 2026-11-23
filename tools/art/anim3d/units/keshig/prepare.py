"""Register source alpha to the shipped token; keep every source outside git."""
import hashlib,json,os,shutil
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=R/'assets/keshig'; M=R/'masters/keshig'; M.mkdir(parents=True,exist_ok=True)
src=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/keshig-256.png').convert('RGBA')
b=ref.getchannel('A').getbbox(); sb=src.getchannel('A').getbbox()
# The downloaded source has a keyed transparent background.
assert sb and sb!=(0,0,*src.size), 'Source must be keyed before registration'
patch=src.crop(sb).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.paste(patch,(b[0]*4,b[1]*4));out.save(A/'projection.png')
for kind in ['coat','linen','bronze','hair']:
 shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'fill-{kind}.png')
files=[A/'painting-source.png',A/'projection.png',R/'assets/horseman/Horse.glb']+list(A.glob('fill-*.png'))
lock={'source_alpha_bbox':sb,'token_alpha_bbox':b,'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(M/'inputs.json').write_text(json.dumps(lock,indent=2)+'\n')
Path(__file__).with_name('assets.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
print(lock)

"""Register the archived source to the exact shipped token, record external inputs."""
from pathlib import Path
from PIL import Image
import hashlib,json,os,shutil
R=Path(os.environ['ANIM_ROOT']);A=R/'assets/cuirassier';M=R/'masters/cuirassier'
src=Image.open(A/'painting-source.png').convert('RGBA');token=Image.open('app/src/assets/units/cuirassier-256.png').convert('RGBA')
b=src.getchannel('A').point(lambda x:255 if x>128 else 0).getbbox();t=token.getchannel('A').point(lambda x:255 if x>128 else 0).getbbox()
canvas=Image.new('RGBA',(1024,1024));canvas.alpha_composite(src.crop(b).resize(((t[2]-t[0])*4,(t[3]-t[1])*4),Image.Resampling.LANCZOS),(t[0]*4,t[1]*4));canvas.save(A/'painting-aligned.png')
for kind in ['hair','bronze','linen']:shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'fill-{kind}.png')
files=[A/'painting-source.png',A/'painting-aligned.png',R/'assets/horseman/Horse.glb']+list(A.glob('fill-*.png'))


for kind in ['coat','steel']:
 image=canvas.copy();pixels=image.load()
 for y in range(image.height):
  for x in range(image.width):
   r,g,b,a=pixels[x,y];hi=max(r,g,b);lo=min(r,g,b)
   valid=(hi-lo<max(20,hi*.32)) and (kind=='steel' or (hi<165 and y>300))
   pixels[x,y]=(r,g,b,a if valid else 0)
 image.save(A/f'projection-{kind}.png')

files+=list(A.glob("projection-*.png"))
(M/'inputs.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))

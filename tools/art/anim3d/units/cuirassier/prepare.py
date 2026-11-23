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


# Only cream pigment belongs on the stone. Exclude standing hooves and their
# contact shadows so they cannot remain painted on the disc during movement.
stone=canvas.copy();pixels=stone.load()
for y in range(stone.height):
 for x in range(stone.width):
  r,g,b,a=pixels[x,y]
  pixels[x,y]=(r,g,b,a if y>196*4 and r>190 and g>155 and b>100 else 0)
stone.save(A/'projection-stone.png');files.append(A/'projection-stone.png')
(M/'inputs.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))

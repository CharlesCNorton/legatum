"""Prepare external painting maps; never create masters in the repository."""
import os
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/arquebusier'; A.mkdir(parents=True,exist_ok=True)
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/arquebusier-256.png').convert('RGBA')
# Register the full-resolution painting to the alpha bounds of the shipped token.
b=ref.getchannel('A').getbbox(); sb=source.getchannel('A').getbbox()
canvas=Image.new('RGBA',(1024,1024)); target=tuple(v*4 for v in b)
canvas.paste(source.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2])
canvas.save(A/'projection.png')
fill=A/'painted-fills.png'
if fill.exists():
 im=Image.open(fill).convert('RGB');w,h=im.size
 for name,box in [('red',(0,0,w//2,h//2)),('linen',(w//2,0,w,h//2)),('leather',(0,h//2,w//2,h)),('skin',(w//2,h//2,w,h))]:
  im.crop(box).resize((512,512),Image.Resampling.LANCZOS).save(A/(name+'-fill.png'))
print('Painting registered',sb,'to',b)

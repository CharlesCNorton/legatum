import os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/keshig';Q=R/'review/3d-v2'
s=Image.new('RGBA',(8*192,2*220),(233,207,160,255));d=ImageDraw.Draw(s)
for row,view in enumerate(['top','front']):
 for i in range(8):
  im=Image.open(M/f'feet/{view}/{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.LANCZOS);s.alpha_composite(im,(i*192,row*220+24));d.text((i*192+6,row*220+6),f'{view} {i+1} / forward -Y',fill=(55,42,25))
s.save(Q/'keshig-g-feet-check.png')

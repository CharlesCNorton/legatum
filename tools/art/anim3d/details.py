"""Compare helmet, cuirass and shield crops without stretching their proportions."""
from pathlib import Path
import os
from PIL import Image,ImageDraw,ImageOps
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/spearman-3d-v2'
source=Image.open(M/'spearman-source.png').convert('RGBA')
render=Image.open(M/'renders/detail/three-quarter.png').convert('RGBA')
assert render.size==(512,512),'Run RESOLUTION=512 render.sh detail first'
regions=[('Helmet',(540,250,750,500),(207,104,299,222)),('Cuirass',(520,495,720,750),(202,207,277,305)),('Aspis',(650,490,925,910),(253,207,356,367))]
out=Image.new('RGB',(560,900),(224,215,191));draw=ImageDraw.Draw(out)
for row,(label,a,b) in enumerate(regions):
 draw.text((12,row*300+8),label+' | painting / rendered geometry',fill=(40,34,27))
 for col,(im,box) in enumerate([(source,a),(render,b)]):
  crop=ImageOps.contain(im.crop(box),(256,256),Image.Resampling.LANCZOS)
  x=12+col*280+(256-crop.width)//2;y=row*300+32+(256-crop.height)//2
  out.paste(crop,(x,y),crop)
p=R/'review/3d-v2/c-details.png';out.save(p);print(p)

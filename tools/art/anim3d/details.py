"""Source and render close-ups in the calibrated rest-camera coordinate system."""
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageOps
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/spearman-3d-v2'
source=Image.open(M/'spearman-source.png').convert('RGBA')
render=Image.open(M/'renders/detail/three-quarter.png').convert('RGBA')
regions=[('Helmet',(115,54,153,106)),('Cuirass',(103,102,143,150)),('Aspis',(128,101,183,180))]
out=Image.new('RGB',(560,900),(224,215,191));draw=ImageDraw.Draw(out)
for row,(label,box) in enumerate(regions):
 draw.text((12,row*300+8),label+' | painting / rendered geometry',fill=(40,34,27))
 x0,y0,x1,y1=box
 painting_box=(349+(x0-75)*556/105,9+(y0-12)*1236/232,349+(x1-75)*556/105,9+(y1-12)*1236/232)
 render_box=tuple(v*render.width/256 for v in box)
 for col,(im,crop_box) in enumerate([(source,painting_box),(render,render_box)]):
  crop=ImageOps.contain(im.crop(tuple(round(v) for v in crop_box)),(256,256),Image.Resampling.LANCZOS)
  x=12+col*280+(256-crop.width)//2;y=row*300+32+(256-crop.height)//2
  out.paste(crop,(x,y),crop)
p=R/'review/3d-v2/spearman-c-details.png';out.save(p);print(p)

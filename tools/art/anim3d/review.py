"""Native-size PNG sheets and animated WebP previews of actual rendered pixels."""
from pathlib import Path
import os,sys
from PIL import Image,ImageDraw
root=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
master=root/'masters/spearman-3d-v2';review=root/'review/3d-v2'
stage=sys.argv[1];renders=master/'renders'/stage
source=Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
if stage=='b':names=['front','three-quarter','side']
elif stage=='d' or stage.startswith('e-'):names=[p.stem for p in sorted(renders.glob('*.png'))]
else:names=['three-quarter']
images=[('Painting',source)]+[(n,Image.open(renders/(n+'.png')).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)) for n in names]
sheet=Image.new('RGB',(len(images)*272,380),(224,215,191));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(images):
 x=8+i*272;d.text((x,10),name+' | 256 / 64 px',fill=(40,34,27));sheet.paste(im,(x,36),im)
 small=im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
filename={'b':'b-mpfb-kit-plain.png','c':'c-textured-lit.png','d':'d-rig-poses.png'}.get(stage,stage+'-strip.png')
sheet.save(review/filename)
if stage.startswith('e-'):
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
 frames=[im for _,im in images[1:]]
 frames[0].save(review/(stage+'.webp'),save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
print(review/filename)

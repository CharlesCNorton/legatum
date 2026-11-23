"""Native-size PNG sheets and animated WebP previews of actual rendered pixels."""
from pathlib import Path
import os,sys
from PIL import Image,ImageDraw
root=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
master=root/'masters/horseman-3d';review=root/'review/3d-v2'
stage=sys.argv[1];renders=master/'renders'/stage
source=Image.open('app/src/assets/units/horseman-256.png').convert('RGBA')
names=[p.stem for p in sorted(renders.glob('*.png'))]
images=[('Painting',source)]+[(n,Image.open(renders/(n+'.png')).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)) for n in names]
sheet=Image.new('RGB',(len(images)*272,380),(224,215,191));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(images):
 x=8+i*272;d.text((x,10),name+' | 256 / 64 px',fill=(40,34,27));sheet.paste(im,(x,36),im)
 small=im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
filename={'b':'b-plain.png','c':'c-textured-lit.png','d':'d-rig-poses.png','c-details':'c-details.png'}.get(stage,stage+'-strip.png')
sheet.save(review/('horseman-'+filename))
if stage.startswith('e-'):
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
 frames=[im for _,im in images[1:]]
 frames[0].save(review/('horseman-'+stage+'.webp'),save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
if stage=='c-details':
 # Three meaningful native-size surface comparisons, in addition to full-frame evidence.
 big=Image.open(renders/'00.png').convert('RGBA')
 ref=Image.open(root/'assets/horseman/painting-aligned-1024.png').convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
 big=big.resize((512,512),Image.Resampling.LANCZOS)
 sheet=Image.new('RGB',(960,450),(224,215,191));draw=ImageDraw.Draw(sheet)
 crops=[('Helmet / skin',(160,40,310,215),(185,65,320,215)),('Tunic / saddle',(160,135,315,330),(160,145,320,335)),('Horse / tack',(250,165,405,385),(270,175,425,395))]
 for i,(label,rc,bc) in enumerate(crops):
  draw.text((i*320+8,8),label+' | painting / 3D',fill=(40,34,27))
  for j,(im,box) in enumerate([(ref,rc),(big,bc)]):
   crop=im.crop(box);crop.thumbnail((150,360));sheet.paste(crop,(i*320+j*160+5,45),crop)
 sheet.save(review/'horseman-c-details.png')
print(review/('horseman-'+filename))

if stage=='c':
 rendered=Image.open(renders/'00.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',(256,256),(224,215,191,255));painted=Image.alpha_composite(bg,source);model=Image.alpha_composite(bg,rendered)
 cross=Image.blend(painted,model,.5);split=painted.copy();split.paste(model.crop((128,0,256,256)),(128,0))
 sheet=Image.new('RGB',(1088,380),(224,215,191));draw=ImageDraw.Draw(sheet)
 for i,(label,im) in enumerate([('Painting',painted),('3D rest',model),('Split 50/50',split),('Crossfade 50%',cross)]):
  draw.text((i*272+8,10),label,fill=(40,34,27));sheet.paste(im.convert('RGB'),(i*272+8,36))
  sheet.paste(im.convert('RGB').resize((64,64),Image.Resampling.LANCZOS),(i*272+104,302))
 sheet.save(review/'horseman-f-restpose-compare.png')

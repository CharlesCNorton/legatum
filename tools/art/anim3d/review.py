"""Native-size PNG sheets and animated WebP previews of actual rendered pixels."""
from pathlib import Path
import os,sys,json
from PIL import Image,ImageDraw,ImageChops,ImageStat
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
filename='spearman-'+{'b':'b-plain.png','c':'c-textured-lit.png','d':'d-rig-poses.png'}.get(stage,stage+'-strip.png')
sheet.save(review/filename)
if stage.startswith('e-'):
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
 frames=[im for _,im in images[1:]]
 frames[0].save(review/('spearman-'+stage+'.webp'),save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
print(review/filename)

if stage=='c':
 painting,render=images[0][1],images[1][1]
 def composite(im):
  bg=Image.new('RGBA',im.size,(224,215,191,255));return Image.alpha_composite(bg,im).convert('RGB')
 left,right=composite(painting),composite(render)
 cross=Image.blend(left,right,.5)
 split=left.copy();split.paste(right.crop((128,0,256,256)),(128,0))
 compare=Image.new('RGB',(1088,380),(224,215,191));draw=ImageDraw.Draw(compare)
 for i,(label,im) in enumerate([('Painting',left),('3D rest',right),('50/50 crossfade',cross),('Split: painting | 3D',split)]):
  x=8+i*272;draw.text((x,10),label,fill=(40,34,27));compare.paste(im,(x,36));compare.paste(im.resize((64,64),Image.Resampling.LANCZOS),(x+96,302))
 compare.save(review/'spearman-f-restpose-compare.png')

if stage=='c':
 a=painting.getchannel('A').point(lambda v:255 if v>32 else 0)
 b=render.getchannel('A').point(lambda v:255 if v>32 else 0)
 intersection=ImageChops.multiply(a,b);union=ImageChops.lighter(a,b)
 area=lambda im:sum(im.histogram()[1:])
 metrics={'silhouette_iou':round(area(intersection)/area(union),4),'painting_bounds':a.getbbox(),'render_bounds':b.getbbox(),'mean_absolute_rgb_error_on_union':[round(v,2) for v in ImageStat.Stat(ImageChops.difference(left,right),mask=union).mean], 'meaning':'Diagnostics only; not an art approval or perceptual identity score'}
 (review/'spearman-look-metrics.json').write_text(json.dumps(metrics,indent=2))

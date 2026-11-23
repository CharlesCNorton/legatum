"""Publish review evidence immediately, preserving the first plain stage."""
from pathlib import Path
import os,sys,json
from PIL import Image,ImageDraw
root=Path(os.environ['ANIM_ROOT']);m=root/'masters/field-cannon';r=root/'review/3d-v2';stage=sys.argv[1];folder=m/'renders'/stage
files=sorted(folder.glob('*.png'));source=Image.open('app/src/assets/units/field-cannon-256.png').convert('RGBA')
if stage!='b':
 from grade import apply
 apply(folder,source)
gallery=m/'gallery256'/stage;gallery.mkdir(parents=True,exist_ok=True)
for path in files:Image.open(path).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS).save(gallery/path.name)
images=[('Painting',source)]+[(p.stem,Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)) for p in files]
sheet=Image.new('RGB',(272*len(images),380),(224,215,191));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(images):
 x=8+i*272;d.text((x,10),name+' | 256 / 64 px',fill=(40,34,27));sheet.paste(im,(x,36),im);small=im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
name={'b':'b-plain','c':'c-textured-lit','detail':'c-details','d':'d-rig-poses'}.get(stage,stage+'-strip');dest=r/f'field-cannon-{name}.png';sheet.save(dest)
if stage=='c':
 render=images[-1][1];cross=Image.blend(source,render,.5);comparison=Image.new('RGB',(816,380),(224,215,191));draw=ImageDraw.Draw(comparison)
 for j,(label,im) in enumerate([('Painting',source),('Rendered 3D',render),('50/50 crossfade',cross)]):
  x=8+j*272;draw.text((x,10),label,fill=(40,34,27));comparison.paste(im,(x,36),im);small=im.resize((64,64),Image.Resampling.LANCZOS);comparison.paste(small,(x+96,302),small)
 comparison.save(r/'field-cannon-f-restpose-compare.png')
 from grade import stats
 from PIL import ImageChops
 sa=source.getchannel('A').point(lambda a:255 if a>128 else 0);ra=render.getchannel('A').point(lambda a:255 if a>128 else 0)
 intersection=ImageChops.multiply(sa,ra).histogram()[255];union=ImageChops.lighter(sa,ra).histogram()[255]
 (r/'field-cannon-look-metrics.json').write_text(json.dumps({'painting':stats(source),'render':stats(render),'silhouette_iou':intersection/max(1,union),'painting_bounds':sa.getbbox(),'render_bounds':ra.getbbox(),'note':'Measured residuals, not an art approval or exact-viewpoint claim'},indent=2)+'\n')
if stage=='detail':
 detail=Image.new('RGB',(1024,540),(224,215,191))
 details=ImageDraw.Draw(detail);provenance=json.loads((folder/'render.json').read_text())
 details.text((8,8),'Painting | original source at 512 px',fill=(40,34,27))
 details.text((520,8),f"{provenance['engine']} {provenance['device']} | {provenance['resolution']} px render shown at 512",fill=(40,34,27))
 # Compare against the full painting at 512, not an enlarged 256px thumbnail.
 original=Image.open(root/'assets/field-cannon/painting-source.png').convert('RGBA');box=source.getchannel('A').getbbox()
 reference=Image.new('RGBA',(512,512));crop=original.crop(original.getchannel('A').getbbox()).resize(((box[2]-box[0])*2,(box[3]-box[1])*2),Image.Resampling.LANCZOS)
 reference.paste(crop,(box[0]*2,box[1]*2))
 for i,im in enumerate([reference,Image.open(files[0]).convert('RGBA')]):
  im=im.resize((512,512),Image.Resampling.LANCZOS);detail.paste(im,(i*512,28),im)
 detail.save(dest)
if stage.startswith('e-'):
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]];frames=[im for _,im in images[1:]]
 frames[0].save(r/f'field-cannon-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
with (r/'field-cannon-log.md').open('a') as f:f.write(f'- Posted {dest.name}; actual {os.environ.get("RENDER_ENGINE","CYCLES")} render, visual review pending.\n')
print(dest)

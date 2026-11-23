"""Immediate native-size stage evidence and animation previews, inherited sheet layout."""
import os,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot'))); M=R/'masters/panzer'; review=R/'review/3d-v2'
stage=sys.argv[1]; folder=M/'renders'/stage
names=['three-quarter','front','side'] if stage=='b' else [p.stem for p in sorted(folder.glob('*.png'))]
source=Image.open('app/src/assets/units/panzer-256.png').convert('RGBA')
images=[('Painting',source)]+[(n,Image.open(folder/f'{n}.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)) for n in names]
if stage=='details':
    crop=source.crop((45,45,175,140)).resize((256,256),Image.Resampling.LANCZOS)
    images[-1]=(images[-1][0], images[-1][1].crop((45,45,175,140)).resize((256,256),Image.Resampling.LANCZOS))
    images.insert(1,('Painting detail',crop))
sheet=Image.new('RGB',(len(images)*272,380),(224,215,191));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(images):
    x=8+i*272;d.text((x,10),name+' | 256 / 64 px',fill=(40,34,27));sheet.paste(im,(x,36),im)
    small=Image.open('app/src/assets/units/panzer-64.png').convert('RGBA') if name=='Painting' else im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
suffix={'b':'b-plain','c':'c-textured-lit','details':'c-details','d':'d-rig-poses','g':'g-feet-check'}.get(stage,stage+'-strip')
sheet.save(review/f'panzer-{suffix}.png')
if stage.startswith('e-'):
    frames=[im for _,im in images[1:]];fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
    frames[0].save(review/f'panzer-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
with (review/'panzer-log.md').open('a') as f:f.write(f'- Emitted panzer-{suffix}.png from actual {stage} renders; visual review pending.\n')
print(review/f'panzer-{suffix}.png')

if stage=='c':
    render=images[-1][1]
    panels=[('Painting',source),('3D render',render),('50/50 crossfade',Image.blend(source,render,.5))]
    compare=Image.new('RGB',(816,380),(224,215,191));draw=ImageDraw.Draw(compare)
    for i,(label,im) in enumerate(panels):
        draw.text((8+i*272,10),label,fill=(40,34,27));compare.paste(im,(8+i*272,36),im)
        small=Image.open('app/src/assets/units/panzer-64.png').convert('RGBA') if label=='Painting' else im.resize((64,64),Image.Resampling.LANCZOS);compare.paste(small,(104+i*272,302),small)
    compare.save(review/'panzer-f-restpose-compare.png')

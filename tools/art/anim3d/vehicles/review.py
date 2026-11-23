"""Immediate native-size stage evidence and animation previews, inherited sheet layout."""
import os,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot'))); M=R/'masters/tank'; review=R/'review/3d-v2'
stage=sys.argv[1]; folder=M/'renders'/stage
if stage=='g':
    sheet=Image.new('RGB',(8*256,2*284),(224,215,191));draw=ImageDraw.Draw(sheet)
    for row,view in enumerate(('top','front')):
        for i in range(8):
            im=Image.open(folder/f'{view}-{i:02}.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
            draw.text((i*256+8,row*284+8),f'{view} / move {i} / geometry',fill=(40,34,27))
            sheet.paste(im,(i*256,row*284+28),im)
    sheet.save(review/'tank-g-feet-check.png')
    with (review/'tank-log.md').open('a') as f:f.write('- Emitted tank-g-feet-check.png: actual top/front geometry renders of all eight move samples.\n')
    raise SystemExit(0)
names=['three-quarter','front','side'] if stage=='b' else [p.stem for p in sorted(folder.glob('*.png'))]
source=Image.open('app/src/assets/units/tank-256.png').convert('RGBA')
images=[('Painting',source)]+[(n,Image.open(folder/f'{n}.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)) for n in names]
if stage=='details':
    # Same camera-plane translation and magnification as render.py's detail view.
    # An arbitrary panel crop compared different parts at different scales.
    field=4.95;size=1024;half=2.8/field*size/2
    cx=size/2+.12/field*size;cy=size/2-.48/field*size
    crop=Image.open(M/'textures/painting-projection.png').convert('RGBA').crop(
        tuple(round(v) for v in (cx-half,cy-half,cx+half,cy+half))
    ).resize((256,256),Image.Resampling.LANCZOS)
    images.insert(1,('Painting detail',crop))
sheet=Image.new('RGB',(len(images)*272,380),(224,215,191));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(images):
    x=8+i*272;d.text((x,10),name+' | 256 / 64 px',fill=(40,34,27));sheet.paste(im,(x,36),im)
    small=Image.open('app/src/assets/units/tank-64.png').convert('RGBA') if name=='Painting' else im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
suffix={'b':'b-plain','c':'c-textured-lit','details':'c-details','d':'d-rig-poses'}.get(stage,stage+'-strip')
sheet.save(review/f'tank-{suffix}.png')
if stage.startswith('e-'):
    frames=[im for _,im in images[1:]];fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]]
    frames[0].save(review/f'tank-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
with (review/'tank-log.md').open('a') as f:f.write(f'- Emitted tank-{suffix}.png from actual {stage} renders; visual review pending.\n')
print(review/f'tank-{suffix}.png')

if stage=='c':
    render=images[-1][1]
    panels=[('Painting',source),('3D render',render),('50/50 crossfade',Image.blend(source,render,.5))]
    compare=Image.new('RGB',(816,380),(224,215,191));draw=ImageDraw.Draw(compare)
    for i,(label,im) in enumerate(panels):
        draw.text((8+i*272,10),label,fill=(40,34,27));compare.paste(im,(8+i*272,36),im)
        small=Image.open('app/src/assets/units/tank-64.png').convert('RGBA') if label=='Painting' else im.resize((64,64),Image.Resampling.LANCZOS);compare.paste(small,(104+i*272,302),small)
    compare.save(review/'tank-f-restpose-compare.png')

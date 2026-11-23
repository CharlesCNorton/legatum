"""Register the archived alpha painting to the shipped token field."""
from pathlib import Path
from PIL import Image, ImageDraw
import os,json,hashlib
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/bomber'; M=R/'masters/bomber'; M.mkdir(parents=True,exist_ok=True)
im=Image.open(A/'bomber-source.png').convert('RGBA'); box=im.getchannel('A').getbbox()
fig=im.crop(box); k=928/max(fig.size); size=tuple(round(v*k) for v in fig.size); offset=((1024-size[0])//2,(1024-size[1])//2)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig.resize(size,Image.Resampling.LANCZOS),offset);out.save(A/'projection.png')
hidden=Image.open(A/'occlusion-fill-source.png').convert('RGBA').resize(im.size,Image.Resampling.LANCZOS)
filled=Image.new('RGBA',(1024,1024));filled.alpha_composite(hidden.crop(box).resize(size,Image.Resampling.LANCZOS),offset);filled.save(A/'occlusion-fill.png')

# Source-object exclusion: rotating blades must not remain painted on the body.
mask=Image.new('L',(1024,1024),255);draw=ImageDraw.Draw(mask)
blades=[[(777,615),(811,462),(825,445),(836,452),(817,570),(800,623)],
        [(775,637),(746,652),(650,730),(662,744),(734,704),(790,650)],
        [(792,634),(823,649),(877,718),(883,736),(870,739),(810,682),(780,646)],
        [(1145,407),(1165,260),(1173,248),(1181,260),(1166,414)],
        [(1150,426),(1110,458),(1070,494),(1085,508),(1158,438)],
        [(1160,424),(1198,444),(1243,470),(1246,484),(1236,489),(1182,459)]]
for poly in blades:
    draw.polygon([((x-box[0])*k+offset[0],(y-box[1])*k+offset[1]) for x,y in poly],fill=0)
mask.save(A/'projection-mask.png')
# Separate material coverage, not a cutout: exclude the raised support and its
# baked shadow from stone pigment. Actual scene AO supplies moving contact.
stone_mask=Image.new('L',(1024,1024),0);draw=ImageDraw.Draw(stone_mask)
for poly in [[(400,940),(510,940),(510,987),(770,987),(770,940),(880,940),(880,1100),(400,1100)]]:
    draw.polygon([((x-box[0])*k+offset[0],(y-box[1])*k+offset[1]) for x,y in poly],fill=255)
stone_mask.save(A/'stone-mask.png')
(M/'registration.json').write_text(json.dumps({'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}},indent=2))

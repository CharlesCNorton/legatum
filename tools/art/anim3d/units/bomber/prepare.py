"""Register the archived alpha painting to the shipped token field."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
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
# Register generated stone to the painted disc, not to the generator's canvas.
# Only color is used on the closed base; the original rim remains authoritative.
stone_spec=json.loads(Path(__file__).with_name('stone-fill.json').read_text())
assert hashlib.sha256((A/'stone-fill-source.png').read_bytes()).hexdigest()==stone_spec['source_sha256'], 'stone source changed'
clean=Image.open(A/'stone-fill-source.png').convert('RGBA')
clean_box=clean.getchannel('A').point(lambda x:255 if x>200 else 0).getbbox()
x0,y0,x1,y1=stone_spec['target_bounds']
clean=clean.crop(clean_box).resize((x1-x0,y1-y0),Image.Resampling.LANCZOS)
plate=Image.new('RGBA',(1024,1024));plate.alpha_composite(clean,(x0,y0))
keep=Image.new('L',(1024,1024));draw=ImageDraw.Draw(keep)
draw.rectangle((0,stone_spec['original_rim_below_y'],1024,1024),fill=255)
keep=keep.filter(ImageFilter.GaussianBlur(2))
plate=Image.composite(out,plate,keep)
plate.save(A/'stone-fill.png')
(M/'registration.json').write_text(json.dumps({'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}},indent=2))

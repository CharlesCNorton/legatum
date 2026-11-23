"""Register the full painting and recolor existing generated unseen-surface fills."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/rifleman';A.mkdir(parents=True,exist_ok=True)
lock=json.loads((Path(__file__).parent/'assets.lock.json').read_text())
for path,expected in lock.items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==expected,path
source=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/rifleman-256.png').convert('RGBA')
b=ref.getchannel('A').getbbox();sb=source.getchannel('A').getbbox();canvas=Image.new('RGBA',(1024,1024));target=tuple(v*4 for v in b)
canvas.paste(source.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2]);canvas.save(A/'projection.png')
for name,source_name,dark,light in [('wool','fill-linen.png','#182338','#51647f'),('linen','fill-linen.png','#354650','#8c9da5'),('leather','fill-coat.png','#201b17','#75664e')]:
 ImageOps.colorize(ImageOps.grayscale(Image.open(R/'assets/horseman'/source_name)),dark,light).save(A/(name+'-fill.png'))
print('Registered full source',sb,'to token bounds',b)

# Register the clean generated disc in exactly the original source canvas.
clean=Image.open(A/'stone-fill-source.png').convert('RGBA').resize(source.size,Image.Resampling.LANCZOS)
plate=Image.new('RGBA',(1024,1024));plate.paste(clean.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2]);plate.save(A/'stone-projection.png')

clean=Image.open(A/'cloth-fill-source.png').convert('RGBA').resize(source.size,Image.Resampling.LANCZOS)
plate=Image.new('RGBA',(1024,1024));plate.paste(clean.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2])
mask=Image.new('L',(1024,1024));draw=ImageDraw.Draw(mask)
draw.line([(84*4,137*4),(205*4,14*4)],fill=255,width=13*4)
for box in [(99,93,122,113),(132,70,154,94)]:draw.ellipse(tuple(v*4 for v in box),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(3))
Image.composite(plate,canvas,mask).save(A/'cloth-projection.png')

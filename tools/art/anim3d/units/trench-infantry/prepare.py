"""Prepare external painting maps; never create masters in the repository."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/trench-infantry'; A.mkdir(parents=True,exist_ok=True)
for relative,expected in json.loads((Path(__file__).parent/'assets.lock.json').read_text()).items():
 assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==expected, 'Changed input: '+relative
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/trench-infantry-256.png').convert('RGBA')
# Register the full-resolution painting to the alpha bounds of the shipped token.
b=ref.getchannel('A').getbbox(); sb=source.getchannel('A').getbbox()
canvas=Image.new('RGBA',(1024,1024)); target=tuple(v*4 for v in b)
canvas.paste(source.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2])
canvas.save(A/'projection.png')
from PIL import ImageOps
src=R/'assets/horseman'
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-linen.png')), '#333c45','#9ca4aa').save(A/'wool-fill.png')
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-linen.png')), '#55432c','#ae9169').save(A/'linen-fill.png')
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-coat.png')), '#341c0d','#a97642').save(A/'leather-fill.png')
print('Painting registered',sb,'to',b)

# Generated occlusion plate is a texture source only. Register the disc separately
# so generation cannot change the actual disc silhouette or camera alignment.
clean=Image.open(A/'occlusion-fill-source.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
# An unobstructed coat swatch carries the same brushwork onto side/back folds.
clean.crop((510,470,620,650)).convert('RGB').resize((384,512),Image.Resampling.LANCZOS).save(A/'wool-fill.png')
mask=clean.getchannel('A').point(lambda a:255 if a>220 else 0)
mask.paste(0,(0,0,1024,830));bounds=mask.getbbox()
stone=Image.new('RGBA',(1024,1024))
stone.paste(clean.crop(bounds).resize((472,120),Image.Resampling.LANCZOS),(272,852))
# Retain the original authored rim; moving boots and rifle are absent from top.
rim=Image.new('L',(1024,1024));ImageDraw.Draw(rim).rectangle((0,944,1024,1024),fill=255)
rim= rim.filter(ImageFilter.GaussianBlur(3))
Image.composite(canvas,stone,rim).save(A/'stone-projection.png')
clothmask=Image.new('L',(1024,1024));d=ImageDraw.Draw(clothmask)
for box in [(83,80,103,106),(135,64,155,85)]:d.ellipse(tuple(v*4 for v in box),fill=255)
d.line([(94*4,57*4),(92*4,174*4)],fill=255,width=8*4)
clothmask=clothmask.filter(ImageFilter.GaussianBlur(4))
Image.composite(clean,canvas,clothmask).save(A/'cloth-projection.png')

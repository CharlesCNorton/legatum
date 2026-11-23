"""Prepare external painting maps; never create masters in the repository."""
import os,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/infantry'; A.mkdir(parents=True,exist_ok=True)
for relative,expected in json.loads((Path(__file__).parent/'assets.lock.json').read_text()).items():
 assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==expected, 'Changed input: '+relative
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/infantry-256.png').convert('RGBA')
# Register the full-resolution painting to the alpha bounds of the shipped token.
b=ref.getchannel('A').getbbox(); sb=source.getchannel('A').getbbox()
canvas=Image.new('RGBA',(1024,1024)); target=tuple(v*4 for v in b)
canvas.paste(source.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2])
canvas.save(A/'projection.png')
from PIL import ImageOps
src=R/'assets/horseman'
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-linen.png')), '#343923','#969365').save(A/'wool-fill.png')
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-linen.png')), '#635631','#c1ad72').save(A/'linen-fill.png')
ImageOps.colorize(ImageOps.grayscale(Image.open(src/'fill-coat.png')), '#341c0d','#a97642').save(A/'leather-fill.png')
print('Painting registered',sb,'to',b)

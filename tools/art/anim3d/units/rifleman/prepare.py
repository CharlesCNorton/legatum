"""Register the full painting and recolor existing generated unseen-surface fills."""
import os,json,hashlib
from pathlib import Path
from PIL import Image,ImageOps
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/rifleman';A.mkdir(parents=True,exist_ok=True)
source=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/rifleman-256.png').convert('RGBA')
b=ref.getchannel('A').getbbox();sb=source.getchannel('A').getbbox();canvas=Image.new('RGBA',(1024,1024));target=tuple(v*4 for v in b)
canvas.paste(source.crop(sb).resize((target[2]-target[0],target[3]-target[1]),Image.Resampling.LANCZOS),target[:2]);canvas.save(A/'projection.png')
for name,source_name,dark,light in [('wool','fill-linen.png','#182338','#51647f'),('linen','fill-linen.png','#354650','#8c9da5'),('leather','fill-coat.png','#201b17','#75664e')]:
 ImageOps.colorize(ImageOps.grayscale(Image.open(R/'assets/horseman'/source_name)),dark,light).save(A/(name+'-fill.png'))
lock=json.loads((Path(__file__).parent/'assets.lock.json').read_text())
for path,expected in lock.items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==expected,path
print('Registered full source',sb,'to token bounds',b)

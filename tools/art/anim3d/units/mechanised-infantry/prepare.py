"""Register the archived full master to the shipped painting's alpha bounds."""
from pathlib import Path
import os, json, hashlib
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/mechanised-infantry'; M=ROOT/'masters/mechanised-infantry'; M.mkdir(parents=True,exist_ok=True)
lock=json.loads((Path(__file__).parent/'assets.lock.json').read_text())
for name,value in lock.items():
 assert hashlib.sha256((A/name).read_bytes()).hexdigest()==value,'Changed asset: '+name
source=Image.open(A/'painting-source.png').convert('RGBA')
# Source archive may carry the original magenta key background.
pixels=list(source.getdata())
source.putdata([(r,g,b,0 if r>130 and b>100 and g<.65*min(r,b) else a) for r,g,b,a in pixels])
target=Image.open('app/src/assets/units/mechanised-infantry-256.png').convert('RGBA')
b=target.getchannel('A').getbbox(); crop=source.crop(source.getchannel('A').getbbox())
canvas=Image.new('RGBA',(1024,1024)); canvas.alpha_composite(crop.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS),(b[0]*4,b[1]*4));canvas.save(A/'projection.png')
# Prevent the soldier from being painted a second time onto the cabin/ramp.
from PIL import ImageDraw
mechanical=canvas.copy();mask=mechanical.getchannel('A')
draw=ImageDraw.Draw(mask)
draw.polygon([(x*4,y*4) for x,y in [(179,104),(190,102),(195,112),(200,123),(199,136),(193,146),(195,161),(192,180),(183,181),(181,164),(176,157),(173,144),(173,136),(165,130),(169,117)]],fill=0)
mechanical.putalpha(mask);mechanical.save(A/'machine-projection.png')
(M/'inputs.json').write_text(json.dumps({'source_sha256':hashlib.sha256((A/'painting-source.png').read_bytes()).hexdigest(),'painting_bounds_256':b,'projection':'full master fitted to shipped alpha bbox; no mesh replacement','fill_sha256':hashlib.sha256((A/'painted-olive.png').read_bytes()).hexdigest()},indent=2))
print('Painting bounds',b)

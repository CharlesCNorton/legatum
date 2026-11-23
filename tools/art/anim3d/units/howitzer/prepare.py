"""Register the archived full master to the shipped painting's alpha bounds."""
from pathlib import Path
import os, json, hashlib
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/howitzer'; M=ROOT/'masters/howitzer'; M.mkdir(parents=True,exist_ok=True)
source=Image.open(A/'painting-source.png').convert('RGBA')
# Source archive may carry the original magenta key background.
pixels=list(source.getdata())
source.putdata([(r,g,b,0 if r>130 and b>100 and g<.65*min(r,b) else a) for r,g,b,a in pixels])
target=Image.open('app/src/assets/units/howitzer-256.png').convert('RGBA')
b=target.getchannel('A').getbbox(); crop=source.crop(source.getchannel('A').getbbox())
canvas=Image.new('RGBA',(1024,1024)); canvas.alpha_composite(crop.resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS),(b[0]*4,b[1]*4));canvas.save(A/'projection.png')
# Object-specific source exclusion: cream stone must not become paint on trails/axle.
mechanical=canvas.copy()
mechanical.putdata([(r,g,b,0 if r>165 and g>140 and b>90 and r>g*1.05 else a) for r,g,b,a in canvas.getdata()])
mechanical.save(A/'machine-projection.png')
(M/'inputs.json').write_text(json.dumps({'source_sha256':hashlib.sha256((A/'painting-source.png').read_bytes()).hexdigest(),'painting_bounds_256':b,'projection':'full master fitted to shipped alpha bbox; no mesh replacement','fill_sha256':hashlib.sha256((A/'painted-olive.png').read_bytes()).hexdigest()},indent=2))
print('Painting bounds',b)

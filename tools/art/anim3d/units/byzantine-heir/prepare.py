"""Align the licensed source to the committed token; retain external assets."""
from pathlib import Path
from PIL import Image
import json, hashlib, os
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=R/'assets/byzantine-heir'; M=R/'masters/byzantine-heir'; M.mkdir(parents=True,exist_ok=True)
src=Image.open(A/'source.png').convert('RGBA'); token=Image.open('app/src/assets/units/byzantine-heir-256.png').convert('RGBA')
b=token.getbbox(); sb=src.getbbox(); out=Image.new('RGBA',(1024,1024));out.alpha_composite(src.crop(sb).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS),(b[0]*4,b[1]*4));out.save(A/'painting-aligned.png')
(M/'source.json').write_text(json.dumps({'source_sha256':hashlib.sha256((A/'source.png').read_bytes()).hexdigest(),'token_bbox':b,'source_bbox':sb,'projection_canvas':1024,'license':'CC BY 4.0'},indent=2))
print('Prepared aligned painting',b)

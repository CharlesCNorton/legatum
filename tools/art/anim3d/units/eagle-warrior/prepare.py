"""Register full source into token canvas; retain originals and pin input hashes."""
import os,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/eagle-warrior';M=R/'masters/eagle-warrior';M.mkdir(parents=True,exist_ok=True)
s=Image.open(A/'painting-source.png').convert('RGBA');t=Image.open('app/src/assets/units/eagle-warrior-256.png').convert('RGBA')
sb=s.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox();tb=t.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox()
out=Image.new('RGBA',(1280,1280));out.paste(s.crop(sb).resize(((tb[2]-tb[0])*5,(tb[3]-tb[1])*5),Image.Resampling.LANCZOS),(tb[0]*5,tb[1]*5));out.save(A/'projection.png')
record={'source_bbox':sb,'token_bbox':tb,'method':'alpha bbox affine registration to original token; full source RGB retained','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}}
(M/'inputs.json').write_text(json.dumps(record,indent=2));Path('tools/art/anim3d/units/eagle-warrior/assets.lock.json').write_text(json.dumps(record,indent=2)+'\n');print(record)

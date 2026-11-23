"""Register the original source to the shipped token and copy licensed painted fills."""
import os,json,hashlib,shutil,subprocess
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/musketman';A.mkdir(exist_ok=True)
if not (A/'painting-source.png').exists():
 subprocess.run(['curl','-fL','--retry','2','https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/musketman-source.png','-o',str(A/'painting-source.png')],check=True)
src=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/musketman-256.png').convert('RGBA')
b=ref.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();sb=src.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();box=tuple(v*4 for v in b)
im=Image.new('RGBA',(1024,1024));im.paste(src.crop(sb).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),box[:2]);im.save(A/'projection.png')
for kind in ('linen','coat','hair','bronze'):
 if not (A/f'{kind}-fill.png').exists():shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'{kind}-fill.png')
# Recolour original generated cloth/hide artwork for unseen surfaces.
from PIL import ImageOps
for name,source,dark,light in [('buff','linen',(70,40,17),(205,165,91)),('red','coat',(43,7,3),(176,51,25)),('leather','coat',(26,13,5),(116,70,29))]:
 im=Image.open(A/f'{source}-fill.png').convert('L')
 ImageOps.colorize(im,dark,light).save(A/f'{name}-fill.png')
(A/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
print('Prepared source',src.size,sb,'registered to',b)

# Open motion is shared externally; reject changed source bytes before rebuilding.
lock=json.loads((Path(__file__).parent/"motion.lock.json").read_text())
for name,digest in lock.items():
 path=R/"assets/quaternius-ual"/name
 assert path.exists(),f"Missing licensed Quaternius source: {path}"
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,f"Changed motion source: {path}"

# Reproducibility is checked after deriving deterministic registration/fills.
lock_path=Path(__file__).parent/"assets.lock.json"
if lock_path.exists():
 for name,digest in json.loads(lock_path.read_text()).items():
  path=Path("app/src/assets/units/musketman-256.png") if name=="token-256.png" else A/name
  assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,f"Changed painting/fill: {name}"

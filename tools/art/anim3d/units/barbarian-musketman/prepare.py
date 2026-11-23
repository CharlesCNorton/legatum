"""Register the original source to the shipped token and copy licensed painted fills."""
import os,json,hashlib,shutil,urllib.request
from pathlib import Path
from PIL import Image, ImageFilter
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/barbarian-musketman';A.mkdir(exist_ok=True)
if not (A/'painting-source.png').exists():
 urllib.request.urlretrieve('https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-musketman-source.png',A/'painting-source.png')
lock=json.loads((Path(__file__).parent/'assets.lock.json').read_text())
for name,digest in lock.items():
 assert hashlib.sha256((A/name).read_bytes()).hexdigest()==digest,f'Changed source: {name}'
src=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/barbarian-musketman-256.png').convert('RGBA')
b=ref.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();sb=src.getchannel('A').point(lambda a:255 if a>96 else 0).getbbox();box=tuple(v*4 for v in b)
im=Image.new('RGBA',(1024,1024));im.paste(src.crop(sb).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),box[:2]);im.save(A/'projection.png')
for kind in ('linen','coat','hair','bronze'):
 if not (A/f'{kind}-fill.png').exists():shutil.copyfile(R/f'assets/horseman/fill-{kind}.png',A/f'{kind}-fill.png')
# Register the generated clean stone by its occupied silhouette; retain original rim.
plate=Image.open(A/'stone-fill-source.png').convert('RGBA')
pb=plate.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
stone=Image.new('RGBA',(1024,1024))
stone.paste(plate.crop(pb).resize((596,176),Image.Resampling.LANCZOS),(56,760))
# Original lower rim is unoccluded; generated top contains no boots or shadows.
mask=Image.new('L',(1024,1024));mask.paste(255,(0,878,1024,1024));mask=mask.filter(ImageFilter.GaussianBlur(3))
stone=Image.composite(im,stone,mask)
# Extend RGB outside the plate, without using image alpha to erase 3D geometry.
# Nearest valid pixel along each scanline, then nearest occupied scanline.
pixels=stone.load(); alpha=stone.getchannel('A'); rows=[]
for y in range(1024):
 bounds=alpha.crop((0,y,1024,y+1)).point(lambda v:255 if v>128 else 0).getbbox()
 if not bounds:continue
 lo,hi=bounds[0],bounds[2]-1;rows.append(y)
 for x in range(1024):
  if pixels[x,y][3]<129:pixels[x,y]=pixels[max(lo,min(hi,x)),y][:3]+(255,)
for y in range(1024):
 if y not in rows:
  nearest=min(rows,key=lambda yy:abs(yy-y))
  stone.paste(stone.crop((0,nearest,1024,nearest+1)),(0,y))
stone.convert('RGB').save(A/'stone-projection.png')
# Isolate generated material quadrants for the newly exposed clothing/skin.
fills=Image.open(A/'painted-fills-source.png').convert('RGB');w,h=fills.size
for kind,box in {'buff':(0,0,w//2,h//2),'ivory':(w//2,0,w,h//2),'flesh':(0,h//2,w//2,h),'charcoal':(w//2,h//2,w,h)}.items():
 fills.crop(box).save(A/f'{kind}-fill.png')
(A/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
print('Prepared source',src.size,sb,'registered to',b)

# Open motion is shared externally; reject changed source bytes before rebuilding.
lock=json.loads((Path(__file__).parent/"motion.lock.json").read_text())
for name,digest in lock.items():
 path=R/"assets/quaternius-ual"/name
 assert path.exists(),f"Missing licensed Quaternius source: {path}"
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,f"Changed motion source: {path}"

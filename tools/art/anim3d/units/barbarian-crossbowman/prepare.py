"""Prepare external CC BY painting and generated fill; never put masters in git."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/barbarian-crossbowman';A.mkdir(parents=True,exist_ok=True);HERE=Path(__file__).parent
source=A/'source.png';url='https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-crossbowman-source.png'
if not source.exists():subprocess.run(['curl','-fL','--retry','2',url,'-o',str(source)],check=True)
fill=A/'fill-linen.png'
if not fill.exists():shutil.copy2(R/'assets/horseman/fill-linen.png',fill)
lock=json.loads((HERE/'inputs.json').read_text())
for name in lock:
    assert hashlib.sha256((A/name).read_bytes()).hexdigest()==lock[name]['sha256'],'Source changed: '+name
s=Image.open(source).convert('RGBA');pix=s.load()
for y in range(s.height):
    for x in range(s.width):
        r,g,b,a=pix[x,y]
        if r>g*1.35 and b>g*1.30 and r>90 and b>70:pix[x,y]=(r,g,b,0)
t=Image.open('app/src/assets/units/barbarian-crossbowman-256.png').convert('RGBA');bb=t.getbbox();crop=s.crop(s.getbbox());out=Image.new('RGBA',(1024,1024));out.alpha_composite(crop.resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.LANCZOS),(bb[0]*4,bb[1]*4));out.save(A/'painting-aligned.png')
# Register the generated clean stone plate by its own alpha bounds, retaining
# original rim pigment. This is only color on a closed 3D disc.
g=Image.open(A/'stone-fill-source.png').convert('RGBA');bbg=g.getchannel('A').point(lambda x:255 if x>160 else 0).getbbox()
plate=Image.new('RGBA',(1024,1024));plate.alpha_composite(g.crop(bbg).resize((476,172),Image.Resampling.LANCZOS),(286,802))
plate.save(A/'stone-plate.png')
print('PREPARED',A)

"""Align the archived master to the shipped token and verify all colour inputs."""
from pathlib import Path
import os,json,hashlib,shutil,urllib.request
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/phalangite';A.mkdir(parents=True,exist_ok=True)
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for name,record in lock.items():
    path=A/name
    if not path.exists():
        if record.get('url'):urllib.request.urlretrieve(record['url'],path)
        else:shutil.copyfile(R/record['reuse'],path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],'Changed source: '+name
src=Image.open(A/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/phalangite-256.png').convert('RGBA');b=ref.getchannel('A').getbbox();patch=src.crop(src.getchannel('A').getbbox()).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS);out=Image.new('RGBA',(1024,1024));out.paste(patch,(b[0]*4,b[1]*4));out.save(A/'painting-aligned.png');print('PASS: original painting and generated fills verified; painting aligned to token')

"""Publish a verified isolated CPU round without touching the shipped atlas."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.deliver import run
from kit.images import resize_rgba
root = Path(os.environ['ANIM_ROOT'])
number = int(os.environ.get('ROUND', '13'))
review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
frames, master = root/'preview', root/'masters/spearman-3d-v2'
receipt = json.loads((frames/'receipt.json').read_text())
for clip in ('rest','idle','move','attack','hit','death'):
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt[clip]['sha256'], (clip,'stale frames')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == value for p,value in receipt[clip]['look_code'].items()), 'stale look'
result = run(SimpleNamespace(slug='spearman', frames=frames, anchor=(79.375,138.125),
    out=root/'atlas', review=root/'review/3d-v2', label=f'Round {number} CPU proxy',
    grade=None, master=None, round=number, reduce='display'))
for size in (256,160,64):
    sheet = Image.new('RGB',(size*10,5*(size+22)), '#e0d7bf')
    draw = ImageDraw.Draw(sheet)
    for row,clip in enumerate(('idle','move','attack','hit','death')):
        draw.text((4,row*(size+22)+3),clip+' | CPU proxy',fill='#28221b')
        for col,path in enumerate(sorted((frames/clip).glob('*.png'))):
            im=resize_rgba(Image.open(path).convert('RGBA'),(size,size),space='display')
            sheet.paste(im,(col*size,row*(size+22)+22),im)
    sheet.save(review/f'spearman-r{number}-merge-clips-{size}.png')
feet = root/'review/3d-v2/spearman-g-feet-check.png'
shutil.copy2(feet,review/feet.name)
subprocess.run([sys.executable,'tools/art/anim3d/critique.py','--slug','spearman','--round',str(number),
    '--label','Cycles CPU proxy / 8 samples / decoded 160 atlas; GPU pending',
    '--painting','app/src/assets/units/spearman-256.png','--rest',str(frames/'rest/00.png'),
    '--frames',str(root/'review/3d-v2/spearman-decoded-160'),'--feet',str(feet),
    '--out',str(review),'--preset','spearman'],check=True)
shutil.copy2(root/f'review/3d-v2/spearman-round{number}.mp4',review/f'spearman-round{number}.mp4')
shutil.copy2(review/f'spearman-round{number}-restpose-compare.png',review/'spearman-f-restpose-compare.png')
print('CPU_ROUND_DELIVERED',json.dumps(result))

"""Pack the isolated CPU proxy review; never overwrite the shipped atlas."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.deliver import run
from kit.images import resize_rgba
from kit.regions import region_stats
root = Path(os.environ['ANIM_ROOT'])
review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
round_number = int(os.environ.get('ROUND', '12'))
frames = root/'preview'
receipt = json.loads((frames/'receipt.json').read_text())
for clip in ('rest','idle','move','attack','hit','death'):
    master = root/'masters/spearman-3d-v2'
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt[clip]['sha256'], (clip,'stale CPU frame source')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in receipt[clip]['look_code'].items()), 'stale CPU look'

result = run(SimpleNamespace(slug='spearman', frames=frames, anchor=(79.375,138.125),
    out=root/'atlas', review=root/'review/3d-v2', label='CPU proxy',
    grade=None, master=None, round=round_number, reduce='display'))
print(json.dumps(result))
# Keep native-size compares; 64 reference is the actual shipped token.
canvas = Image.new('RGB', (3*256, 320+192+96), '#e0d7bf')
draw = ImageDraw.Draw(canvas)
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
before = Image.open(frames/'baseline/00.png').convert('RGBA')
after = Image.open(frames/'rest/00.png').convert('RGBA')
for column, (title, im) in enumerate([('Painting',painting),('R11 CPU proxy',before),('R12 CPU proxy',after)]):
    draw.text((column*256+8,8),title,fill='#28221b')
    for size,y in [(256,28),(160,320),(64,512)]:
        small = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA') if column==0 and size==64 else resize_rgba(im,(size,size),space='display')
        canvas.paste(small,(column*256+(256-size)//2,y),small)
canvas.save(review/'spearman-r12-merge-sizes.png')
# A/B the strength change separately from the form/continuity changes.
contact_before = Image.open(frames/'contact-before/00.png').convert('RGBA')
box=(80,210,175,228)
report={name:region_stats(im,box) for name,im in [('painting',painting),('contact_100',contact_before),('contact_40',after)]}
(root/'contact-ab.json').write_text(json.dumps(report,indent=2)+'\n')
print('CONTACT_AB',json.dumps(report))

"""Validate and package isolated CPU evidence; never write the shipped atlas."""
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.deliver import run
from kit.images import resize_rgba

root = Path(os.environ['ANIM_ROOT'])
assert root.resolve() != (Path.home()/'LegatumRuns/anim-pilot').resolve(), 'CPU evidence needs an isolated root'
review = root/'review/3d-v2'
round_number = int(os.environ['ROUND'])
frames = root/'preview'
master = root/'masters/spearman-3d-v2'
receipt = json.loads((frames/'receipt.json').read_text())
for clip in ('rest','idle','move','attack','hit','death'):
    path = master/'spearman.blend' if clip == 'rest' else master/'clips'/clip/(clip+'.blend')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt[clip]['sha256'], (clip, 'stale CPU source')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p,h in receipt[clip]['look_code'].items()), 'stale CPU look'
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((master/'look').iterdir())
            if p.suffix in ('.png', '.json')} == receipt[clip]['calibration'], 'stale CPU calibration'
result = run(SimpleNamespace(slug='spearman', frames=frames, anchor=(79.375,138.125),
    out=root/'atlas', review=review, label='Cycles CPU analytical painted-look proxy',
    grade=None, master=None, round=round_number, reduce='display'))
print(json.dumps(result))
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
render = Image.open(frames/'rest/00.png').convert('RGBA')
cream = (248,244,231,255)
def composite(im):
    bg = Image.new('RGBA', im.size, cream)
    bg.alpha_composite(im)
    return bg.convert('RGB')
views = [composite(painting), composite(render), Image.blend(composite(painting),composite(render),.5)]
triptych = Image.new('RGB',(768,256),cream[:3])
for i,im in enumerate(views): triptych.paste(im,(256*i,0))
triptych.save(review/f'spearman-round{round_number}-restpose-compare.png')
triptych.save(review/'spearman-f-restpose-compare.png')
sheet = Image.new('RGB',(768,560),cream[:3]);draw=ImageDraw.Draw(sheet)
for size,y in [(256,24),(160,302),(64,486)]:
    p = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA') if size==64 else resize_rgba(painting,(size,size),space='display')
    r = resize_rgba(render,(size,size),space='display')
    for i,im in enumerate([composite(p),composite(r),Image.blend(composite(p),composite(r),.5)]):
        sheet.paste(im,(i*256+(256-size)//2,y))
for i,label in enumerate(['Painting','R%d CPU proxy'%round_number,'50/50 crossfade']): draw.text((i*256+8,6),label,fill='#302820')
sheet.save(review/f'spearman-round{round_number}-sizes.png')

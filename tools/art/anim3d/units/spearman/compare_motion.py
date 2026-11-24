"""Compare immutable round-8 GPU strips with this lane's actual CPU renders.

ANIM_ROOT points at the isolated lane. Evidence is copied to the main review
folder only under r9c names, leaving the other lanes' canonical images intact.
"""
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw
root = Path(os.environ['ANIM_ROOT'])
review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
master = root/'masters/spearman-3d-v2'
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
rest_before = Image.open(root/'before/spearman-f-restpose-compare.png').convert('RGBA')
rest_after = Image.open(master/'renders/c/three-quarter.png').convert('RGBA')
sheet = Image.new('RGB', (816, 380), '#e0d7bf')
draw = ImageDraw.Draw(sheet)
for col, (label, im) in enumerate([
        ('Painting', painting), ('Round 8 GPU', rest_before.crop((280,36,536,292))),
        ('Round 9c CPU | master unchanged', rest_after)]):
    im = im.resize((256,256), Image.Resampling.LANCZOS)
    x = 8+col*272
    draw.text((x,10), label+' | 256 / 64 px', fill='#28221b')
    sheet.paste(im,(x,36),im)
    thumb = im.resize((64,64), Image.Resampling.LANCZOS)
    sheet.paste(thumb,(x+96,302),thumb)
sheet.save(review/'spearman-r9c-rest-compare.png')
for clip in ['move', 'attack', 'hit', 'death']:
    manifest = json.loads((master/'renders'/('e-'+clip)/'render.json').read_text())
    if manifest['device'] != 'CPU' or manifest['resolution'] != 256:
        continue
    frames = sorted((master/'renders'/('e-'+clip)).glob('[0-9][0-9].png'))
    if not frames:
        continue
    before = Image.open(root/'before'/f'spearman-e-{clip}-strip.png').convert('RGBA')
    sheet = Image.new('RGB', ((len(frames)+1)*272, 772), '#e0d7bf')
    draw = ImageDraw.Draw(sheet)
    for row, label in enumerate(['Round 8 GPU', 'Round 9c Cycles CPU preview']):
        y = row*386
        for col in range(len(frames)+1):
            im = (painting if col == 0 else
                  before.crop((8+col*272, 36, 8+col*272+256, 292)) if row == 0 else
                  Image.open(frames[col-1]).convert('RGBA').resize((256,256), Image.Resampling.LANCZOS))
            x = 8+col*272
            draw.text((x, y+10), 'Painting | 256 / 64 px' if col == 0 else f'{label} | {clip} {col-1:02}', fill='#28221b')
            sheet.paste(im, (x, y+36), im)
            thumb = im.resize((64,64), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x+96,y+302), thumb)
    path = review/f'spearman-r9c-{clip}-compare.png'
    sheet.save(path)
    print(path)
feet_path = root/'review/3d-v2/spearman-g-feet-check.png'
if feet_path.exists():
    sheet = Image.new('RGB', (1600, 1060), '#e0d7bf')
    draw = ImageDraw.Draw(sheet)
    for row, (label, path) in enumerate([
            ('Round 8 GPU', root/'before/spearman-g-feet-check.png'),
            ('Round 9c CPU', feet_path)]):
        draw.text((12,row*530+4),label,fill='#28221b')
        sheet.paste(Image.open(path).convert('RGB'),(0,row*530+20))
    sheet.save(review/'spearman-r9c-feet-compare.png')

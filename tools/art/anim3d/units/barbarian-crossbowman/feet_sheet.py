"""Publish ungraded front/top geometry evidence, never the painted camera view."""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(os.environ['ANIM_ROOT'])
folder = root / 'masters/barbarian-crossbowman/feet'
report = json.loads((folder / 'evidence.json').read_text())
sheet = Image.new('RGBA', (1280, 384), (233, 207, 160, 255))
draw = ImageDraw.Draw(sheet)
draw.text((8, 5), 'Actual boots / travel toward -Y / ' + report['device'], fill='black')
for row, view in enumerate(('top', 'front')):
    for i in range(8):
        im = Image.open(folder / f'{view}-{i:02}.png').convert('RGBA')
        sheet.alpha_composite(im.resize((160, 160), Image.Resampling.LANCZOS), (i*160, 26+row*176))
        draw.text((i*160+8, 16+row*176), f'{view} {i+1}', fill='black')
sheet.save(root / 'review/3d-v2/barbarian-crossbowman-g-feet-check.png')
print(json.dumps(report['contact']))

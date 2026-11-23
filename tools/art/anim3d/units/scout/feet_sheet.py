"""Publish the two diagnostic views at native 160px per sample."""
import os,json
from pathlib import Path
from PIL import Image,ImageDraw
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/scout';info=json.loads((m/'feet.json').read_text())
sheet=Image.new('RGBA',(1280,370),(233,207,160,255));draw=ImageDraw.Draw(sheet)
for row,view in enumerate(['front','top']):
    draw.text((8,row*185+5),f'{view}: source walk, travel toward -Y / {info["device"]}',fill='black')
    for i in range(8):sheet.alpha_composite(Image.open(m/'feet'/f'{view}-{i+1:02d}.png').convert('RGBA'),(160*i,row*185+25))
sheet.save(r/'review/3d-v2/scout-g-feet-check.png')

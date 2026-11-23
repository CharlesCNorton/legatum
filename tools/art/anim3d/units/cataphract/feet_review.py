"""Combine actual foot renders, never a schematic substitute for the geometry."""
import os, json
from pathlib import Path
from PIL import Image, ImageDraw
root = Path(os.environ['ANIM_ROOT']); master = root/'masters/cataphract'
manifest = json.loads((master/'feet/manifest.json').read_text())
sheet = Image.new('RGBA',(1536,440),(233,207,160,255)); draw = ImageDraw.Draw(sheet)
for row,view in enumerate(['top','front']):
    for i in range(8):
        im = Image.open(master/f'feet/{view}/{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.LANCZOS)
        sheet.alpha_composite(im,(i*192,row*220+26))
        draw.text((i*192+5,row*220+5),f'{view} {i+1} / {manifest["device"]}',fill=(55,42,25))
        if view == 'top': draw.text((i*192+5,row*220+202),'Travel -Y (down)',fill=(55,42,25))
sheet.convert('RGB').save(root/'review/3d-v2/cataphract-g-feet-check.png')

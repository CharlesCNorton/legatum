"""Combine actual foot renders, never a schematic substitute for the geometry."""
import os, json
from pathlib import Path
from PIL import Image, ImageDraw
root = Path(os.environ['ANIM_ROOT']); master = root/'masters/cavalry'
manifest = json.loads((master/'feet/manifest.json').read_text())
sheet = Image.new('RGBA',(1536,440),(233,207,160,255)); draw = ImageDraw.Draw(sheet)
for row,view in enumerate(['top','front']):
    for i in range(8):
        im = Image.open(master/f'feet/{view}/{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.LANCZOS)
        sheet.alpha_composite(im,(i*192,row*220+26))
        draw.text((i*192+5,row*220+5),f'{view} {i+1} / {manifest["device"]}',fill=(55,42,25))
        if view == 'top': draw.text((i*192+5,row*220+202),'Travel -Y (down)',fill=(55,42,25))
        else:
            floor=row*220+26+round(96+(.5-.112)*192/2.4)
            draw.line((i*192,floor,(i+1)*192-1,floor),fill=(170,135,85))
            low=min(v['lowest_z'] for v in manifest['sole_samples'][i].values())
            draw.text((i*192+5,row*220+202),f'Lowest sole {low:.3f} m',fill=(55,42,25))
sheet.convert('RGB').save(root/'review/3d-v2/cavalry-g-feet-check.png')

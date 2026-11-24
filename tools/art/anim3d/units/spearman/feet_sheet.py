"""Assemble native 192px top/front foot renders with measured headings."""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw
root = Path(os.environ['ANIM_ROOT'])
folder = root/'masters/spearman-3d-v2/feet-check'
data = json.loads((folder/'metrics.json').read_text())
bands = (len(data['frames'])+7)//8
sheet = Image.new('RGB', (8*200, 52+bands*448+30), '#e0d7bf')
draw = ImageDraw.Draw(sheet)
draw.text((12, 8), 'Spearman move | actual lower-leg geometry | forward = -Y | top view: travel UP', fill='#28221b')
for i, row in enumerate(data['frames']):
    x = (i%8)*200+4
    band = (i//8)*448
    draw.text((x, band+32), f"Sample {i+1}/{len(data['frames'])} | frame {row['frame']}", fill='#28221b')
    for y, view in [(52, 'top'), (288, 'front')]:
        y += band
        im = Image.open(folder/f'{view}-{i:02}.png').convert('RGBA')
        if view == 'front':
            floor_y = y+round(96+(.31-.106)*192/1.3)
            draw.line((x,floor_y,x+191,floor_y),fill='#b5a88e',width=1)
        sheet.paste(im, (x, y), im)
    feet = row['feet']
    label=lambda s: 'raised' if feet[s]['heading_projection_m']<.08 else '%.1f deg'%feet[s]['yaw_degrees']
    draw.text((x, band+250), 'L '+label('l')+' / R '+label('r'), fill='#28221b')
checks = data['checks']
draw.text((12, sheet.height-22), 'TOP / FRONT | planted heading %.2f deg | compensated slip %.3f mm | contact error %.3f mm | virtual speed %.3f m/s' % (checks['max_planted_heading_degrees'],checks['max_sole_contact_slip_m']*1000,checks['max_planted_floor_error_m']*1000,checks['virtual_forward_speed_m_s']), fill='#28221b')
path = root/'review/3d-v2/spearman-g-feet-check.png'
sheet.save(path)
print(path)

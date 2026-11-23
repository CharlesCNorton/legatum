"""Assemble the required top/front walk review without altering render pixels."""
import json
import os
from pathlib import Path
from PIL import Image,ImageDraw

root = Path(os.environ['ANIM_ROOT'])
folder = root/'masters/horseman/feet-check'
report = json.loads((folder/'report.json').read_text())
sheet = Image.new('RGB',(8*160,2*190+55),(240,232,214))
draw = ImageDraw.Draw(sheet)
draw.text((8,8),'Actual lower legs | blue front L, green front R, orange rear L, purple rear R | 25cm grid',fill=(40,34,27))
draw.text((8,25),'Top: travel down. Front: looking against travel. Source walk is in place; stance moves backward under the body.',fill=(40,34,27))
for row,view in enumerate(('top','front')):
    for index,record in enumerate(report['frames']):
        im = Image.open(folder/f'{view}-{index:02}.png').convert('RGBA')
        im.thumbnail((152,152),Image.Resampling.LANCZOS)
        x,y = index*160+4,row*190+55
        draw.text((x,y),f'{view} {index+1}',fill=(40,34,27))
        sheet.paste(im,(x,y+18),im)
        planted = [name for name,m in record['hooves'].items() if m['support']]
        draw.text((x,y+171),','.join(planted) or 'NO SUPPORT',fill=(40,34,27))
destination = root/'review/3d-v2/horseman-g-feet-check.png'
sheet.save(destination)
(destination.with_suffix('.json')).write_text(json.dumps(report,indent=2))
print(destination)

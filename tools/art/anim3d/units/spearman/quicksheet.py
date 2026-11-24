"""Tile quicklook frames into one labelled sheet on the painting's cream.
python quicksheet.py <dir> <out.png> [views] [cell]"""
import sys
from pathlib import Path
from PIL import Image,ImageDraw
src=Path(sys.argv[1]);views=(sys.argv[3] if len(sys.argv)>3 else 'cam').split(',')
cell=int(sys.argv[4]) if len(sys.argv)>4 else 256
rows=[sorted(src.glob(view+'-*.png')) for view in views]
n=max(len(r) for r in rows)
sheet=Image.new('RGB',(n*cell,len(rows)*cell),(222,214,190))
draw=ImageDraw.Draw(sheet)
for y,row in enumerate(rows):
 for x,path in enumerate(row):
  im=Image.open(path).convert('RGBA')
  if im.width!=cell:im=im.resize((cell,cell),Image.LANCZOS)
  sheet.paste(im,(x*cell,y*cell),im);draw.text((x*cell+4,y*cell+2),f'{views[y]} {x}',fill=(60,50,40))
sheet.save(sys.argv[2]);print(sys.argv[2])

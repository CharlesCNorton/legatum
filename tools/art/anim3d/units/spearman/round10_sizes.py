"""Compare current combined rest and decoded motion at native review sizes."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba
from PIL import Image, ImageDraw
root = Path(os.environ['ANIM_ROOT']); review = root/'review/3d-v2'
master = root/'masters/spearman-3d-v2'
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
render = Image.open(master/'renders/c/three-quarter.png').convert('RGBA')
background = (224,215,191,255)
sheet = Image.new('RGB', (4*272, 620), background[:3]); draw=ImageDraw.Draw(sheet)
for size,y in [(256,30),(160,320),(64,530)]:
    tiles=[]
    for im in [painting,render]:
        tile=Image.new('RGBA',(size,size),background); tile.alpha_composite(resize_rgba(im,(size,size)))
        tiles.append(tile.convert('RGB'))
    tiles.append(Image.blend(*tiles,.5))
    split=tiles[0].copy();split.paste(tiles[1].crop((size//2,0,size,size)),(size//2,0));tiles.append(split)
    for i,(label,im) in enumerate(zip(['Painting','Round 10 CPU','50/50 crossfade','split'],tiles)):
        x=i*272+(272-size)//2;draw.text((i*272+8,y-19),f'{label} | {size}px',fill=(40,34,27));sheet.paste(im,(x,y))
sheet.save(review/'spearman-round10-sizes.png')

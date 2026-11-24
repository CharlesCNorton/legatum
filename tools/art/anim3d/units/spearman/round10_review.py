"""Native-size R9/R10c CPU motion comparisons; all outputs stay outside git.

ANIM_ROOT is the lane; before/ contains a preserved R9 render root. Both passes
must use identical render settings and the same fixed rest grade.
"""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(os.environ['ANIM_ROOT'])
review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
master = root/'masters/spearman-3d-v2'
before = root/'before/masters/spearman-3d-v2'
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
a = json.loads((master/'painting-grade.json').read_text())
b = json.loads((before/'painting-grade.json').read_text())
assert a['luts'] == b['luts'] and a['master_sha256'] == b['master_sha256']

def sheet(clip, indices):
    stage = 'c' if clip == 'rest' else 'e-'+clip
    for folder in [before, master]:
        manifest = json.loads((folder/'renders'/stage/'render.json').read_text())
        assert manifest['engine'] == 'CYCLES' and manifest['device'] == 'CPU'
        assert manifest['resolution'] == 256 and manifest['samples'] == 16
    images = []
    for folder in [before, master]:
        images.append([Image.open(folder/'renders'/stage/
                     ('three-quarter.png' if clip == 'rest' else f'{i:02}.png')).convert('RGBA')
                       for i in indices])
    width = (len(indices)+1)*272
    output = Image.new('RGB', (width, 2*sum(size+30 for size in [256,160,64])), '#e0d7bf')
    draw = ImageDraw.Draw(output)
    y = 0
    for size in [256, 160, 64]:
        for label, row in zip(['Round 9 CPU', 'Round 10c CPU'], images):
            for col, im in enumerate([painting]+row):
                x = col*272+8
                draw.text((x,y+5), f'{"Painting" if col == 0 else label+" / "+clip+" "+str(indices[col-1])} | {size}px', fill='#28221b')
                thumb = im.resize((size,size), Image.Resampling.LANCZOS)
                output.paste(thumb, (x+(256-size)//2, y+24), thumb)
            y += size+30
    path = review/f'spearman-r10c-{clip}-compare.png'
    output.save(path)
    print(path)

sheet('rest', [0])
sheet('move', [0, 2, 4, 6])
sheet('death', [1, 2, 3, 4, 5, 6, 7, 9])
# Side-by-side animated evidence retains exact delivered clip cadence/hold.
for clip, count, fps in [('move', 8, 6), ('death', 10, 4)]:
    cells = []
    for i in range(count):
        cell = Image.new('RGB',(3*160,184),'#e0d7bf')
        draw=ImageDraw.Draw(cell)
        for col,(label,folder) in enumerate([('Painting',None),('Round 9 CPU',before),('Round 10c CPU',master)]):
            im=painting if folder is None else Image.open(folder/'renders'/('e-'+clip)/f'{i:02}.png').convert('RGBA')
            im=im.resize((160,160),Image.Resampling.LANCZOS)
            cell.paste(im,(col*160,24),im)
            draw.text((col*160+4,5),label,fill='#28221b')
        cells.append(cell)
    cells[0].save(review/f'spearman-r10c-{clip}.webp',save_all=True,append_images=cells[1:],duration=round(1000/fps),loop=0,quality=90)

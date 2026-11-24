"""R15a native-size A/B sheets: painting, matched R14 CPU, candidate CPU."""
import json
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba

root = Path(os.environ['ANIM_ROOT'])
review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
before = Image.open(root/'preview/before-calibrated.png').convert('RGBA')
after = Image.open(root/'preview/rest/00.png').convert('RGBA')
images = [painting, before, after]
labels = ['Painting', 'Round 14 | CPU proxy', 'R15a | CPU proxy']
for size in (256, 160, 64):
    canvas = Image.new('RGB', (3*(size+20), size+60), '#f8f4e8')
    draw = ImageDraw.Draw(canvas)
    for i, (im, label) in enumerate(zip(images, labels if size > 64 else ['Painting', 'R14 CPU', 'R15a CPU'])):
        if size == 64 and i == 0:
            im = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
        im = resize_rgba(im, (size, size), space='display')
        x = i*(size+20)+10
        draw.text((x, 8), label, fill='#302518')
        canvas.paste(im, (x, 30), im)
    canvas.save(review/f'spearman-r15a-compare-{size}.png')
for name, box, scale in [('sandals', (87,204,170,224),6), ('cloak', (96,118,169,194),4)]:
    w,h=(box[2]-box[0])*scale,(box[3]-box[1])*scale
    canvas=Image.new('RGB',(3*(w+16),h+40),'#f8f4e8');draw=ImageDraw.Draw(canvas)
    for i,(im,label) in enumerate(zip(images,labels)):
        crop=im.crop(box).resize((w,h),Image.Resampling.NEAREST)
        canvas.paste(crop,(i*(w+16)+8,30),crop)
        draw.text((i*(w+16)+8,8),label,fill='#302518')
    canvas.save(review/f'spearman-r15a-{name}-detail.png')
# Specific detail/edge measures in fixed boxes, alongside the shared critique.
# Red mask is an explicitly defined pigment proxy, not a geometry/object ID.
report = {}
for label, im in zip(('painting','before','after'), images):
    a=np.asarray(im).astype(float);r,g,b=a[...,:3].transpose(2,0,1)
    red=(r>1.5*g)&(r>1.7*b)&(a[...,3]>128)
    lum=a[...,:3]@np.array([.2126,.7152,.0722])
    report[label]={'spear_side_red_pixels_98_120_112_175':int(red[120:175,98:112].sum())}
    for name,(x0,y0,x1,y1) in [('left_instep',(94,209,108,218)),('right_toes',(153,214,165,220))]:
        q=lum[y0:y1,x0:x1]
        report[label][name]={'mean_luminance':float(q.mean()),'p10':float(np.percentile(q,10)),
                             'p90':float(np.percentile(q,90)), 'raw_rgb_mae_to_painting':float(np.abs(a[y0:y1,x0:x1,:3]-np.asarray(painting)[y0:y1,x0:x1,:3]).mean())}
(root/'detail-metrics.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

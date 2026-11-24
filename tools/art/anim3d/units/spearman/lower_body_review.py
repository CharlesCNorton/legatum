"""R10a fixed-LUT CPU comparison at native 256/160/64, with region diagnostics.

ANIM_ROOT selects the isolated candidate; baseline is the preserved R9 CPU pass.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from grade import apply

ROOT = Path.home()/'LegatumRuns/anim-pilot'
BASE = ROOT/'lanes/spearman-r9-merge/masters/spearman-3d-v2'
MASTER = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
OUT = ROOT/'review/3d-v2'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduce_linear(im, size):
    """Premultiplied linear-light RGBA Lanczos; alpha is never gamma encoded."""
    def linear(c):
        c /= 255
        return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4
    pixels = list(im.getdata())
    alpha = Image.new('F', im.size)
    alpha.putdata([p[3]/255 for p in pixels])
    alpha = list(alpha.resize((size, size), Image.Resampling.LANCZOS).getdata())
    channels = []
    for i in range(3):
        channel = Image.new('F', im.size)
        channel.putdata([linear(p[i])*p[3]/255 for p in pixels])
        channels.append(list(channel.resize((size, size), Image.Resampling.LANCZOS).getdata()))
    def encode(c):
        c = max(0, min(1, c))
        return round(255*(12.92*c if c <= .0031308 else 1.055*c**(1/2.4)-.055))
    result = Image.new('RGBA', (size, size))
    result.putdata([tuple(encode(ch[i]/a) if a > 1e-6 else 0 for ch in channels)
                    + (round(255*max(0, min(1, a))),) for i, a in enumerate(alpha)])
    return result


def main():
    baseline = json.loads((BASE/'renders/c/render.json').read_text())
    candidate = json.loads((MASTER/'renders/c/render.json').read_text())
    for key in ('engine', 'device', 'resolution', 'samples', 'blender'):
        assert baseline[key] == candidate[key], key
    assert candidate['device'] == 'CPU' and candidate['resolution'] == 256
    luts = json.loads((BASE/'painting-grade.json').read_text())['luts']
    reference = Path('app/src/assets/units/spearman-256.png')
    old_raw = BASE/'renders/c/raw/three-quarter.png'
    new_raw = MASTER/'renders/c/three-quarter.png'
    assert not candidate.get('grade_sha256'), 'Review expects raw candidate and fixed R9 LUT'
    painting = Image.open(reference).convert('RGBA')
    before = apply(Image.open(old_raw).convert('RGBA'), luts)
    after = apply(Image.open(new_raw).convert('RGBA'), luts)
    after.save(OUT/'spearman-r10a-rest.png')
    bg = (224, 215, 191)
    def flat(im):
        return Image.alpha_composite(Image.new('RGBA', im.size, bg+(255,)), im).convert('RGB')
    for size in (256, 160, 64):
        images = [reduce_linear(im, size) for im in (painting, before, after)]
        if size == 64:
            images[0] = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
        images = list(map(flat, images))
        split = images[0].copy()
        split.paste(images[2].crop((size//2, 0, size, size)), (size//2, 0))
        entries = list(zip(('Painting', 'Round 9 CPU', 'Round 10a CPU'), images))
        entries += [('50/50 painting + R10a', Image.blend(images[0], images[2], .5)),
                    ('Split painting / R10a', split)]
        width = max(176, size+16)
        sheet = Image.new('RGB', (5*width, size+48), bg)
        draw = ImageDraw.Draw(sheet)
        for i, (label, im) in enumerate(entries):
            draw.text((i*width+8, 8), f'{label} | {size}px', fill=(40, 34, 27))
            sheet.paste(im, (i*width+(width-size)//2, 36))
        sheet.save(OUT/f'spearman-r10a-{size}.png')
    crop = (86, 174, 170, 224)
    detail = Image.new('RGB', (3*336, 232), bg)
    draw = ImageDraw.Draw(detail)
    for i, (label, im) in enumerate(zip(('Painting', 'Round 9 CPU', 'Round 10a CPU'), (painting, before, after))):
        draw.text((i*336+8, 8), label+' | 4x detail, not native size', fill=(40, 34, 27))
        detail.paste(flat(im).crop(crop).resize((336, 200), Image.Resampling.NEAREST), (i*336, 28))
    detail.save(OUT/'spearman-r10a-lower-leg-detail.png')
    metrics = {'settings': {k: candidate[k] for k in ('engine', 'device', 'resolution', 'samples', 'blender')},
               'source_sha256': digest(reference), 'baseline_raw_sha256': digest(old_raw),
               'candidate_raw_sha256': digest(new_raw), 'fixed_grade_sha256': digest(BASE/'painting-grade.json')}
    for name, im in (('round9', before), ('round10a', after)):
        metrics[name] = {}
        for label, box in [('whole', (0, 0, 256, 256)), ('figure_above_base', (85, 50, 190, 205)),
                           ('lower_legs_above_base', (90, 180, 168, 205))]:
            a = painting.getchannel('A').crop(box).point(lambda v: 255 if v>32 else 0)
            b = im.getchannel('A').crop(box).point(lambda v: 255 if v>32 else 0)
            area = lambda mask: sum(mask.histogram()[1:])
            metrics[name][label+'_iou'] = area(ImageChops.multiply(a, b))/area(ImageChops.lighter(a, b))
        a, b = flat(painting).crop(crop), flat(im).crop(crop)
        metrics[name]['lower_body_rgb_mae_255'] = sum(abs(x-y) for p,q in zip(a.getdata(),b.getdata()) for x,y in zip(p,q))/(a.width*a.height*3)
    metrics['limits'] = 'Alpha IoU above y=205 avoids most stone; includes cloak/spear. RGB error includes cast shadows. Diagnostics, not art approval. R9 LUT shared; native linear-light reductions.'
    (OUT/'spearman-r10a-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()

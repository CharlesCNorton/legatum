"""Compare lane-a rest geometry with a fixed grade at native 256 and 64 px.

Run with the isolated lane ANIM_ROOT, after its CPU c render. Preserved GPU
evidence is a separate column; the CPU pair uses identical samples and LUTs.
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from grade import apply


def main():
    root = Path(os.environ['ANIM_ROOT'])
    master = root/'masters/spearman-3d-v2'
    out = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
    source = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    source64 = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
    luts = json.loads((master/'baseline-grade.json').read_text())['luts']
    baseline_manifest = json.loads((master/'baseline-cpu/render.json').read_text())
    manifest = json.loads((master/'renders/c/render.json').read_text())
    for key in ['engine', 'device', 'samples', 'resolution']:
        assert manifest[key] == baseline_manifest[key], f'Incomparable CPU settings: {key}'
    assert manifest['device'] == 'CPU' and manifest['resolution'] == 256
    before = apply(Image.open(master/'baseline-cpu/raw/three-quarter.png').convert('RGBA'), luts)
    after_path = master/'renders/c'
    if manifest.get('grade_sha256'):
        after_path /= 'raw'
    after = apply(Image.open(after_path/'three-quarter.png').convert('RGBA'), luts)
    after.save(out/'spearman-r9a-rest.png')
    gpu = Image.open(master/'round8-render/three-quarter.png').convert('RGBA')
    gpu = gpu.resize((256, 256), Image.Resampling.LANCZOS)
    background = (224, 215, 191)

    def flat(im):
        return Image.alpha_composite(Image.new('RGBA', im.size, background+(255,)), im).convert('RGB')

    painting, old, new = map(flat, [source, before, after])
    split = painting.copy()
    split.paste(new.crop((128, 0, 256, 256)), (128, 0))
    entries = [('Painting', painting), ('Round 8 | GPU', flat(gpu)),
               ('Baseline | CPU 16 samples', old), ('R9a | CPU 16 samples', new),
               ('50/50 painting + R9a', Image.blend(painting, new, .5)),
               ('Split: painting | R9a', split)]
    small = [im.resize((64, 64), Image.Resampling.LANCZOS) for _, im in entries]
    small[0] = flat(source64)
    small[4] = Image.blend(small[0], small[3], .5)
    small[5] = small[0].copy()
    small[5].paste(small[3].crop((32, 0, 64, 64)), (32, 0))
    sheet = Image.new('RGB', (272*len(entries), 390), background)
    draw = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(entries):
        x = i*272+8
        draw.text((x, 10), label, fill=(40, 34, 27))
        sheet.paste(im, (x, 36))
        sheet.paste(small[i], (x+96, 306))
    sheet.save(out/'spearman-r9a-restpose-compare.png')
    sheet.crop((0, 0, sheet.width, 296)).save(out/'spearman-r9a-256.png')
    tokens = Image.new('RGB', (272*len(entries), 96), background)
    labels = ImageDraw.Draw(tokens)
    for i, (label, _) in enumerate(entries):
        labels.text((i*272+8, 4), label, fill=(40, 34, 27))
        tokens.paste(small[i], (i*272+104, 24))
    tokens.save(out/'spearman-r9a-64.png')
    metrics = {}
    for name, im in [('baseline_cpu', before), ('r9a_cpu', after)]:
        regions = {}
        for label, box in [('whole', (0, 0, 256, 256)),
                           ('figure_above_feet', (85, 50, 190, 208)),
                           ('cloak_and_skirt', (97, 148, 173, 199)),
                           ('head_and_crest', (116, 54, 148, 104))]:
            a = source.getchannel('A').crop(box).point(lambda v: 255 if v>32 else 0)
            b = im.getchannel('A').crop(box).point(lambda v: 255 if v>32 else 0)
            area = lambda mask: sum(mask.histogram()[1:])
            regions[label] = round(area(ImageChops.multiply(a, b))/area(ImageChops.lighter(a, b)), 5)
        metrics[name] = regions
    metrics['note'] = 'Alpha IoU only; not an art or animation pass. Same CPU settings and baseline LUT.'
    (out/'spearman-r9a-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()

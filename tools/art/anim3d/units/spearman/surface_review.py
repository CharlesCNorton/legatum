"""Native 256/64 material comparison and region diagnostics; no image synthesis."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from grade import apply, fit, histograms, cdf

root = Path.home()/'LegatumRuns/anim-pilot'
work = Path(sys.argv[1]) if len(sys.argv) > 1 else root/'masters/spearman-r9b'
review = root/'review/3d-v2'
painting_path = Path('app/src/assets/units/spearman-256.png')
painting = Image.open(painting_path).convert('RGBA')
before = Image.open(work/'ab/before-raw.png').convert('RGBA').resize((256, 256), Image.Resampling.LANCZOS)
after = Image.open(work/'ab/after-raw.png').convert('RGBA').resize((256, 256), Image.Resampling.LANCZOS)
r8 = Image.open(work/'masters/spearman-3d-v2/round8-gpu/three-quarter.png').convert('RGBA').resize((256, 256), Image.Resampling.LANCZOS)
luts = fit(after, painting)
after_grade = apply(after, luts)
before_grade = apply(before, luts)
bg = (224, 215, 191)


def sheet(images, name):
    output = Image.new('RGB', (272*len(images), 380), bg)
    draw = ImageDraw.Draw(output)
    for i, (label, im) in enumerate(images):
        x = i*272+8
        draw.text((x, 10), label, fill=(40, 34, 27))
        output.paste(im, (x, 36), im)
        small = im.resize((64, 64), Image.Resampling.LANCZOS)
        output.paste(small, (x+96, 302), small)
    output.save(review/f'spearman-r9b-{name}.png')


sheet([('Painting | 256 / 64 px', painting), ('Round 8 | supplied GPU', r8),
       ('Before | CPU, candidate grade', before_grade), ('After | CPU, candidate grade', after_grade)], 'comparison')
sheet([('Painting | 256 / 64 px', painting), ('Before | CPU raw', before),
       ('After | CPU raw', after)], 'raw-comparison')
regions = {'Shoulder / skin / linen': (93, 94, 130, 143),
           'Helmet / bronze': (116, 80, 151, 112),
           'Shield / worn bronze': (127, 105, 181, 181),
           'Linen / leather / cloak': (99, 145, 144, 196)}
close = Image.new('RGB', (4*228, len(regions)*280), bg)
draw = ImageDraw.Draw(close)
metrics = {}
for row, (label, box) in enumerate(regions.items()):
    for col, (name, im) in enumerate([('Painting', painting), ('Round 8 GPU', r8), ('Before CPU', before_grade), ('After CPU', after_grade)]):
        draw.text((col*228+8, row*280+8), label if col == 0 else name, fill=(40, 34, 27))
        crop = im.crop(box)
        crop.thumbnail((204, 198))
        # Fourfold enlargement of actual 256px pixels, explicitly diagnostic.
        crop = crop.resize((crop.width*3, crop.height*3), Image.Resampling.NEAREST)
        close.paste(crop, (col*228+8, row*280+28), crop)
    mask = ImageChops.multiply(painting.getchannel('A'), after.getchannel('A')).crop(box)
    metrics[label] = {name: [round(x, 3) for x in ImageStat.Stat(
        ImageChops.difference(im.convert('RGB'), painting.convert('RGB')).crop(box), mask).mean]
        for name, im in [('before', before_grade), ('after', after_grade)]}
close.save(review/'spearman-r9b-details.png')
assert ImageChops.difference(before.getchannel('A'), after.getchannel('A')).getbbox() is None
report = {'painting_sha256': hashlib.sha256(painting_path.read_bytes()).hexdigest(),
          'grade_strength': .8, 'luts': luts, 'grade_policy': 'One candidate-rest LUT applied to both CPU previews; supplied round8 GPU retains its original grade.',
          'raw_alpha_identical': True, 'region_rgb_mae': metrics,
          'opaque_cdf_error': {name: [round(sum(abs(a-b) for a, b in zip(cdf(x), cdf(y)))/256, 6)
              for x, y in zip(histograms(im), histograms(painting))]
              for name, im in [('before_same_grade', before_grade), ('after_same_grade', after_grade)]},
          'note': 'Diagnostics only. Histogram matching and pixel errors do not establish artistic quality.'}
(work/'ab/painting-grade.json').write_text(json.dumps(report, indent=2)+'\n')
# Separate raw/graded files stay available for inspection.
after_grade.save(work/'ab/after.png')
before_grade.save(work/'ab/before.png')
print(json.dumps({k: v for k, v in report.items() if k != 'luts'}, indent=2))

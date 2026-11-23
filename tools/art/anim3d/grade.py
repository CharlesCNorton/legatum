"""Fit one alpha-masked RGB histogram grade at rest; reuse it for every frame.

Never fit per-frame: that would pump colour during motion. Preserve raw renders
and alpha. The grade is bound to the master hash and recorded in each manifest.
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER = ROOT/'masters/spearman-3d-v2'
REVIEW = ROOT/'review/3d-v2'
GRADE = MASTER/'painting-grade.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def histograms(image):
    mask = image.getchannel('A').point(lambda x: 255 if x > 240 else 0)
    return [image.getchannel(c).histogram(mask=mask) for c in 'RGB']


def cdf(hist):
    total = sum(hist)
    assert total, 'Empty opaque mask'
    result, acc = [], 0
    for count in hist:
        acc += count
        result.append(acc/total)
    return result


def fit(render, painting, strength=.80):
    tables = []
    for src, target in zip(histograms(render), histograms(painting)):
        s, t = cdf(src), cdf(target)
        j, lut = 0, []
        for i, quantile in enumerate(s):
            while j < 255 and t[j] < quantile: j += 1
            # Monotone mapping preserves tonal ordering and clamps only the
            # unobserved tails. Blending retains natural colour relationships.
            lut.append(round(i*(1-strength)+j*strength))
        tables.append(lut)
    return tables


def apply(image, tables):
    channels = [image.getchannel(c).point(table) for c, table in zip('RGB', tables)]
    return Image.merge('RGBA', (*channels, image.getchannel('A')))


def main(stage):
    folder = MASTER/'renders'/stage
    manifest = json.loads((folder/'render.json').read_text())
    raw = folder/'raw'
    raw.mkdir(exist_ok=True)
    # An ungraded render.json is written by render.py on every successful run.
    if not manifest.get('grade_sha256'):
        for path in folder.glob('*.png'): shutil.copyfile(path, raw/path.name)
    if stage == 'c':
        assert manifest['blend_sha256'] == digest(MASTER/'spearman.blend'), 'Stale rest render: rerender c before grading'
        render = Image.open(raw/'three-quarter.png').convert('RGBA').resize((256, 256), Image.Resampling.LANCZOS)
        source_path = Path('app/src/assets/units/spearman-256.png')
        source = Image.open(source_path).convert('RGBA')
        data = {'master_sha256': digest(MASTER/'spearman.blend'), 'reference_sha256': digest(source_path),
                'calibration_render_sha256': digest(raw/'three-quarter.png'), 'strength': .80,
                'luts': fit(render, source)}
        GRADE.write_text(json.dumps(data, indent=2))
    data = json.loads(GRADE.read_text())
    assert data['master_sha256'] == digest(MASTER/'spearman.blend'), 'Stale grade: render c first'
    for path in sorted(raw.glob('*.png')):
        apply(Image.open(path).convert('RGBA'), data['luts']).save(folder/path.name)
    manifest['grade_sha256'] = digest(GRADE)
    manifest['grade_reference_sha256'] = data['reference_sha256']
    manifest['raw_sha256'] = {p.name: digest(p) for p in sorted(raw.glob('*.png'))}
    (folder/'render.json').write_text(json.dumps(manifest, indent=2))
    print('GRADE', stage, data['strength'], manifest['grade_sha256'])


if __name__ == '__main__':
    main(sys.argv[1])

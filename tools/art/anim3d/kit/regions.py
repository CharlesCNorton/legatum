"""Regional A/B diagnostics: where a round got better or worse, not just whether.

Whole-image IoU and colour error hide regional changes (the shared base inflates
IoU; a matching torso hides thin legs). Spearman round 10 used these three
measures to keep regional wins while the whole-image numbers slipped slightly:

- `region_iou`: alpha overlap inside a box (e.g. lower legs above the base).
- `region_rgb_mae`: mean absolute RGB error to the painting inside a box.
- `pale_pixels`: bright, low-chroma pixels inside a box, for unpainted surfaces
  that appear in motion poses the painting never shows.

Boxes are (x0, y0, x1, y1) in pixels of the compared image. Both sides of an
A/B must share renderer settings and ONE fixed grade. These are diagnostics,
never art approval. Pure Pillow/numpy; run with the pipeline venv.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .images import resize_rgba

CREAM = (224, 215, 191)


def _rgba(image):
    return np.asarray(image.convert('RGBA'))


def region_iou(painting, render, box=None, threshold=32):
    """Alpha intersection over union inside `box` (whole image when None)."""
    a = _rgba(painting)[..., 3] > threshold
    b = _rgba(render)[..., 3] > threshold
    assert a.shape == b.shape, 'Compare images at the same size'
    if box:
        x0, y0, x1, y1 = box
        a, b = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
    union = np.count_nonzero(a | b)
    return float(np.count_nonzero(a & b)/union) if union else 1.0


def region_rgb_mae(painting, render, box, opaque=240, background=None):
    """Mean absolute RGB difference (/255) inside `box`.

    Default: only pixels opaque in both images. With `background`, both are
    flattened on that colour first, so silhouette differences count as error.
    """
    x0, y0, x1, y1 = box
    p, r = _rgba(painting).astype(float), _rgba(render).astype(float)
    if background is not None:
        bg = np.array(background, dtype=float)
        p, r = (im[..., :3]*im[..., 3:]/255+bg*(1-im[..., 3:]/255) for im in (p, r))
        return float(np.abs(p[y0:y1, x0:x1]-r[y0:y1, x0:x1]).mean())
    shared = (p[y0:y1, x0:x1, 3] > opaque) & (r[y0:y1, x0:x1, 3] > opaque)
    assert np.any(shared), 'No shared opaque pixels in region'
    return float(np.abs(p[y0:y1, x0:x1, :3]-r[y0:y1, x0:x1, :3])[shared].mean())


def pale_pixels(image, box, min_mean=145, max_chroma=80, opaque=240):
    """Count bright, low-chroma opaque pixels inside `box`.

    The Spearman thresholds flag unpainted linen/skin fill against red wool and
    bronze. Retune per palette (a white-robed unit needs a different test) and
    keep the thresholds in the unit's metrics file.
    """
    x0, y0, x1, y1 = box
    data = _rgba(image)[y0:y1, x0:x1].astype(float)
    rgb = data[..., :3]
    pale = (rgb.mean(axis=2) > min_mean) & ((rgb.max(axis=2)-rgb.min(axis=2)) < max_chroma)
    return int((pale & (data[..., 3] > opaque)).sum())


def scale_box(box, source=256, target=160):
    return tuple(round(v*target/source) for v in box)


def flatten(image, background=CREAM):
    image = image.convert('RGBA')
    return Image.alpha_composite(Image.new('RGBA', image.size, background+(255,)), image).convert('RGB')


def comparison_sheet(entries, sizes=(256, 160, 64), background=CREAM, note=''):
    """Labelled native-size rows of RGBA images, e.g. painting / before / after.

    `entries` is a list of (label, image). Reductions are linear-light and
    premultiplied. Returns an RGB sheet; nothing is enlarged.
    """
    column = max(sizes)+16
    height = sum(size+28 for size in sizes)+8
    sheet = Image.new('RGB', (column*len(entries), height), background)
    draw = ImageDraw.Draw(sheet)
    y = 4
    for size in sizes:
        for col, (label, image) in enumerate(entries):
            draw.text((col*column+8, y), f'{label} | {size}px {note}'.strip(), fill=(40, 34, 27))
            small = resize_rgba(image.convert('RGBA'), (size, size))
            sheet.paste(flatten(small, background), (col*column+(column-size)//2, y+20))
        y += size+28
    return sheet


def compare(painting, before, after, regions=None, pale=None):
    """Before/after metrics for named regions. Images are same-size RGBA.

    `regions`: {name: box} measured for IoU and RGB error to the painting.
    `pale`: {name: box} measured for pale-pixel counts (motion poses).
    """
    report = {'whole_iou': {'before': region_iou(painting, before), 'after': region_iou(painting, after)}}
    for name, box in (regions or {}).items():
        report[name] = {'box': list(box),
                        'iou': {'before': region_iou(painting, before, box), 'after': region_iou(painting, after, box)},
                        'rgb_mae_255': {'before': region_rgb_mae(painting, before, box, background=CREAM),
                                        'after': region_rgb_mae(painting, after, box, background=CREAM)}}
    for name, box in (pale or {}).items():
        report[name] = {'box': list(box), 'pale_pixels': {'before': pale_pixels(before, box), 'after': pale_pixels(after, box)}}
    return report


def _box(text):
    name, values = text.split('=')
    box = tuple(int(v) for v in values.split(','))
    assert len(box) == 4, 'Box is name=x0,y0,x1,y1'
    return name, box


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--painting', type=Path, required=True)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--region', type=_box, action='append', default=[], help='name=x0,y0,x1,y1 (IoU and RGB error)')
    parser.add_argument('--pale', type=_box, action='append', default=[], help='name=x0,y0,x1,y1 (pale-pixel count)')
    parser.add_argument('--sheet', type=Path, help='write a native-size painting/before/after sheet')
    args = parser.parse_args()
    painting, before, after = (Image.open(p).convert('RGBA') for p in (args.painting, args.before, args.after))
    if before.size != painting.size:
        painting = resize_rgba(painting, before.size)
    print(json.dumps(compare(painting, before, after, dict(args.region), dict(args.pale)), indent=2))
    if args.sheet:
        comparison_sheet([('Painting', painting), ('Before', before), ('After', after)]).save(args.sheet)


if __name__ == '__main__':
    main()

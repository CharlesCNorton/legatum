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


def luminance(rgb):
    """Rec. 709 luma of display-referred sRGB values (0-255), as a reviewer reads it."""
    rgb = np.asarray(rgb, dtype=float)
    return rgb[..., 0]*.2126+rgb[..., 1]*.7152+rgb[..., 2]*.0722


def region_stats(image, box, opaque=240):
    """What a reviewer measures in one box: opaque pixel count, mean RGB, mean
    and 90th-percentile luminance. Compare painting and render box by box
    ("feet luminance 183 vs 141", "shield p90 161 vs 174") to turn a visual
    note into a number the next round can check.
    """
    x0, y0, x1, y1 = box
    data = _rgba(image)[y0:y1, x0:x1].astype(float)
    mask = data[..., 3] > opaque
    if not np.any(mask):
        return {'pixels': 0}
    rgb = data[..., :3][mask]
    luma = luminance(rgb)
    return {'pixels': int(mask.sum()), 'mean_rgb': [round(float(v), 1) for v in rgb.mean(axis=0)],
            'luminance_mean': round(float(luma.mean()), 1), 'luminance_p90': round(float(np.percentile(luma, 90)), 1)}


def span_width(image, y, x0=0, x1=None, threshold=128):
    """Opaque pixel count along row `y` between x0 and x1: the on-screen width
    of a thin prop (spear shaft, ankle). Thin geometry that covers under ~2 px
    at delivery size renders dark and jagged.
    """
    alpha = _rgba(image)[y, x0:x1, 3]
    return int((alpha > threshold).sum())


def spans(image, start, stop, axis='row', x0=0, x1=None, threshold=128):
    """Opaque extent of each row (or column) in [start, stop): {index: (first,
    last, count)}; rows with nothing opaque are omitted. `x0`/`x1` limit the
    search along the line, to isolate one limb or prop.
    """
    alpha = _rgba(image)[..., 3] > threshold
    if axis == 'column':
        alpha = alpha.T
    result = {}
    for index in range(start, stop):
        hits = np.flatnonzero(alpha[index, x0:x1])
        if hits.size:
            result[index] = (int(hits[0])+x0, int(hits[-1])+x0, int(hits.size))
    return result


def span_differences(painting, render, start, stop, axis='row', x0=0, x1=None, tolerance=1):
    """Where the render's outline differs from the painting's by more than
    `tolerance` px: {index: (first edge, last edge, opaque count)} as render
    minus painting. Tune form against these numbers, not by eye: the Spearman's
    first leg bulking "looked right but measured wrong" (shins 13-15 px wide
    against the painting's 9-10), and a reviewer's "shield 5% small" turned out
    to match within 1 px (Fable form lane, 2026-11-24).
    """
    a, b = spans(painting, start, stop, axis, x0, x1), spans(render, start, stop, axis, x0, x1)
    report = {}
    for index in sorted(set(a) | set(b)):
        pa, pb = a.get(index, (0, 0, 0)), b.get(index, (0, 0, 0))
        delta = tuple(q-p for p, q in zip(pa, pb))
        if max(abs(v) for v in delta) > tolerance:
            report[index] = delta
    return report


def frame_steps(frames, held_tail=2, still=.15, jump=2.5):
    """Frame-to-frame change over a clip, to spend the frame budget on motion.

    Returns the mean absolute difference (0-255) between consecutive frames,
    the largest step as a multiple of the clip median, and findings: frames
    that barely change (under `still` x median) before the allowed held tail,
    and steps over `jump` x median (a pose that teleports between two
    delivered samples). Pass lossless frames or decoded alpha, not lossy RGB.

    Spearman round-10 death, decoded alpha: steps 13.6, 8.2, 11.1, 15.1, 5.5,
    1.2, 0.03, 0.03, 0: three of ten frames spent on a pose that had already
    settled, which the art director flagged as the clip's main waste.
    """
    arrays = [_rgba(f).astype(float) for f in frames]
    steps = [float(np.abs(b-a).mean()) for a, b in zip(arrays, arrays[1:])]
    moving = sorted(step for step in steps if step > 0)
    if not moving:
        return {'steps': steps, 'max_step_over_median': 0, 'findings': ['clip does not move']}
    median = moving[len(moving)//2]
    findings = []
    last_free = len(steps)-(held_tail-1)
    quiet = [i+1 for i, step in enumerate(steps[:last_free]) if step < still*median]
    if quiet:
        findings.append(f'frames {quiet} barely change before the held tail')
    big = [i+1 for i, step in enumerate(steps) if step > jump*median]
    if big:
        findings.append(f'frames {big} jump more than {jump}x the median step')
    return {'steps': [round(step, 3) for step in steps],
            'max_step_over_median': round(max(steps)/median, 2), 'findings': findings}

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


def grid_crop(images, box, scale=8, every=4, background=CREAM):
    """Enlarge one box of several same-size images side by side with a pixel
    grid, for measuring a small region (feet, a hand) by counting pixels.

    `images` is [(label, image), ...]; `box` is (x0, y0, x1, y1). Grid lines
    fall every `every` source pixels and are labelled with source coordinates.
    The Spearman's leg problem was found on such a crop: soles 3 px low, not
    legs too wide.
    """
    x0, y0, x1, y1 = box
    w, h = (x1-x0)*scale, (y1-y0)*scale
    sheet = Image.new('RGB', ((w+24)*len(images), h+34), background)
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(images):
        left = index*(w+24)+20
        crop = flatten(image.convert('RGBA'), background).crop(box).resize((w, h), Image.Resampling.NEAREST)
        sheet.paste(crop, (left, 16))
        draw.text((left, 2), label, fill=(40, 34, 27))
        for x in range(x0-x0 % every+every, x1, every):
            draw.line((left+(x-x0)*scale, 16, left+(x-x0)*scale, 16+h), fill=(0, 0, 0))
            draw.text((left+(x-x0)*scale+2, 18+h), str(x), fill=(40, 34, 27))
        for y in range(y0-y0 % every+every, y1, every):
            draw.line((left, 16+(y-y0)*scale, left+w, 16+(y-y0)*scale), fill=(0, 0, 0))
            draw.text((left-19, 12+(y-y0)*scale), str(y), fill=(40, 34, 27))
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


def clip_report(folder):
    """Frame-step findings for each <folder>/<clip>/NN.png set (decoded cells)."""
    report = {}
    for clip in sorted(p for p in Path(folder).iterdir() if p.is_dir()):
        paths = sorted((p for p in clip.glob('*.png') if p.stem.isdecimal()), key=lambda p: int(p.stem))
        if len(paths) > 1:
            report[clip.name] = frame_steps([Image.open(p).getchannel('A').convert('RGBA') for p in paths])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--painting', type=Path)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--after', type=Path)
    parser.add_argument('--region', type=_box, action='append', default=[], help='name=x0,y0,x1,y1 (IoU and RGB error)')
    parser.add_argument('--pale', type=_box, action='append', default=[], help='name=x0,y0,x1,y1 (pale-pixel count)')
    parser.add_argument('--stats', type=_box, action='append', default=[], help='name=x0,y0,x1,y1 (pixels, mean RGB, luminance mean and p90)')
    parser.add_argument('--sheet', type=Path, help='write a native-size painting/before/after sheet')
    parser.add_argument('--rows', help='y0,y1[,x0,x1]: rows where the after outline differs from the painting by over 1 px')
    parser.add_argument('--columns', help='x0,x1[,y0,y1]: the same for columns')
    parser.add_argument('--grid', help='x0,y0,x1,y1: write an 8x gridded crop of painting and after to --sheet')
    parser.add_argument('--clips', type=Path, help='folder of decoded cells (<clip>/NN.png): report wasted and jumping frames')
    args = parser.parse_args()
    if args.clips:
        print(json.dumps(clip_report(args.clips), indent=2))
    if not args.painting:
        return
    assert args.after, '--painting needs --after (and usually --before)'
    painting, after = (Image.open(p).convert('RGBA') for p in (args.painting, args.after))
    before = Image.open(args.before).convert('RGBA') if args.before else after
    if after.size != painting.size:
        painting = resize_rgba(painting, after.size)
    report = compare(painting, before, after, dict(args.region), dict(args.pale))
    for name, box in args.stats:
        report[name] = {'box': list(box), 'painting': region_stats(painting, box),
                        'before': region_stats(before, box), 'after': region_stats(after, box)}
    for axis, text in (('row', args.rows), ('column', args.columns)):
        if text:
            v = [int(n) for n in text.split(',')]+[0, None]
            report[axis+'_span_differences_after_minus_painting'] = {
                str(k): list(d) for k, d in span_differences(painting, after, v[0], v[1], axis, v[2], v[3]).items()}
    print(json.dumps(report, indent=2))
    if args.sheet and args.grid:
        grid_crop([('Painting', painting), ('Render', after)], tuple(int(v) for v in args.grid.split(','))).save(args.sheet)
    elif args.sheet:
        comparison_sheet([('Painting', painting), ('Before', before), ('After', after)]).save(args.sheet)


if __name__ == '__main__':
    main()

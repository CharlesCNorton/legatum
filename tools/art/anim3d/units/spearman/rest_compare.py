#!/usr/bin/env python3
"""Rest compare: painting | render | 50/50 crossfade | silhouette difference, at 256 and 160 px.

  rest_compare.py RENDER.png OUT.png [--label TEXT] [--rows Y0 Y1] [--zoom OUT2.png --box x0 y0 x1 y1]

Numbers use critique.py's definitions at zero offset (IoU also at the best of
+-3 px, for information) and its spearman regions. --rows prints the opaque
spans of both images per row, the measurement the leg fit is tuned on.
In the difference panel: grey both, cyan painting only, magenta render only.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit import critique  # noqa: E402
from kit.images import resize_rgba  # noqa: E402

CREAM = (224, 215, 191)
REPO = Path(__file__).resolve().parents[5]


def flat(image):
    return Image.alpha_composite(Image.new('RGBA', image.size, CREAM + (255,)), image).convert('RGB')


def spans(mask_row):
    xs = np.flatnonzero(mask_row)
    if not len(xs):
        return []
    breaks = np.flatnonzero(np.diff(xs) > 1)
    starts = np.concatenate(([xs[0]], xs[breaks + 1]))
    ends = np.concatenate((xs[breaks], [xs[-1]]))
    return [(int(a), int(b)) for a, b in zip(starts, ends)]


def measure(painting, render):
    p, r = resize_rgba(painting, (256, 256), space='display'), resize_rgba(render, (256, 256), space='display')
    pm, _ = critique.painting_mask(p)
    rm = np.asarray(r)[:, :, 3] > 8
    best, dx, dy, _ = critique.best_iou(pm, rm)
    both = pm & rm
    p_rgb, r_rgb = np.asarray(p)[:, :, :3], np.asarray(r)[:, :, :3]
    raw = np.linalg.norm(critique.rgb_to_lab(p_rgb) - critique.rgb_to_lab(r_rgb), axis=2)
    tone = np.linalg.norm(critique.rgb_to_lab(critique.blurred_rgb(p_rgb, both)) -
                          critique.rgb_to_lab(critique.blurred_rgb(r_rgb, both)), axis=2)
    preset = json.loads((Path(critique.__file__).parent / 'presets/spearman.json').read_text())
    regions = critique.region_delta_e(raw, tone, both, {k: tuple(v) for k, v in preset['critique_regions'].items()})
    lower = (np.arange(256)[:, None] > 172) & np.ones((1, 256), bool)
    return {
        'iou_zero_offset': round(float((pm & rm).sum() / (pm | rm).sum()), 4),
        'iou_best': round(float(best), 4), 'offset': [dx, dy],
        'iou_lower_body': round(float((pm & rm & lower).sum() / ((pm | rm) & lower).sum()), 4),
        'blurred_delta_e': round(float(tone[both].mean()), 3), 'raw_delta_e': round(float(raw[both].mean()), 3),
        'regions': {k: round(v.get('mean_delta_e_blurred', -1), 2) for k, v in regions.items()},
    }, pm, rm


def sheet(painting, render, label, numbers):
    rows = []
    for size in (256, 160):
        pi, ri = resize_rgba(painting, (size, size), space='display'), resize_rgba(render, (size, size), space='display')
        p, r = flat(pi), flat(ri)
        pm, rm = np.asarray(pi)[:, :, 3] > 8, np.asarray(ri)[:, :, 3] > 8
        diff = np.full((size, size, 3), CREAM, np.uint8)
        diff[pm & rm] = (120, 116, 108)
        diff[pm & ~rm] = (0, 170, 210)
        diff[rm & ~pm] = (225, 30, 170)
        row = Image.new('RGB', (4 * size + 24, size), CREAM)
        for i, im in enumerate((p, r, Image.blend(p, r, .5), Image.fromarray(diff))):
            row.paste(im, (i * (size + 8), 0))
        rows.append(row)
    out = Image.new('RGB', (rows[0].width, 38 + 256 + 8 + 160), CREAM)
    draw = ImageDraw.Draw(out)
    draw.text((4, 4), 'painting | ' + label + ' | 50/50 crossfade | silhouette (cyan painting only, magenta render only)', fill=(40, 34, 27))
    draw.text((4, 20), f"IoU {numbers['iou_zero_offset']} (zero offset)   blurred dE {numbers['blurred_delta_e']}   " +
              '  '.join(f'{k} {v}' for k, v in numbers['regions'].items()), fill=(40, 34, 27))
    out.paste(rows[0], (0, 38))
    out.paste(rows[1], (0, 38 + 256 + 8))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('render', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--painting', type=Path, default=REPO / 'app/src/assets/units/spearman-256.png')
    ap.add_argument('--label', default='render')
    ap.add_argument('--rows', type=int, nargs=2)
    ap.add_argument('--zoom', type=Path)
    ap.add_argument('--box', type=int, nargs=4, default=[60, 170, 200, 250])
    ap.add_argument('--scale', type=int, default=5)
    args = ap.parse_args()
    painting, render = Image.open(args.painting).convert('RGBA'), Image.open(args.render).convert('RGBA')
    numbers, pm, rm = measure(painting, render)
    sheet(painting, render, args.label, numbers).save(args.out)
    if args.zoom:
        p = flat(resize_rgba(painting, (256, 256), space='display')).crop(args.box)
        r = flat(resize_rgba(render, (256, 256), space='display')).crop(args.box)
        w, h = p.size
        s = args.scale
        diff = np.full((256, 256, 3), CREAM, np.uint8)
        diff[pm & rm] = (120, 116, 108); diff[pm & ~rm] = (0, 170, 210); diff[rm & ~pm] = (225, 30, 170)
        d = Image.fromarray(diff).crop(args.box)
        out = Image.new('RGB', (4 * w * s + 24, h * s), CREAM)
        for i, im in enumerate((p, r, Image.blend(p, r, .5), d)):
            out.paste(im.resize((w * s, h * s), Image.Resampling.NEAREST), (i * (w * s + 8), 0))
        out.save(args.zoom)
    print(json.dumps(numbers))
    if args.rows:
        for y in range(args.rows[0], args.rows[1] + 1):
            print(y, 'paint', spans(pm[y]), 'render', spans(rm[y]))


if __name__ == '__main__':
    main()

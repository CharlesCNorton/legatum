#!/usr/bin/env python3
"""Painting | render | 50/50 crossfade at native 256 and 160 px, plus critique numbers.

Run with the pipeline venv (Pillow and numpy):
  look_compare.py RENDER.png OUT.png [--painting P] [--zoom OUT2.png] [--label TEXT]
The render is any transparent square PNG at the painting's camera. It is reduced
in linear light with premultiplied alpha. The numbers reuse critique.py, so they
match the round critique (IoU with a ±3 px search, mean CIE76 ΔE on the overlap).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import critique  # noqa: E402

CREAM = (224, 215, 191)
REPO = Path(__file__).resolve().parents[5]


def to_linear(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def to_srgb(c):
    return np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)


def resize_linear(image, size):
    """Area/Lanczos reduction in linear light with premultiplied alpha."""
    image = image.convert('RGBA')
    if image.size == (size, size):
        return image
    a = np.asarray(image).astype(np.float64) / 255
    rgb, alpha = to_linear(a[..., :3]) * a[..., 3:], a[..., 3]
    bands = [Image.fromarray(band.astype(np.float32), 'F').resize((size, size), Image.Resampling.LANCZOS)
             for band in (*np.moveaxis(rgb, 2, 0), alpha)]
    r, g, b, al = (np.asarray(band, dtype=np.float64) for band in bands)
    al = np.clip(al, 0, 1)
    out = np.stack([r, g, b], -1) / np.maximum(al, 1e-6)[..., None]
    out = np.clip(to_srgb(np.clip(out, 0, 1)), 0, 1)
    out[al < 1e-4] = 0
    return Image.fromarray(np.dstack([out, al]).__mul__(255).round().astype(np.uint8), 'RGBA')


def flat(image, bg=CREAM):
    base = Image.new('RGBA', image.size, bg + (255,))
    return Image.alpha_composite(base, image).convert('RGB')


def metrics(painting, render):
    p, r = resize_linear(painting, 256), resize_linear(render, 256)
    pm, _ = critique.painting_mask(p)
    rm = np.asarray(r)[:, :, 3] > 8
    iou, dx, dy, aligned = critique.best_iou(pm, rm)
    overlap = pm & aligned
    delta = np.linalg.norm(critique.rgb_to_lab(np.asarray(p)[:, :, :3]) -
                           critique.rgb_to_lab(critique.shift_array(np.asarray(r)[:, :, :3], dx, dy)), axis=2)
    # The base is a third of the overlap: also report the figure above the disc.
    rows = np.arange(256)[:, None] < 236
    return {'iou': round(float(iou), 4), 'offset': [dx, dy], 'delta_e': round(float(delta[overlap].mean()), 2),
            'delta_e_figure_rows_lt_236': round(float(delta[overlap & rows].mean()), 2),
            'delta_e_p90': round(float(np.percentile(delta[overlap], 90)), 2), 'overlap_px': int(overlap.sum())}


def sheet(painting, render, label):
    rows = []
    for size in (256, 160):
        p, r = flat(resize_linear(painting, size)), flat(resize_linear(render, size))
        row = Image.new('RGB', (3 * size + 16, size), CREAM)
        for i, im in enumerate((p, r, Image.blend(p, r, .5))):
            row.paste(im, (i * (size + 8), 0))
        rows.append(row)
    out = Image.new('RGB', (rows[0].width, 22 + 256 + 8 + 160), CREAM)
    ImageDraw.Draw(out).text((4, 5), 'painting | ' + label + ' | 50/50 crossfade   (256 px, then 160 px)', fill=(40, 34, 27))
    out.paste(rows[0], (0, 22))
    out.paste(rows[1], (0, 22 + 256 + 8))
    return out


def zoom(painting, render, box=None, scale=3):
    """Enlarged painting | render pair for the author's own inspection (nearest neighbour)."""
    p, r = flat(resize_linear(painting, 256)), flat(resize_linear(render, 256))
    if box:
        p, r = p.crop(box), r.crop(box)
    w, h = p.size
    out = Image.new('RGB', (2 * w * scale + 8, h * scale), CREAM)
    out.paste(p.resize((w * scale, h * scale), Image.Resampling.NEAREST), (0, 0))
    out.paste(r.resize((w * scale, h * scale), Image.Resampling.NEAREST), (w * scale + 8, 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('render', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--painting', type=Path, default=REPO / 'app/src/assets/units/spearman-256.png')
    ap.add_argument('--label', default='3D render')
    ap.add_argument('--zoom', type=Path)
    ap.add_argument('--box', type=int, nargs=4)
    ap.add_argument('--scale', type=int, default=3)
    args = ap.parse_args()
    painting, render = Image.open(args.painting).convert('RGBA'), Image.open(args.render).convert('RGBA')
    sheet(painting, render, args.label).save(args.out)
    if args.zoom:
        zoom(painting, render, args.box, args.scale).save(args.zoom)
    print(json.dumps(metrics(painting, render)))


if __name__ == '__main__':
    main()

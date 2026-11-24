#!/usr/bin/env python3
"""Painting | render | 50/50 crossfade at native 256 and 160 px, plus critique numbers.

Run with the pipeline venv (Pillow and numpy):
  look_compare.py RENDER.png OUT.png [--painting P] [--zoom OUT2.png] [--label TEXT]
The render is any transparent square PNG at the painting's camera. It is reduced
the way the game's painting was (display-space Lanczos, premultiplied alpha). The numbers reuse critique.py, so they
match the round critique: IoU with a ±3 px search, blurred colour at zero offset.
Legacy raw and IoU-offset values remain informational.
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


from kit.images import resize_rgba


def resize_linear(image, size):
    """Historical API name; reference-matched display-space reduction."""
    return resize_rgba(image, (size, size), space="display")


def flat(image, bg=CREAM):
    base = Image.new('RGBA', image.size, bg + (255,))
    return Image.alpha_composite(base, image).convert('RGB')


def metrics(painting, render, heat=None):
    p, r = resize_linear(painting, 256), resize_linear(render, 256)
    pm, _ = critique.painting_mask(p)
    rm = np.asarray(r)[:, :, 3] > 8
    iou, dx, dy, aligned = critique.best_iou(pm, rm)
    overlap = pm & aligned
    delta = np.linalg.norm(critique.rgb_to_lab(np.asarray(p)[:, :, :3]) -
                           critique.rgb_to_lab(critique.shift_array(np.asarray(r)[:, :, :3], dx, dy)), axis=2)
    # The base is a third of the overlap: also report the figure above the disc.
    rows = np.arange(256)[:, None] < 236
    # The ±3 px search maximises silhouette overlap only; projected paint is
    # registered at zero offset, so also report the colour error unshifted.
    plain = np.linalg.norm(critique.rgb_to_lab(np.asarray(p)[:, :, :3]) - critique.rgb_to_lab(np.asarray(r)[:, :, :3]), axis=2)
    both = pm & rm
    p_rgb, r_rgb = np.asarray(p)[:, :, :3], np.asarray(r)[:, :, :3]
    tone = np.linalg.norm(critique.rgb_to_lab(critique.blurred_rgb(p_rgb, both)) - critique.rgb_to_lab(critique.blurred_rgb(r_rgb, both)), axis=2)
    if heat is not None:
        view = np.asarray(flat(r)).copy()
        level = np.clip(plain / 40, 0, 1)[..., None]
        view = (view * (1 - level) + np.array([255, 0, 255]) * level).astype(np.uint8)
        view[~both] = (view[~both] * .35 + 150).astype(np.uint8)
        view[pm & ~rm] = (0, 170, 210)
        Image.fromarray(view).resize((768, 768), Image.Resampling.NEAREST).save(heat)
    return {'iou': round(float(iou), 4), 'offset': [dx, dy], 'delta_e': round(float(delta[overlap].mean()), 2),
            'delta_e_no_offset': round(float(plain[both].mean()), 2),
            'mean_delta_e_blurred_zero_offset': round(float(tone[both].mean()), 2),
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
    ap.add_argument('--heat', type=Path, help='ΔE heat (magenta) over the render, 3x; cyan = painting only')
    args = ap.parse_args()
    painting, render = Image.open(args.painting).convert('RGBA'), Image.open(args.render).convert('RGBA')
    sheet(painting, render, args.label).save(args.out)
    if args.zoom:
        zoom(painting, render, args.box, args.scale).save(args.zoom)
    print(json.dumps(metrics(painting, render, args.heat)))


if __name__ == '__main__':
    main()

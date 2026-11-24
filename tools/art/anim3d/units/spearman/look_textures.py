#!/usr/bin/env python3
"""Part-constrained paint textures for look.py, from the painting and an ID render.

  look_textures.py SOURCE.png ID.png OUT_DIR

The frozen rest projection samples the painting at each surface point's screen
position. Wherever the 3D silhouette and the painting disagree by a few pixels,
that reads another part's paint (cloak red on a shield rim, background on a
shoulder). This script gives every kit part its own copy of the painting in
which only pixels that belong to that part survive; everything else is painted
in from the part's own nearest pixels by push-pull diffusion. A part's hidden
and misregistered surface then continues its own colour instead of a seam.

Outputs, in source-painting pixel space (the existing frozen UVs sample them):
  front-<part>.png   full-resolution part paint, inpainted everywhere
  low-<part>.png     low-frequency local colour of the part (for unseen fills)
  palettes.json      value ramps sampled from each part's painted pixels
  assignment.png     debug view: which part owns each painted pixel
Requires Pillow and numpy only.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import critique  # noqa: E402

PARTS = ['shield', 'helmet', 'crest', 'cuirass', 'greave_l', 'greave_r', 'cloak', 'tunic', 'skirt',
         'belt', 'sandal_l', 'sandal_r', 'skin', 'spear', 'base']
ID_COLOURS = {p: (40 + 70 * (i % 4), 40 + 70 * ((i // 4) % 4), 250 - 100 * (i % 3)) for i, p in enumerate(PARTS)}
REACH = 64          # px in source space a part may claim paint beyond its 3D outline
COLOUR_SCALE = 10.  # CIE76 units that cost as much as SPACE_SCALE pixels
SPACE_SCALE = 18.


def id_in_source_space(id_image, size):
    """Sample the square ID render at each source pixel (project.py's calibration)."""
    ids = np.asarray(id_image.convert('RGBA'))
    n = ids.shape[0]
    sx, sy = np.meshgrid(np.arange(size[0]) + .5, np.arange(size[1]) + .5)
    x = (75 + (sx - 349) * 105 / 556) * n / 256
    y = (12 + (sy - 9) * 232 / 1236) * n / 256
    inside = (x >= 0) & (x < n) & (y >= 0) & (y < n)
    px = ids[np.clip(y.astype(int), 0, n - 1), np.clip(x.astype(int), 0, n - 1)]
    table = np.array([ID_COLOURS[p] for p in PARTS], dtype=np.int32)
    distance = np.abs(px[..., None, :3].astype(np.int32) - table[None, None]).sum(-1)
    index = distance.argmin(-1)
    index[(px[..., 3] < 128) | ~inside | (distance.min(-1) > 60)] = -1
    return index


def grow_distance(mask, reach):
    """Chebyshev distance to a mask, capped at reach (repeated 3x3 dilation)."""
    distance = np.full(mask.shape, reach + 1, dtype=np.float32)
    distance[mask] = 0
    current = Image.fromarray((mask * 255).astype(np.uint8))
    for step in range(1, reach + 1):
        current = current.filter(ImageFilter.MaxFilter(3))
        grown = np.asarray(current) > 0
        distance[grown & (distance > step)] = step
    return distance


def erode(mask, radius):
    if radius <= 0: return mask
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * radius + 1))) > 0


def kmeans(samples, k, seed=7):
    rng = np.random.default_rng(seed)
    centres = samples[rng.choice(len(samples), size=min(k, len(samples)), replace=False)]
    for _ in range(18):
        nearest = np.linalg.norm(samples[:, None] - centres[None], axis=2).argmin(1)
        centres = np.array([samples[nearest == i].mean(0) if np.any(nearest == i) else centres[i] for i in range(len(centres))])
    return centres


def resize_f(array, size, method=Image.Resampling.BILINEAR):
    return np.asarray(Image.fromarray(array.astype(np.float32), 'F').resize(size, method), dtype=np.float32)


def push_pull(colour, weight):
    """Fill weight==0 texels from valid ones, coarse to fine, smooth and seam-free."""
    levels = [(colour * weight[..., None], weight)]
    while min(levels[-1][1].shape) > 1:
        c, w = levels[-1]
        h, wd = (w.shape[0] + 1) // 2 * 2, (w.shape[1] + 1) // 2 * 2
        c = np.pad(c, ((0, h - w.shape[0]), (0, wd - w.shape[1]), (0, 0)))
        w = np.pad(w, ((0, h - w.shape[0]), (0, wd - w.shape[1])))
        levels.append((c.reshape(h // 2, 2, wd // 2, 2, 3).sum((1, 3)), w.reshape(h // 2, 2, wd // 2, 2).sum((1, 3))))
    result = None
    for c, w in reversed(levels):
        average = c / np.maximum(w, 1e-6)[..., None]
        if result is None:
            result = average
            continue
        size = (w.shape[1], w.shape[0])
        up = np.dstack([resize_f(result[..., i], size) for i in range(3)])
        alpha = np.clip(w, 0, 1)[..., None]
        result = average * alpha + up * (1 - alpha)
    return result


def blur_valid(colour, weight, cell):
    """Mean of valid pixels per coarse cell, defined everywhere, upsampled smooth."""
    small = (colour.shape[1] // cell, colour.shape[0] // cell)
    w = resize_f(weight, small, Image.Resampling.BOX)
    c = np.dstack([resize_f(colour[..., i] * weight, small, Image.Resampling.BOX) for i in range(3)])
    coarse = push_pull(c / np.maximum(w, 1e-6)[..., None], (w > .05).astype(np.float32))
    size = (colour.shape[1] // 4, colour.shape[0] // 4)
    return np.dstack([resize_f(coarse[..., i], size, Image.Resampling.BICUBIC) for i in range(3)])


def palette(pixels):
    """Six value steps of the part's own paint, dark to light."""
    luminance = pixels @ np.array([.2126, .7152, .0722])
    order = np.argsort(luminance)
    colours = []
    for q in (3, 16, 38, 62, 84, 97):
        lo, hi = int(len(order) * max(0, q - 4) / 100), max(int(len(order) * min(100, q + 4) / 100), 1)
        colours.append([int(round(v)) for v in pixels[order[lo:hi]].mean(0)])
    return {'positions': [.05, .20, .40, .60, .80, .95], 'colours': colours}


def main():
    source_path, id_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    source = np.asarray(Image.open(source_path).convert('RGBA')).astype(np.float32)
    rgb, alpha = source[..., :3], source[..., 3] / 255
    height, width = alpha.shape
    ids = id_in_source_space(Image.open(id_path), (width, height))
    lab = critique.rgb_to_lab(rgb).astype(np.float32)
    opaque = alpha > .85
    lightness, red, yellow = lab[..., 0], lab[..., 1], lab[..., 2]
    chroma = np.hypot(red, yellow)
    is_red = (red > 30) & (red > yellow * .9)
    is_pale = (lightness > 68) & (chroma < 33) & (red < 14)
    families = {'red': is_red | (lightness < 22), 'pale': ~is_red & (chroma < 34), 'warm': ~is_red & ~is_pale}
    family_of = {'cloak': 'red', 'crest': 'red', 'tunic': 'pale', 'skirt': 'pale', 'base': 'pale'}
    owner = np.full((height, width), -1, dtype=np.int32)
    debug = np.zeros((height, width, 3), dtype=np.uint8)
    palettes = {}
    stone_like = (lightness > 66) & (red < 14)  # cream and bright bronze overlap: the stone uses its outline
    figure = opaque & ~((ids == PARTS.index('base')) & stone_like)
    for index, part in enumerate(PARTS):
        region = ids == index
        # A part keeps the painting inside its own rest outline unless the paint
        # there plainly belongs to another material family (red on bronze, linen
        # on skin, background). Bronze, leather, skin and wood share a family:
        # colour cannot separate them, so the 3D outline decides.
        agree = region & opaque & (stone_like if part == 'base' else families[family_of.get(part, 'warm')])
        smooth = np.asarray(Image.fromarray((agree * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(3))) > 127
        valid = erode(smooth & region & opaque, 1)
        if part == 'base':
            # The stone keeps only clean stone: no feet, spear butt or their painted shadows.
            valid = valid & ~(grow_distance(figure, 16) <= 16)
        if valid.sum() < 50:
            print('too few owned pixels for', part, int(valid.sum()))
            valid = region & opaque
        owner[valid] = index
        debug[valid] = ID_COLOURS[part]
        weight = valid.astype(np.float32)
        filled = push_pull(rgb, weight)
        Image.fromarray(np.clip(filled, 0, 255).round().astype(np.uint8)).save(out / f'front-{part}.png')
        low = blur_valid(rgb, weight, 28)
        Image.fromarray(np.clip(low, 0, 255).round().astype(np.uint8)).save(out / f'low-{part}.png')
        palettes[part] = palette(rgb[valid])
        print(part, 'owned px', int(valid.sum()), 'of 3D region', int(region.sum()))
    Image.fromarray(debug).save(out / 'assignment.png')
    ids_view = np.zeros((height, width, 3), dtype=np.uint8)
    for index, part in enumerate(PARTS): ids_view[ids == index] = ID_COLOURS[part]
    Image.fromarray(ids_view).save(out / 'ids-source-space.png')
    (out / 'palettes.json').write_text(json.dumps(palettes, indent=1))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Part-constrained paint textures for look.py, from the painting and an ID render.

  look_textures.py SOURCE.png ID.png OUT_DIR [LIGHT.png]

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
         'belt', 'sandal_l', 'sandal_r', 'skin', 'spear', 'base', 'rim']
ID_COLOURS = {p: (40 + 70 * (i % 4), 40 + 70 * ((i // 4) % 4), 250 - 100 * (i % 3)) for i, p in enumerate(PARTS)}
MATERIAL = {'cloak': 'red', 'crest': 'red', 'tunic': 'linen', 'skirt': 'linen', 'shield': 'bronze', 'helmet': 'bronze',
            'cuirass': 'bronze', 'greave_l': 'bronze', 'greave_r': 'bronze'}
REACH = 64          # px in source space a part may claim paint beyond its 3D outline
COLOUR_SCALE = 10.  # CIE76 units that cost as much as SPACE_SCALE pixels
SPACE_SCALE = 18.


def register(source):
    """Resample the painting so project.py's frozen UVs land on the right pixels.

    Fitting the full painting to the game's 256 px painting gives one isotropic
    scale (5.3425 source px per 256-canvas px, centred on (627, 627) <-> (127.5,
    128); mean CIE76 0.7 with Lanczos). project.py's calibration, frozen into
    every UV, is 0.9% narrower and 0.3% shorter: up to 0.4 px off at 256, which
    alone costs about 3 CIE76 against the painting. The UVs stay; the texture moves.
    """
    k = 5.3425
    ax, ay = 105 * k / 556, 232 * k / 1236
    bx, by = 627 - 52.5 * k - 349 * ax, 627 - 116 * k - 9 * ay
    pixels = np.asarray(source.convert('RGBA')).astype(np.float32)
    pixels[..., :3] *= pixels[..., 3:] / 255
    bands = [Image.fromarray(np.ascontiguousarray(pixels[..., i]), 'F').transform(
        source.size, Image.Transform.AFFINE, (ax, 0, bx, 0, ay, by), Image.Resampling.BICUBIC) for i in range(4)]
    out = np.dstack([np.asarray(b, dtype=np.float32) for b in bands])
    alpha = np.clip(out[..., 3:], 0, 255)
    out[..., :3] = np.where(alpha > .5, out[..., :3] * 255 / np.maximum(alpha, 1e-3), 0)
    out[..., 3:] = alpha
    return np.clip(out, 0, 255)


def render_in_source_space(image, size):
    """Sample a square rest-camera render at each source pixel (project.py's calibration)."""
    pixels = np.asarray(image.convert('RGBA'))
    n = pixels.shape[0]
    sx, sy = np.meshgrid(np.arange(size[0]) + .5, np.arange(size[1]) + .5)
    x = (75 + (sx - 349) * 105 / 556) * n / 256
    y = (12 + (sy - 9) * 232 / 1236) * n / 256
    inside = (x >= 0) & (x < n) & (y >= 0) & (y < n)
    return pixels[np.clip(y.astype(int), 0, n - 1), np.clip(x.astype(int), 0, n - 1)], inside


def id_in_source_space(id_image, size):
    px, inside = render_in_source_space(id_image, size)
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


QUANTILES = (2, 9, 22, 38, 54, 70, 84, 94, 99)


def palette(pixels, light=None):
    """Value steps of the material's own paint, dark to light.

    With `light` (the look's ramp input at rest, for the same material's 3D
    surface) each step sits where that share of the surface is lit: at rest the
    unseen-surface shader then has the painting's own value distribution, and
    the key light decides where the lights and darks fall. Without it the steps
    are evenly spread.
    """
    luminance = pixels @ np.array([.2126, .7152, .0722])
    order = np.argsort(luminance)
    colours, positions = [], []
    for i, q in enumerate(QUANTILES):
        lo, hi = int(len(order) * max(0, q - 3) / 100), max(int(len(order) * min(100, q + 3) / 100), 1)
        colours.append([int(round(v)) for v in pixels[order[lo:hi]].mean(0)])
        position = float(np.percentile(light, q)) if light is not None and len(light) > 200 else .05 + .9 * i / (len(QUANTILES) - 1)
        positions.append(round(max(position, positions[-1] + .012 if positions else 0), 4))
    return {'positions': positions, 'colours': colours}


def main():
    source_path, id_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    light_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    out.mkdir(parents=True, exist_ok=True)
    source = register(Image.open(source_path))
    Image.fromarray(source.round().astype(np.uint8), 'RGBA').save(out / 'registered-source.png')
    rgb, alpha = source[..., :3], source[..., 3] / 255
    height, width = alpha.shape
    ids = id_in_source_space(Image.open(id_path), (width, height))
    light = None
    if light_path:
        # look.py --set debug=6 writes the ramp input through the display transform.
        encoded = render_in_source_space(Image.open(light_path), (width, height))[0][..., 0] / 255
        light = np.where(encoded <= .04045, encoded / 12.92, ((encoded + .055) / 1.055) ** 2.4)
    opaque = alpha > .85

    def colour_masks(pixels):
        lab = critique.rgb_to_lab(pixels).astype(np.float32)
        lightness, red, yellow = lab[..., 0], lab[..., 1], lab[..., 2]
        chroma = np.hypot(red, yellow)
        is_red = (red > 30) & (red > yellow * .9)
        is_pale = (lightness > 68) & (chroma < 33) & (red < 14)
        # Cream stone and bright bronze overlap in colour: the stone also needs its outline.
        stone_like = (lightness > 66) & (red < 14)
        flesh = (yellow < 2.1 * red) & (red > 9)
        return is_red, is_pale, stone_like, flesh, {'red': is_red | (lightness < 22), 'pale': ~is_red & (chroma < 34), 'warm': ~is_red & ~is_pale}

    is_red, is_pale, stone_like, flesh, families = colour_masks(rgb)
    strict = {'cloak': 'red', 'crest': 'red', 'shield': 'warm', 'helmet': 'warm', 'greave_l': 'warm', 'greave_r': 'warm',
              'sandal_l': 'warm', 'sandal_r': 'warm', 'spear': 'warm', 'skin': 'warm'}
    owner = np.full((height, width), -1, dtype=np.int32)
    bronze_region = np.isin(ids, [PARTS.index(q) for q, m in MATERIAL.items() if m == 'bronze'])
    debug = np.zeros((height, width, 3), dtype=np.uint8)
    palettes = {}
    stone = np.isin(ids, [PARTS.index('base'), PARTS.index('rim')])
    figure = ((ids >= 0) & ~stone) | (opaque & stone & ~stone_like)
    for index, part in enumerate(PARTS):
        region = ids == index
        # A part keeps the painting inside its own rest outline. Only rigid or
        # free-swinging parts also reject paint of another material family (red
        # cloak on a shield rim, linen on a thigh): that patch would travel with
        # the part. Torso layers keep everything: where the model's tunic sits
        # under the painted cloak collar, the collar is what belongs on it.
        family = strict.get(part)
        agree = region & opaque & (stone_like if part in ('base', 'rim') else families[family] if family else True)
        smooth = np.asarray(Image.fromarray((agree * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(3))) > 127
        valid = erode(smooth & region & opaque, 1)
        if part in ('base', 'rim'):
            # The stone keeps only clean stone: no feet, spear butt or their painted
            # shadows. Top and side are separate parts so neither bleeds into the other.
            valid = erode(opaque & stone_like & region, 2) & ~(grow_distance(figure, 16) <= 16)
        if valid.sum() < 50:
            print('too few owned pixels for', part, int(valid.sum()))
            valid = region & opaque
        owner[valid] = index
        debug[valid] = ID_COLOURS[part]
        weight = valid.astype(np.float32)
        filled = push_pull(rgb, weight)
        Image.fromarray(np.clip(filled, 0, 255).round().astype(np.uint8)).save(out / f'front-{part}.png')
        low = blur_valid(rgb, weight, 48)
        Image.fromarray(np.clip(low, 0, 255).round().astype(np.uint8)).save(out / f'low-{part}.png')
        # Ramps come from the whole painting's material, not just the part's rest
        # outline: the visible cloak is mostly its shadowed inside, but its unseen
        # back needs the lit cinnabar of the collar too.
        material = MATERIAL.get(part)
        pool, surface = valid, region
        if material == 'red': pool = valid | (opaque & is_red)
        elif material == 'linen': pool = (valid & ~is_red) | (opaque & is_pale & ~stone & (np.arange(height)[:, None] < height * .8))
        elif material == 'bronze': pool = opaque & bronze_region & families['warm']
        elif part == 'skin': pool = valid & flesh   # tan flesh, not the bronze it borders
        if material: surface = np.isin(ids, [PARTS.index(q) for q, m in MATERIAL.items() if m == material])
        palettes[part] = palette(rgb[pool], light[surface] if light is not None else None)
        print(part, 'owned px', int(valid.sum()), 'of 3D region', int(region.sum()))
    # The stone is shaded, not projected (its 3D outline is larger than the painted
    # one): keep the painting's lit top, upper and lower side and bright edge colours.
    # Measured on the painting's own disc: the side is the band above its bottom
    # edge in the central columns, the top is clean stone well above that band.
    columns = np.nonzero(opaque.any(0))[0]
    centre = range(int(np.percentile(columns, 30)), int(np.percentile(columns, 70)))
    bottom = {x: int(np.nonzero(opaque[:, x])[0].max()) for x in centre}
    band = lambda lo, hi: np.array([rgb[bottom[x] - d, x] for x in centre for d in range(lo, hi)])
    clean = erode(opaque & stone_like, 2) & ~(grow_distance(figure, 6) <= 6)
    clean[:min(bottom.values()) - 190] = False
    clean[max(bottom.values()) - 85:] = False
    top = rgb[clean]
    luminance = top @ np.array([.2126, .7152, .0722])
    mean = lambda pixels: [int(round(v)) for v in np.median(pixels, axis=0)]
    palettes['stone'] = {'top': mean(top), 'top_light': mean(top[luminance > np.percentile(luminance, 85)]),
                         'top_dark': mean(top[luminance < np.percentile(luminance, 15)]),
                         'shadow': mean(top[luminance < np.percentile(luminance, 3)]),
                         'edge': mean(band(66, 74)), 'upper': mean(band(36, 56)), 'lower': mean(band(6, 20))}
    Image.fromarray(debug).save(out / 'assignment.png')
    ids_view = np.zeros((height, width, 3), dtype=np.uint8)
    for index, part in enumerate(PARTS): ids_view[ids == index] = ID_COLOURS[part]
    Image.fromarray(ids_view).save(out / 'ids-source-space.png')
    (out / 'palettes.json').write_text(json.dumps(palettes, indent=1))


if __name__ == '__main__':
    main()

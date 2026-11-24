#!/usr/bin/env python3
"""Fit where the full-size painting sits on the game's 256 px canvas.

The projection needs the mapping canvas pixel -> source pixel. Taking it from
the two alpha bounding boxes is not good enough: box edges on a 256 px image
are whole pixels, so the scale comes out up to 1% wrong and different in x and
y. On the Spearman that put the frozen UVs up to 0.4 px off at 256 and cost
about 3 CIE76 against the painting (found by the Fable look lane, 2026-11-24).

`fit` searches one isotropic scale and an offset by comparing a display-space
Lanczos reduction of the source with the 256 px painting (the game's painting
was reduced that way). `registration_tuple` returns the value in the form
`kit/projection.py: freeze_projection` takes.

    $ANIM_ROOT/venv/bin/python -m kit.registration <slug>-source.png <slug>-256.png

Pure Pillow/numpy.
"""
import argparse
import json

import numpy as np
from PIL import Image

CANVAS = 256
CREAM = (224, 215, 191)
PAD = 256  # transparent margin so the sampled box may leave the source


def _flat(image):
    rgba = np.asarray(image.convert('RGBA'), dtype=np.float64)
    alpha = rgba[..., 3:]/255
    return rgba[..., :3]*alpha+np.array(CREAM, dtype=np.float64)*(1-alpha)


def reduce_to_canvas(padded, scale, x0, y0, canvas=CANVAS):
    """Source reduced so canvas pixel (0,0) starts at source (x0, y0) and one
    canvas pixel covers `scale` source pixels. `padded` comes from `pad`.
    """
    box = (x0+PAD, y0+PAD, x0+PAD+canvas*scale, y0+PAD+canvas*scale)
    return padded.resize((canvas, canvas), Image.Resampling.LANCZOS, box=box)


def pad(source):
    source = source.convert('RGBA')
    padded = Image.new('RGBA', (source.width+2*PAD, source.height+2*PAD))
    padded.paste(source, (PAD, PAD))
    return padded


def error(padded, reference_flat, scale, x0, y0):
    return float(np.abs(_flat(reduce_to_canvas(padded, scale, x0, y0))-reference_flat).mean())


def _box(image):
    return image.convert('RGBA').getchannel('A').point(lambda v: 255 if v > 128 else 0).getbbox()


def bbox_estimate(source, reference):
    """Starting point from the alpha boxes (the method that is NOT accurate enough)."""
    sx0, sy0, sx1, sy1 = _box(source)
    rx0, ry0, rx1, ry1 = _box(reference)
    scale = (sy1-sy0)/(ry1-ry0)
    return scale, (sx0+sx1)/2-scale*(rx0+rx1)/2, (sy0+sy1)/2-scale*(ry0+ry1)/2


# (scale step in percent, offset step in canvas pixels, scale half-range, offset half-range)
STAGES = ((.5, .5, 8, 4), (.1, .125, 3, 3), (.025, .03, 3, 3), (.006, .008, 3, 3))


def fit(source, reference):
    """Best isotropic scale and offset. Returns a dict with `scale` (source px
    per canvas px), `x0`, `y0` (source position of canvas pixel corner 0,0),
    the remaining mean absolute RGB error (0-255, on cream) and the bounding-box
    estimate with its error, for comparison. The first stage searches +-4% in
    scale and +-2 canvas px around the bounding-box estimate; about 20 s on a
    1254 px source.
    """
    assert reference.size == (CANVAS, CANVAS), 'Reference must be the 256 px painting'
    padded, target = pad(source), _flat(reference)
    scale, x0, y0 = bbox_estimate(source, reference)
    start = {'scale': scale, 'x0': x0, 'y0': y0, 'error': error(padded, target, scale, x0, y0)}
    best = (start['error'], scale, x0, y0)
    for scale_step, offset_step, scale_range, offset_range in STAGES:
        _, scale, x0, y0 = best
        for ds in range(-scale_range, scale_range+1):
            k = scale*(1+ds*scale_step/100)
            for dx in range(-offset_range, offset_range+1):
                for dy in range(-offset_range, offset_range+1):
                    # Keep the canvas centre fixed while the scale changes.
                    cx = x0+scale*CANVAS/2-k*CANVAS/2+dx*offset_step*k
                    cy = y0+scale*CANVAS/2-k*CANVAS/2+dy*offset_step*k
                    e = error(padded, target, k, cx, cy)
                    if e < best[0]:
                        best = (e, k, cx, cy)
    e, scale, x0, y0 = best
    return {'scale': scale, 'x0': x0, 'y0': y0, 'error': e, 'bbox_estimate': start,
            'source_at_canvas_centre': [x0+scale*CANVAS/2, y0+scale*CANVAS/2]}


def registration_tuple(result, canvas=CANVAS):
    """(x0, y0, px0, py0, sx, sy, canvas) for kit.projection.freeze_projection."""
    return (result['x0'], result['y0'], 0, 0, result['scale'], result['scale'], canvas)


def registered_reference(source, result):
    """The source reduced with the fitted mapping: should match the 256 painting."""
    return reduce_to_canvas(pad(source), result['scale'], result['x0'], result['y0'])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source')
    parser.add_argument('reference')
    args = parser.parse_args()
    result = fit(Image.open(args.source), Image.open(args.reference))
    result['registration'] = list(registration_tuple(result))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

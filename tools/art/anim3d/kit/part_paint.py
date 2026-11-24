"""Per-part paint from one painting: inpainting and value ramps.

The frozen projection samples the painting at each surface point's screen
position. Where the 3D outline and the painting disagree by a few pixels, a
part picks up its neighbour's paint (cloak red on a shield rim, background on
a shoulder), and that patch then travels with the part. The cure used by the
Spearman look lane: give every kit part its own copy of the painting in which
only the part's own pixels survive, and fill everything else from those pixels.
Hidden and misregistered surface then continues the part's own colour.

Unseen surfaces get a value ramp built from the same part's painted pixels, so
they carry the painting's contrast and the key light decides where the lights
fall.

Copied from units/spearman/look_textures.py on fable/unit-anim-3d-spearman-a
(239540b5), where it produced the art director's preferred materials on
2026-11-24 (spear part error 21.3 -> 5.8 CIE76). Which pixels a part owns is
unit work (an ID render plus colour-family tests); this module is the generic
arithmetic. Pure Pillow/numpy.
"""
import numpy as np
from PIL import Image, ImageFilter

QUANTILES = (2, 9, 22, 38, 54, 70, 84, 94, 99)
LUMA = np.array([.2126, .7152, .0722])


def resize_f(array, size, method=Image.Resampling.BILINEAR):
    return np.asarray(Image.fromarray(array.astype(np.float32), 'F').resize(size, method), dtype=np.float32)


def grow_distance(mask, reach):
    """Chebyshev distance to a mask, capped at reach (repeated 3x3 dilation)."""
    distance = np.full(mask.shape, reach+1, dtype=np.float32)
    distance[mask] = 0
    current = Image.fromarray((mask*255).astype(np.uint8))
    for step in range(1, reach+1):
        current = current.filter(ImageFilter.MaxFilter(3))
        grown = np.asarray(current) > 0
        distance[grown & (distance > step)] = step
    return distance


def erode(mask, radius):
    if radius <= 0:
        return mask
    return np.asarray(Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.MinFilter(2*radius+1))) > 0


def push_pull(colour, weight):
    """Fill texels where weight == 0 from valid ones, coarse to fine.

    `colour` is HxWx3 float, `weight` HxW float in [0, 1]. Valid texels keep
    their colour; holes take a smooth, seam-free continuation of the nearest
    valid colours at every scale.
    """
    levels = [(colour*weight[..., None], weight)]
    while min(levels[-1][1].shape) > 1:
        c, w = levels[-1]
        h, wd = (w.shape[0]+1)//2*2, (w.shape[1]+1)//2*2
        c = np.pad(c, ((0, h-w.shape[0]), (0, wd-w.shape[1]), (0, 0)))
        w = np.pad(w, ((0, h-w.shape[0]), (0, wd-w.shape[1])))
        levels.append((c.reshape(h//2, 2, wd//2, 2, 3).sum((1, 3)), w.reshape(h//2, 2, wd//2, 2).sum((1, 3))))
    result = None
    for c, w in reversed(levels):
        average = c/np.maximum(w, 1e-6)[..., None]
        if result is None:
            result = average
            continue
        size = (w.shape[1], w.shape[0])
        up = np.dstack([resize_f(result[..., i], size) for i in range(3)])
        alpha = np.clip(w, 0, 1)[..., None]
        result = average*alpha+up*(1-alpha)
    return result


def part_texture(rgb, owned):
    """The painting with only `owned` pixels kept and the rest inpainted."""
    return np.clip(push_pull(rgb.astype(np.float32), owned.astype(np.float32)), 0, 255)


def low_frequency(colour, weight, cell=48):
    """Mean of valid pixels per coarse cell, defined everywhere, at 1/4 size:
    the part's broad local colour, for surfaces the painting never shows.
    """
    small = (colour.shape[1]//cell, colour.shape[0]//cell)
    w = resize_f(weight, small, Image.Resampling.BOX)
    c = np.dstack([resize_f(colour[..., i]*weight, small, Image.Resampling.BOX) for i in range(3)])
    coarse = push_pull(c/np.maximum(w, 1e-6)[..., None], (w > .05).astype(np.float32))
    size = (colour.shape[1]//4, colour.shape[0]//4)
    return np.dstack([resize_f(coarse[..., i], size, Image.Resampling.BICUBIC) for i in range(3)])


def palette(pixels, light=None, quantiles=QUANTILES):
    """Value steps of a material's own paint, dark to light, for a ColorRamp.

    `pixels` is Nx3 sRGB (0-255) from the painting. With `light` (the shader's
    ramp input sampled over the same material's 3D surface at rest), each stop
    sits where that share of the surface is lit, so the unseen-surface shader
    reproduces the painting's value distribution. Without it the stops are
    evenly spread. Returns {'positions': [...], 'colours': [[r, g, b], ...]}.
    Build the ColorRamp stops in this order: elements re-sort if positions are
    assigned in place.
    """
    luminance = pixels @ LUMA
    order = np.argsort(luminance)
    colours, positions = [], []
    for i, q in enumerate(quantiles):
        lo, hi = int(len(order)*max(0, q-3)/100), max(int(len(order)*min(100, q+3)/100), 1)
        colours.append([int(round(v)) for v in pixels[order[lo:hi]].mean(0)])
        position = (float(np.percentile(light, q)) if light is not None and len(light) > 200
                    else .05+.9*i/(len(quantiles)-1))
        positions.append(round(max(position, positions[-1]+.012 if positions else 0), 4))
    return {'positions': positions, 'colours': colours}

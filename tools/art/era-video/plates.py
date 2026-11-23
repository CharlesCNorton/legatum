#!/usr/bin/env python3
"""Prepare edge-aware relief, hidden background repair, and hand-bounded color masks."""
import os
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '6'
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[3]


def guided(guide, source, radius=6, eps=0.002):
    """Grayscale guided filter; retains painted luminance edges without importing texture."""
    box = lambda x: cv2.boxFilter(x, -1, (radius * 2 + 1,) * 2)
    mean_i, mean_p = box(guide), box(source)
    a = (box(guide * source) - mean_i * mean_p) / (box(guide * guide) - mean_i * mean_i + eps)
    b = mean_p - a * mean_i
    return box(a) * guide + box(b)


def polygon(shape, points):
    mask = np.zeros(shape, np.uint8)
    cv2.fillPoly(mask, [np.array(points, np.int32)], 255)
    return mask.astype(np.float32) / 255


def feather(mask, sigma=2):
    return np.clip(cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma), 0, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=ROOT / 'app/src/assets/eras/classical-1920.jpg')
    parser.add_argument('--masters', type=Path, default=ROOT.parent / 'masters/classical')
    args = parser.parse_args()
    cv2.setNumThreads(6)
    args.masters.mkdir(parents=True, exist_ok=True)
    rgb = np.array(Image.open(args.image).convert('RGB'))
    h, w = rgb.shape[:2]
    if (w, h) != (1920, 1080):
        parser.error('The Classical masks are authored for the supplied 1920x1080 painting.')
    raw = np.array(Image.open(args.masters / 'depth16.png'), dtype=np.float32) / 65535
    if raw.shape != (h, w):
        parser.error('Depth dimensions differ from painting; rerun depth.py.')
    gray = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2GRAY)
    depth = np.clip(guided(gray, cv2.bilateralFilter(raw, 11, 0.045, 5)), 0, 1)
    Image.fromarray(np.round(depth * 65535).astype(np.uint16)).save(args.masters / 'depth-smooth16.png')
    Image.fromarray(np.round(depth * 255).astype(np.uint8)).save(args.masters / 'depth-smooth-preview.png')
    Image.fromarray(rgb).save(args.masters / 'painting.png')

    # Repair a generous 25px apron on both sides of strong depth edges. Only the
    # thin stretch-faded mesh seams ever reveal this; do not use it as a visible layer.
    spread = cv2.dilate(depth, np.ones((9, 9), np.uint8)) - cv2.erode(depth, np.ones((9, 9), np.uint8))
    discontinuities = (spread > 0.04).astype(np.uint8) * 255
    band = cv2.dilate(discontinuities, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
    # Half-resolution inpainting avoids chasing individual brush strokes and is cheaper.
    small = cv2.resize(rgb, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    small_band = cv2.resize(band, (w // 2, h // 2), interpolation=cv2.INTER_NEAREST)
    # Telea alone pulls foreground pigment into newly revealed background (dark
    # halos beside columns/people). Seed its boundary from farther-depth donors.
    # Quantized depth bins keep this bounded and deterministic, without a new model.
    small_depth = cv2.resize(depth, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    apron = cv2.dilate(small_band, np.ones((15, 15), np.uint8)) > 0
    far_depth = cv2.erode(small_depth, np.ones((61, 61), np.uint8))
    target_bin = np.clip(np.ceil((far_depth + 0.015) * 32), 1, 32).astype(np.uint8)
    seeded = small.copy()
    for level in np.unique(target_bin[apron]):
        donors = (small_depth <= level / 32) & (small_band == 0)
        if not donors.any():
            donors = small_depth <= level / 32
        nearest = distance_transform_edt(~donors, return_distances=False, return_indices=True)
        region = apron & (target_bin == level)
        seeded[region] = small[nearest[0][region], nearest[1][region]]
    repaired = cv2.inpaint(seeded, small_band, 5, cv2.INPAINT_TELEA)
    repaired = cv2.resize(repaired, (w, h), interpolation=cv2.INTER_CUBIC)
    blend = feather(band / 255, 2)[..., None]
    background = np.uint8(np.clip(rgb * (1 - blend) + repaired * blend, 0, 255))
    Image.fromarray(background).save(args.masters / 'background.png')
    Image.fromarray(band).save(args.masters / 'inpaint-band.png')

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue, sat, val = [hsv[..., i].astype(np.float32) for i in range(3)]
    blue = (hue > 88) & (hue < 119) & (sat > 38)
    water_region = polygon((h, w), [(250, 345), (565, 345), (680, 386), (820, 420),
        (837, 478), (715, 522), (665, 578), (515, 601), (367, 566), (250, 504)])
    water = feather(cv2.erode((blue * water_region).astype(np.float32), np.ones((5, 5), np.uint8)), 2)
    # Depth gates sky around temple, leaves, and the irregular distant ridgeline.
    sky_region = polygon((h, w), [(0, 0), (1919, 0), (1919, 105), (1600, 132),
        (1460, 208), (1090, 170), (920, 239), (720, 250), (592, 202), (370, 245), (0, 265)])
    sky = feather(sky_region * (depth < 0.035), 3)
    cloth = np.zeros((h, w), np.float32)
    # Conservative interiors: fixed masts/rooflines excluded, edges taper to zero.
    for points in [
        [(588, 445), (678, 451), (672, 500), (650, 526), (604, 519)],
        [(330, 452), (359, 451), (360, 481), (348, 493), (335, 486)],
        [(395, 515), (430, 517), (426, 548), (414, 558), (401, 548)],
        [(1664, 455), (1690, 465), (1688, 529), (1665, 531)],
        [(1780, 583), (1797, 586), (1799, 662), (1785, 666)],
    ]:
        cloth = np.maximum(cloth, polygon((h, w), points))
    # Allow painted folds and blue pennants, not adjoining sea or building surfaces.
    cloth = feather(cv2.erode(cloth, np.ones((5, 5), np.uint8)), 3)
    masks = {'water': water, 'sky': sky, 'cloth': cloth}
    for name, mask in masks.items():
        Image.fromarray(np.uint8(np.round(mask * 255))).save(args.masters / f'mask-{name}.png')
    overlay = rgb.astype(np.float32)
    for mask, color in [(water, (20, 215, 255)), (sky, (175, 80, 255)), (cloth, (255, 75, 45))]:
        a = mask[..., None] * 0.55
        overlay = overlay * (1 - a) + np.array(color) * a
    debug = Image.fromarray(np.uint8(overlay))
    draw = ImageDraw.Draw(debug)
    draw.rectangle((12, 12, 505, 43), fill=(25, 24, 22))
    draw.text((22, 21), 'MASKS: cyan water | violet sky | orange sails / pennants', fill='white')
    debug.save(args.masters / 'masks-overlay.png')
    # Blender ships numpy, not OpenCV/Pillow. Arrays are top-to-bottom like the PNGs.
    np.savez_compressed(args.masters / 'relief.npz',
        depth=cv2.resize(depth, (641, 361), interpolation=cv2.INTER_AREA),
        cloth=cv2.resize(cloth, (641, 361), interpolation=cv2.INTER_AREA))
    stats = {'inpaint_band_percent': float(np.mean(band > 0) * 100),
             'mask_percent': {key: float(np.mean(value > 0.2) * 100) for key, value in masks.items()},
             'mesh_grid': [641, 361], 'source': str(args.image.resolve())}
    (args.masters / 'plates.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()

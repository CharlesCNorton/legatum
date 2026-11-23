#!/usr/bin/env python3
"""Extract the Classical painting's pigment; Pillow/numpy only, never Blender.

Coordinates below refer to the unmodified 1920x1080 painting, top-left origin.
Generated masters stay outside git. The manifest records source and output hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'app/src/assets/eras/classical-1920.jpg'
PATCHES = {
    'marble': (1175, 264, 1243, 310),
    'terracotta': (1100, 516, 1210, 538),
    'quay': (940, 987, 1000, 1008),
    'foliage': (951, 668, 1009, 707),
    'timber': (615, 546, 660, 554),
    'cloth': (610, 459, 659, 512),
    'rock': (909, 350, 975, 414),
    'blue_cloth': (1660, 493, 1676, 518),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seamless(patch):
    """Keep the actual brush marks; crossfade only the tile boundary.

    Pair opposite boundary pixels, feathering inward. The interior keeps the
    source stroke direction; reflecting entire tiles would create kaleidoscopes.
    """
    tile = np.asarray(patch.resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32) / 255
    for axis in (0, 1):
        v = np.swapaxes(tile, 0, axis)
        for i in range(32):
            weight = .5 * (1 + np.cos(np.pi * i / 32))
            average = (v[i] + v[-1-i]) * .5
            v[i] = v[i] * (1-weight) + average * weight
            v[-1-i] = v[-1-i] * (1-weight) + average * weight
    return tile


def save_rgb(path, values):
    Image.fromarray(np.uint8(np.clip(values, 0, 1) * 255 + .5)).save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert('RGB')
    if source.size != (1920, 1080):
        raise ValueError(f'Patch coordinates require 1920x1080, got {source.size}')
    manifest = {'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': digest(SOURCE),
                'generator_sha256': digest(Path(__file__)),
                'license': 'CC BY 4.0; derived from Legatum Classical era painting (LICENSE-ART)',
                'patches': {}, 'files': {}}
    sheet = Image.new('RGB', (1024, 640), '#24231f')
    draw = ImageDraw.Draw(sheet)
    for i, (name, box) in enumerate(PATCHES.items()):
        crop = source.crop(box)
        tile = seamless(crop)
        # Boost the painting's own middle-frequency bristle contrast, not white noise.
        lum = tile @ np.array([.2126, .7152, .0722], dtype=np.float32)
        low = np.asarray(Image.fromarray(np.uint8(lum * 255)).filter(
            ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255
        relief = lum - low
        albedo = np.clip(tile + .55 * relief[..., None], 0, 1)
        height = np.clip(.5 + relief * 2.6, 0, 1)
        # Periodic central differences: OpenGL tangent normals (+Y), linear data.
        dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 2.8
        dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 2.8
        normal = np.stack((-dx, dy, np.ones_like(dx)), axis=-1)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        roughness = np.clip(.79 - relief * 1.3, .48, .95)
        save_rgb(args.out / f'{name}-albedo.png', albedo)
        save_rgb(args.out / f'{name}-normal.png', normal * .5 + .5)
        save_rgb(args.out / f'{name}-roughness.png', roughness)
        save_rgb(args.out / f'{name}-height.png', height)
        manifest['patches'][name] = {'crop_xyxy': box, 'tile_size': [256, 256],
                                     'mean_srgb': np.round(tile.mean(axis=(0, 1)), 4).tolist()}
        x, y = (i % 4) * 256, (i // 4) * 320
        sheet.paste(Image.fromarray(np.uint8(albedo * 255)), (x, y + 24))
        draw.text((x + 8, y + 5), name, fill='white')
        draw.text((x + 8, y + 285), str(box), fill='white')
    sheet.save(args.out / 'texture-contact.png')

    # Sky and a real painted ridge, never a procedural sine-wave mountain.
    source.crop((450, 0, 900, 205)).save(args.out / 'sky.png')
    mountain_box = (270, 185, 720, 345)
    mountain = source.crop(mountain_box).convert('RGBA')
    # Trace the original skyline, retaining the painter's rock planes beneath it.
    skyline = [(270,251),(284,249),(296,241),(308,240),(317,236),(330,239),
               (340,238),(351,240),(370,244),(388,247),(409,245),(423,247),
               (436,252),(446,252),(465,257),(476,257),(486,260),(495,257),
               (506,250),(517,249),(537,243),(548,241),(565,236),(574,234),
               (585,231),(590,224),(596,213),(603,215),(609,214),(618,217),
               (624,219),(636,220),(644,224),(654,228),(666,228),(677,233),
               (690,233),(699,232),(707,239),(720,247)]
    alpha = Image.new('L', mountain.size)
    ImageDraw.Draw(alpha).polygon(
        [(x - 270, y - 185) for x, y in skyline] + [(450, 160), (0, 160)], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.4))
    mountain.putalpha(alpha)
    # Alternating mirrored strips make a wide plate without a vertical colour seam.
    panorama = Image.new('RGBA', (1350, 160))
    for i in range(3):
        panorama.paste(mountain if i % 2 == 0 else ImageOps.mirror(mountain), (i * 450, 0))
    panorama.save(args.out / 'mountains.png')
    manifest['backdrop'] = {'sky_crop': [450, 0, 900, 205],
                            'mountain_crop': mountain_box, 'skyline_xy': skyline}

    # Fixed screen-space canvas weave, placed AFTER Kuwahara so it survives 540p.
    yy, xx = np.mgrid[:540, :960]
    warp = np.cos(2 * np.pi * (xx / 3.7 + .06 * np.sin(yy / 17)))
    weft = np.cos(2 * np.pi * (yy / 3.4 + .06 * np.sin(xx / 19)))
    weave = .94 + .027 * warp + .027 * weft + .006 * warp * weft
    save_rgb(args.out / 'canvas.png', weave)
    for path in sorted(args.out.glob('*.png')):
        manifest['files'][path.name] = digest(path)
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared {len(PATCHES)} painted materials and backdrop/canvas in {args.out}')


if __name__ == '__main__':
    main()

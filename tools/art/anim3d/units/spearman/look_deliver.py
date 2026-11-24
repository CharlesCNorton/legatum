#!/usr/bin/env python3
"""Masters, trimmed 160 px atlas, contact sheet and review movie from look.py frames.

  look_deliver.py FRAMES_DIR OUT_DIR [--tag NAME]

FRAMES_DIR holds rest.png and idle/ move/ attack/ hit/ death/ numbered PNGs
straight from look.py (no grade: the look is the painting's own pigment under
the Standard view). OUT_DIR receives:
  512/ and 256/ masters (rest.png plus every clip frame),
  atlas/spearman.webp + .json in the trimmed v2 format (delivery.py's packer and
  validator, so the byte cap, gutters, offsets and held death are checked),
  <tag>-clips-160.png (every decoded cell) and <tag>.mp4 (five clips, 2x, 8 s).
Nothing under app/ is written: the checked-in atlas stays until the lead decides.
Run from the repository root with the pipeline venv.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import delivery  # noqa: E402
from look_compare import resize_linear  # noqa: E402

CREAM = (224, 215, 191)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('frames', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--tag', default='spearman-look')
    args = ap.parse_args()
    frames, hashes = {}, {}
    for clip, (count, _, _) in delivery.CLIPS.items():
        paths = sorted((args.frames / clip).glob('[0-9][0-9].png'))
        assert len(paths) == count, f'{clip}: expected {count} frames, found {len(paths)}'
        frames[clip] = [Image.open(p).convert('RGBA') for p in paths]
        hashes.update({f'{clip}/{p.stem}': hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    assert (args.frames / 'death/08.png').read_bytes() == (args.frames / 'death/09.png').read_bytes(), 'Death source not held'
    for size in (512, 256):
        for clip, images in frames.items():
            folder = args.out / str(size) / clip
            folder.mkdir(parents=True, exist_ok=True)
            for i, im in enumerate(images):
                resize_linear(im, size).save(folder / f'{i:02}.png')
        resize_linear(Image.open(args.frames / 'rest.png'), size).save(args.out / str(size) / 'rest.png')
    # delivery.py's packer and validator, pointed at these frames and this folder.
    manifest = {'engine': 'BLENDER_EEVEE', 'device': 'GPU', 'resolution': frames['idle'][0].width, 'samples': 64}
    delivery.OUTPUT = args.out / 'atlas'
    delivery.REVIEW = args.out
    delivery.load_sources = lambda preview=False: (frames, {clip: manifest for clip in frames}, hashes)
    delivery.pack(preview=True)
    delivery.validate()
    meta = json.loads((delivery.OUTPUT / 'spearman.json').read_text())
    atlas = Image.open(delivery.OUTPUT / 'spearman.webp').convert('RGBA')
    cells = {c: [delivery.decode(meta, atlas, c, i) for i in range(n)] for c, (n, _, _) in delivery.CLIPS.items()}
    sheet = Image.new('RGB', (10 * 160, 5 * 160), CREAM)
    for row, clip in enumerate(delivery.CLIPS):
        for i, cell in enumerate(cells[clip]):
            sheet.paste(cell, (i * 160, row * 160), cell)
    sheet.save(args.out / f'{args.tag}-clips-160.png')
    big = {c: [im.resize((320, 320), Image.Resampling.NEAREST) for im in ims] for c, ims in cells.items()}
    path = args.out / f'{args.tag}.mp4'
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1600x352',
               '-framerate', '24', '-i', '-', '-an', '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p',
               '-crf', '18', '-movflags', '+faststart', str(path)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for f in range(8 * 24):
            canvas = Image.new('RGB', (1600, 352), CREAM)
            draw = ImageDraw.Draw(canvas)
            for col, (clip, (count, fps, loop)) in enumerate(delivery.CLIPS.items()):
                period = count / fps + (0 if loop else .45)
                im = big[clip][min(count - 1, int((f / 24 % period) * fps))]
                canvas.paste(im, (col * 320, 28), im)
                draw.text((col * 320 + 12, 8), f'{clip} | 160 px at 2x | Eevee painted look', fill=(40, 34, 27))
            process.stdin.write(canvas.tobytes())
    finally:
        process.stdin.close()
    assert process.wait() == 0, 'Movie encoding failed'
    report = json.loads((args.out / 'spearman-delivery.json').read_text())
    print('DELIVER', report['bytes'], 'bytes at quality', report['quality'], '|', path)


if __name__ == '__main__':
    main()

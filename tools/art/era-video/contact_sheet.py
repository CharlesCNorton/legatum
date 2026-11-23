#!/usr/bin/env python3
"""Six evenly spaced rendered frames, including endpoints; labels only on this QA sheet."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    paths = sorted(args.frames.glob('frame_[0-9][0-9][0-9][0-9].png'))
    if len(paths) < 6:
        parser.error('Need at least six rendered frames.')
    numbers = [int(path.stem.split('_')[-1]) for path in paths]
    if numbers != list(range(numbers[0], numbers[-1] + 1)):
        parser.error('Frames contain gaps; use a contiguous range.')
    chosen = [paths[round(i * (len(paths) - 1) / 5)] for i in range(6)]
    sheet = Image.new('RGB', (1440, 592), (30, 29, 26))
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(chosen):
        with Image.open(path) as source:
            if source.width * 9 != source.height * 16:
                parser.error(f'Not 16:9: {path}')
            tile = source.convert('RGB').resize((480, 270), Image.Resampling.LANCZOS)
        x, y = (i % 3) * 480, (i // 3) * 296
        sheet.paste(tile, (x, y))
        number = int(path.stem.split('_')[-1])
        draw.text((x + 12, y + 278), f'Frame {number:03d} | {(number - 1) / 24:.2f}s', fill=(225, 216, 196))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f'{args.out}: ' + ', '.join(path.name for path in chosen))


if __name__ == '__main__':
    main()

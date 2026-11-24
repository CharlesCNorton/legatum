#!/usr/bin/env python3
"""Pack, validate and review a unit's clips from a folder of rendered frames.

    cd tools/art/anim3d
    $ANIM_ROOT/venv/bin/python -m kit.deliver --slug <slug> \
        --frames <dir with idle/ move/ attack/ hit/ death/ NN.png> \
        --anchor 79.375,138.125 --out <atlas dir> --review $ANIM_ROOT/review/3d-v2 \
        --label 'CPU preview' [--grade grade.json --master unit.blend] [--round N] \
        [--reduce display]

Writes <out>/<slug>.webp and <slug>.json (atlas format v2), decoded cells to
<review>/<slug>-decoded-160/ (the layout critique.py reads) and, with --round,
<review>/<slug>-round<N>.mp4. Frames must already be graded, unless --grade is
given: then the one rest-fitted grade is applied to every frame here.

Point --out at a lane folder for CPU previews. Only a 512 px GPU pass may
write the shipped atlas in app/src/assets/units/anim/. This tool checks the
atlas contract; the unit script still owns hash/provenance checks, and nothing
here is an art PASS.
"""
import argparse
import json
from pathlib import Path

from PIL import Image

from . import atlas, grade


def load_frames(folder, clips=atlas.CLIPS, tables=None):
    frames = {}
    for clip, (count, _, _) in clips.items():
        paths = sorted((p for p in (folder/clip).glob('*.png') if p.stem.isdecimal()), key=lambda p: int(p.stem))
        assert len(paths) == count, f'{clip}: expected {count} numbered PNG frames in {folder/clip}, found {len(paths)}'
        images = [Image.open(p).convert('RGBA') for p in paths]
        assert len({im.size for im in images}) == 1 and images[0].width == images[0].height, f'{clip}: frames must be square and equal'
        frames[clip] = [grade.apply(im, tables) for im in images] if tables else images
    return frames


def run(args):
    tables = None
    if args.grade:
        assert args.master, '--grade needs --master so a stale grade is refused'
        tables = grade.load(args.grade, args.master)['luts']
    frames = load_frames(args.frames, tables=tables)
    data, metadata, quality = atlas.pack(frames, args.anchor, space=args.reduce)
    decoded = atlas.validate(data, metadata, frames, space=args.reduce)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/f'{args.slug}.webp').write_bytes(data)
    (args.out/f'{args.slug}.json').write_text(json.dumps(metadata, separators=(',', ':'))+'\n')
    atlas.save_decoded(decoded, args.review/f'{args.slug}-decoded-160')
    report = {'slug': args.slug, 'label': args.label, 'reduction': args.reduce, 'bytes': len(data), 'quality': quality,
              'frames': sum(len(v) for v in decoded.values()), 'source_px': frames['idle'][0].width,
              'validation': 'PASS (atlas contract only; not art approval)'}
    if args.round is not None:
        path = args.review/f'{args.slug}-round{args.round}.mp4'
        atlas.movie(decoded, path, args.label)
        report['movie'] = str(path)
    (args.review/f'{args.slug}-delivery.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def anchor(text):
    x, y = (float(v) for v in text.split(','))
    return x, y


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--slug', required=True)
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--anchor', type=anchor, required=True, help='ax,ay in 160 px cell pixels, shared by every frame')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--label', required=True, help="what was rendered, e.g. 'CPU preview' or 'GPU'")
    parser.add_argument('--grade', type=Path)
    parser.add_argument('--master', type=Path)
    parser.add_argument('--round', type=int)
    parser.add_argument('--reduce', choices=['linear', 'display'], default='linear',
                        help="how 160 px cells are reduced: 'display' matches how the painted tokens were made")
    print(json.dumps(run(parser.parse_args()), indent=2))


if __name__ == '__main__':
    main()

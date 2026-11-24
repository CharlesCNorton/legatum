#!/usr/bin/env python3
"""Review sheets for the fable-d motion pass, from look.py frames.

  fable_d_review.py FRAMES_DIR OUT_DIR [--tag spearman-fable-d] [--clips death,move] [--movie]

FRAMES_DIR holds idle/ move/ attack/ hit/ death/ numbered PNGs straight from
look.py. Writes <tag>-<clip>-strip.png (a 256 px row over a 160 px row on
cream), <tag>-<clip>-160.gif (looping at the clip's game rate; one-shot clips
hold their last frame) and, with --movie, <tag>.mp4 (all five clips side by
side at 160 px shown 2x, 8 s). Display-space reduction as in look_compare.py.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from look_compare import resize_linear  # noqa: E402

CREAM = (224, 215, 191)
CLIPS = {'idle': (8, 4, True), 'move': (8, 6, True), 'attack': (10, 14, False),
         'hit': (4, 12, False), 'death': (10, 4, False)}


def load(folder, size):
    return [resize_linear(Image.open(p).convert('RGBA'), size) for p in sorted(folder.glob('[0-9][0-9].png'))]


def on_cream(im):
    canvas = Image.new('RGB', im.size, CREAM)
    canvas.paste(im, (0, 0), im)
    return canvas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('frames', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--tag', default='spearman-fable-d')
    ap.add_argument('--clips', default='death,move')
    ap.add_argument('--movie', action='store_true')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for clip in args.clips.split(','):
        count, fps, loop = CLIPS[clip]
        big, small = load(args.frames/clip, 256), load(args.frames/clip, 160)
        assert len(big) == count, (clip, len(big))
        sheet = Image.new('RGB', (count*256, 256+160), CREAM)
        draw = ImageDraw.Draw(sheet)
        for i, (a, b) in enumerate(zip(big, small)):
            sheet.paste(a, (i*256, 0), a)
            sheet.paste(b, (i*256+48, 256), b)
            draw.text((i*256+4, 2), f'{clip} {i}', fill=(60, 50, 40))
        sheet.save(args.out/f'{args.tag}-{clip}-strip.png')
        cells = [on_cream(im) for im in small]
        durations = [round(1000/fps)]*count
        if not loop:
            durations[-1] = 1200
        cells[0].save(args.out/f'{args.tag}-{clip}-160.gif', save_all=True, append_images=cells[1:],
                      duration=durations, loop=0, disposal=2)
    if args.movie:
        big = {clip: [im.resize((320, 320), Image.Resampling.NEAREST) for im in load(args.frames/clip, 160)] for clip in CLIPS}
        path = args.out/f'{args.tag}.mp4'
        command = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1600x352',
                   '-framerate', '24', '-i', '-', '-an', '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p',
                   '-crf', '18', '-movflags', '+faststart', str(path)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        try:
            for f in range(8*24):
                canvas = Image.new('RGB', (1600, 352), CREAM)
                draw = ImageDraw.Draw(canvas)
                for col, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
                    # One-shot clips replay after a short settled pause; death holds 1.5 s.
                    period = count/fps+(0 if loop else 1.5 if clip == 'death' else .45)
                    im = big[clip][min(count-1, int((f/24 % period)*fps))]
                    canvas.paste(im, (col*320, 28), im)
                    draw.text((col*320+12, 8), f'{clip} | 160 px at 2x | painted look', fill=(40, 34, 27))
                process.stdin.write(canvas.tobytes())
        finally:
            process.stdin.close()
        assert process.wait() == 0, 'Movie encoding failed'
        print(path)
    print('FABLE_D_REVIEW', args.out)


if __name__ == '__main__':
    main()

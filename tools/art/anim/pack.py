#!/usr/bin/env python3
"""Pack Eevee frames with a hard size/quality floor; retain reviewable provenance."""
import argparse
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw
from units import CLIPS, UNITS

ROOT = Path(__file__).resolve().parents[3]
HOME = Path.home() / 'LegatumRuns/anim-pilot'
MAX_BYTES = 200_000
MIN_QUALITY = 60
# Uniform loop samples; attack keeps anticipation, strike and recovery. Death
# always keeps two copies of its settled pose. JSON remains row/frames/fps/loop.
PROFILES = [
    {c: list(range(n)) for c, (n, _, _) in CLIPS.items()},
    dict(idle=[0, 2, 4, 6], move=list(range(8)), attack=list(range(10)),
         hit=list(range(4)), death=[0, 2, 3, 4, 5, 6, 8, 9]),
    dict(idle=[0, 2, 4, 6], move=list(range(8)), attack=[0, 2, 3, 4, 6, 9],
         hit=[0, 1, 3], death=[0, 2, 4, 6, 8, 9]),
    dict(idle=[0, 2, 4, 6], move=[0, 2, 4, 6], attack=[0, 2, 3, 4, 6, 9],
         hit=[0, 1, 3], death=[0, 2, 4, 6, 8, 9]),
]


def clip_metadata(clip, indices, row):
    n, fps, loop = CLIPS[clip]
    # Preserve loop period / first-to-last duration after reducing frame count.
    fps *= len(indices) / n if loop else (len(indices) - 1) / (n - 1)
    return dict(row=row, frames=len(indices), fps=fps, loop=loop)


def clean_alpha(im):
    """32 coverage levels: at most 4/255 error, no thresholded hard silhouette."""
    im = im.copy()
    alpha = im.getchannel('A').point([round(round(a * 31 / 255) * 255 / 31) for a in range(256)])
    im.putalpha(alpha)
    im.paste((0, 0, 0, 0), mask=alpha.point(lambda a: 255 if a == 0 else 0))
    return im


def encode(atlas, quality):
    out = io.BytesIO()
    atlas.save(out, format='WEBP', quality=quality, method=6, exact=False)
    return out.getvalue()


def fit_atlas(frames):
    attempts = []
    for profile in PROFILES:
        atlas = Image.new('RGBA', (2560, 1280))
        for row, (clip, indices) in enumerate(profile.items()):
            for col, index in enumerate(indices):
                atlas.paste(clean_alpha(frames[clip][index]), (col * 256, row * 256))
        floor = encode(atlas, MIN_QUALITY)
        attempts.append(dict(frames=sum(map(len, profile.values())), quality=MIN_QUALITY, bytes=len(floor)))
        if len(floor) > MAX_BYTES:
            continue
        for quality in (80, 70):
            data = encode(atlas, quality)
            attempts.append(dict(frames=sum(map(len, profile.values())), quality=quality, bytes=len(data)))
            if len(data) <= MAX_BYTES:
                return data, profile, quality, attempts
        return floor, profile, MIN_QUALITY, attempts
    raise RuntimeError(f'Atlas exceeds {MAX_BYTES} bytes at quality {MIN_QUALITY}; '
                       f'no output replaced. Attempts: {attempts}')


def write_review(slug, original, frames, profile, review):
    # Source and rendered cells are all exactly 256 px. The old 256/100 px
    # comparison made correct 1:1 framing look less than half size.
    sheet = Image.new('RGB', (11 * 264, 5 * 568), '#f2ead8')
    draw = ImageDraw.Draw(sheet)
    for row, (clip, indices) in enumerate(profile.items()):
        selected = [frames[clip][i] for i in indices]
        fps = clip_metadata(clip, indices, row)['fps']
        durations = [round(1000 / fps)] * len(selected)
        if not CLIPS[clip][2]: durations[-1] = 850
        selected[0].save(review / f'{slug}-{clip}.webp', save_all=True,
                         append_images=selected[1:], duration=durations, loop=0, quality=85, method=6)
        for backdrop, colour in enumerate(('#888888', '#f2ead8')):
            y = row * 568 + backdrop * 284
            for col, (label, im) in enumerate([('source', original)] +
                                             [(f'{clip} / render {i:02}', frames[clip][i]) for i in indices]):
                x = col * 264
                draw.rectangle((x, y, x + 263, y + 283), fill=colour)
                draw.text((x + 4, y + 4), label, fill='#19160f')
                sheet.paste(im, (x + 4, y + 24), im)
    sheet.save(review / f'{slug}.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', choices=UNITS)
    ap.add_argument('--output-dir', type=Path, default=ROOT / 'app/src/assets/units/anim')
    ap.add_argument('--review-dir', type=Path, default=HOME / 'review')
    args = ap.parse_args()
    slug, output, review = args.slug, args.output_dir, args.review_dir
    frames = {clip: [Image.open(HOME / 'masters' / slug / 'frames' / clip / f'{i:02}.png').convert('RGBA')
                     for i in range(n)] for clip, (n, _, _) in CLIPS.items()}
    assert all(im.size == (256, 256) for ims in frames.values() for im in ims)
    data, profile, quality, attempts = fit_atlas(frames)
    meta = {'frame': dict(w=256, h=256, ax=UNITS[slug]['anchor'][0], ay=UNITS[slug]['anchor'][1]),
            'clips': {clip: clip_metadata(clip, indices, row) for row, (clip, indices) in enumerate(profile.items())}}
    output.mkdir(exist_ok=True, parents=True)
    review.mkdir(exist_ok=True, parents=True)
    # Never publish the failed floor candidate (the old packer left one behind).
    tmp = output / f'.{slug}.webp.tmp'
    tmp.write_bytes(data)
    tmp.replace(output / f'{slug}.webp')
    (output / f'{slug}.json').write_text(json.dumps(meta, separators=(',', ':')) + '\n')
    original = Image.open(ROOT / f'app/src/assets/units/{slug}-256.png').convert('RGBA')
    write_review(slug, original, frames, profile, review)
    report = dict(slug=slug, bytes=len(data), quality=quality, alpha_levels=32,
                  frames=sum(map(len, profile.values())), source_indices=profile, attempts=attempts)
    (review / f'{slug}-pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__': main()

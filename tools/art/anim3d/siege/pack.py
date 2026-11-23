"""Trimmed v2 atlas: 160 px logical frames, unchanged timing, lossless 8-bit alpha."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path

from PIL import Image

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters/field-cannon'
REVIEW = ROOT / 'review/3d-v2'
CLIPS = {'idle': (8, 10, True), 'move': (8, 12, True), 'attack': (10, 14, False),
         'hit': (4, 12, False), 'death': (10, 10, False)}
LIMIT = 200_000


def load_frames(folder, verify=True):
    frames, sources, hashes = {}, {}, {}
    for clip, (count, _, _) in CLIPS.items():
        render_dir = folder / ('e-' + clip)
        sources[clip] = json.loads((render_dir / 'render.json').read_text())
        if verify:
            blend = MASTER / 'clips' / (clip + '.blend')
            assert sources[clip]['blend_sha256'] == hashlib.sha256(blend.read_bytes()).hexdigest(), f'{clip}: stale render'
            info = json.loads(blend.with_suffix('.json').read_text())
            assert info['source_master_sha256'] == hashlib.sha256((MASTER / 'field-cannon.blend').read_bytes()).hexdigest(), f'{clip}: stale clip'
        for i in range(count):
            path = render_dir / f'{i:02}.png'
            frames[(clip, i)] = Image.open(path).convert('RGBA')
            hashes[f'{clip}/{i}'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return frames, sources, hashes


def compose(frames, cell=160, trim=True, width=800, reduced=False, quantize=False, resample=Image.Resampling.BICUBIC, deduplicate=True):
    """Deterministic height-sorted shelves, one transparent pixel between rectangles."""
    items, seen, aliases = [], {}, {}
    for (clip, i), image in frames.items():
        if reduced and ((clip == 'idle' and i in (2, 6)) or (clip == 'hit' and i == 2)):
            continue
        image = image.resize((cell, cell), resample)
        alpha = image.getchannel('A')
        if quantize:
            alpha = alpha.point(lambda x: round(round(x * 31 / 255) * 255 / 31))
            image.putalpha(alpha)
        # Hidden RGB carries no visible information. Never quantize delivery alpha.
        image.paste((0, 0, 0, 0), mask=alpha.point(lambda x: 255 if x == 0 else 0))
        box = alpha.getbbox() if trim else (0, 0, cell, cell)
        assert box, (clip, i, 'empty frame')
        key = (clip, i)
        digest = hashlib.sha256(image.tobytes()).hexdigest()
        if trim and deduplicate and digest in seen:
            aliases[key] = seen[digest]
            continue
        seen[digest] = key
        items.append((key, image.crop(box), box))
    if trim:
        items.sort(key=lambda item: (-item[1].height, -item[1].width, item[0]))
        x = y = row_height = used_width = 0
        placed = []
        for key, image, box in items:
            if x + image.width + 2 > width:
                x = 0
                y += row_height
                row_height = 0
            placed.append((key, image, box, x + 1, y + 1))
            x += image.width + 2
            used_width = max(used_width, x)
            row_height = max(row_height, image.height + 2)
        atlas = Image.new('RGBA', (used_width, y + row_height))
    else:
        atlas = Image.new('RGBA', (10 * cell, 5 * cell))
        placed = []
        for row, clip in enumerate(CLIPS):
            group = [item for item in items if item[0][0] == clip]
            for col, (key, image, box) in enumerate(group):
                placed.append((key, image, box, col * cell, row * cell))
    rects = {}
    for key, image, box, x, y in placed:
        atlas.paste(image, (x, y))
        rects[key] = dict(x=x, y=y, w=image.width, h=image.height, ox=box[0], oy=box[1])
    for key, original in aliases.items():
        rects[key] = dict(rects[original])
    return atlas, rects


def encode(atlas, quality, lossless=False):
    out = io.BytesIO()
    # libwebp's alpha_quality default is 100 (lossless), independent of RGB quality.
    atlas.save(out, format='WEBP', quality=quality, lossless=lossless, method=6, exact=True)
    data = out.getvalue()
    decoded = Image.open(io.BytesIO(data)).convert('RGBA')
    assert decoded.getchannel('A').tobytes() == atlas.getchannel('A').tobytes(), 'Alpha changed in encoding'
    return data


def measure(frames):
    rows = []
    for name, cell, trim, reduced, quantize, lossless in [
        ('256 grid / lossless alpha', 256, False, False, False, False),
        ('256 trim / lossless alpha', 256, True, False, False, False),
        ('256 trim / idle 6 hit 3', 256, True, True, False, False),
        ('256 trim / 32-level alpha', 256, True, False, True, False),
        ('160 grid / lossless alpha', 160, False, False, False, False),
        ('160 trim / lossless alpha', 160, True, False, False, False),
        ('128 trim / lossless alpha', 128, True, False, False, False),
        ('160 trim / lossless colour+alpha', 160, True, False, False, True),
    ]:
        atlas, rects = compose(frames, cell, trim, cell * 5, reduced, quantize, Image.Resampling.LANCZOS, deduplicate=False)
        sizes = {str(q): len(encode(atlas, q, lossless)) for q in ([75] if lossless else [75, 85])}
        rows.append(dict(option=name, frames=len(rects), dimensions=list(atlas.size), bytes=sizes))
    atlas, rects = compose(frames, deduplicate=False)
    rows.append(dict(option='160 trim / bicubic / lossless alpha', frames=len(rects), dimensions=list(atlas.size),
                     bytes={str(q): len(encode(atlas, q)) for q in [75, 80, 85]}))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--measure', action='store_true')
    parser.add_argument('--renders', type=Path, default=MASTER / 'renders')
    parser.add_argument('--report', type=Path, default=REVIEW / 'field-cannon-atlas-options.json')
    args = parser.parse_args()
    frames, sources, hashes = load_frames(args.renders, verify=not args.measure)
    if args.measure:
        report = {'source': str(args.renders), 'render_sources': sources, 'options': measure(frames)}
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report['options'], indent=2))
        return
    attempts = []
    chosen = None
    for quality in [90, 85, 80, 75]:
        candidates = []
        for width in [640, 800, 960]:
            atlas, rects = compose(frames, width=width)
            data = encode(atlas, quality)
            attempts.append(dict(quality=quality, width=width, bytes=len(data)))
            candidates.append((len(data), data, atlas, rects))
        size, data, atlas, rects = min(candidates, key=lambda item: item[0])
        if size <= LIMIT:
            chosen = (quality, data, atlas, rects)
            break
    if chosen is None:
        raise RuntimeError(f'160px/all40 atlas exceeds {LIMIT} bytes at quality 75: {attempts}; report, do not degrade')
    quality, data, atlas, rects = chosen
    meta = {'version': 2, 'atlas': {'w': atlas.width, 'h': atlas.height},
            'frame': {'w': 160, 'h': 160, 'ax': 79.375, 'ay': 138.125}, 'clips': {}}
    for clip, (count, fps, loop) in CLIPS.items():
        meta['clips'][clip] = dict(frames=count, fps=fps, loop=loop,
                                  rects=[rects[(clip, i)] for i in range(count)])
    out = Path('app/src/assets/units/anim')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'field-cannon.webp').write_bytes(data)
    (out / 'field-cannon.json').write_text(json.dumps(meta, separators=(',', ':')) + '\n')
    report = dict(bytes=len(data), quality=quality, alpha='lossless 8-bit', frames=40,
                  unique_rectangles=len({tuple(r.values()) for r in rects.values()}),
                  dimensions=list(atlas.size), resampling='bicubic (premultiplied RGBA)', attempts=attempts, render_sources=sources,
                  source_sha256=hashes, atlas_sha256=hashlib.sha256(data).hexdigest())
    (REVIEW / 'field-cannon-pack.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('render_sources', 'source_sha256')}, indent=2))


if __name__ == '__main__':
    main()

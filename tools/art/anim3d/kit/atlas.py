"""Trimmed sprite atlas: pack, decode, validate and review movie for any unit.

Generalised from the Spearman delivery (rounds 4-10). The contract is the
game's atlas format v2: 160 px logical cells, per-frame alpha trim with integer
offsets, one shared anchor, 2 px transparent gutters, WebP quality >= 75 and at
most 200,000 bytes. Validation works on the DECODED atlas, because that is what
the game draws.

Frames are RGBA Pillow images at any square master size; they are reduced in
linear light with premultiplied alpha before trimming. This module does no
hash or provenance checks: the unit's delivery script owns those (master,
grade and render manifests must be current before calling `pack`).
Pure Pillow; run with the pipeline venv. `movie` needs ffmpeg and ffprobe.
"""
import io
import json
import subprocess

from PIL import Image, ImageChops, ImageDraw

from .images import resize_rgba

# clip: (frames, fps, loops). The shared contract for every unit so far.
CLIPS = {'idle': (8, 4, True), 'move': (8, 6, True), 'attack': (10, 14, False),
         'hit': (4, 12, False), 'death': (10, 4, False)}
CELL, PAD = 160, 2
BYTE_LIMIT = 200000
QUALITIES = (95, 90, 85, 80, 75)
CREAM = (224, 215, 191)


def pack(frames, anchor, clips=CLIPS, cell=CELL, pad=PAD, byte_limit=BYTE_LIMIT,
         qualities=QUALITIES):
    """Return (webp_bytes, metadata, quality) for {clip: [RGBA frames]}.

    `anchor` is (ax, ay) in cell pixels: the point of the cell that sits on the
    hex centre, identical for every frame (Spearman: 127*160/256, 221*160/256).
    Tries qualities from high to low and raises if none fits the byte limit;
    never drops frames to fit.
    """
    metadata = {'version': 2, 'frame': {'w': cell, 'h': cell, 'ax': anchor[0], 'ay': anchor[1]},
                'clips': {}, 'frames': {}}
    rows, y = [], pad
    for row, (clip, (count, fps, loop)) in enumerate(clips.items()):
        assert len(frames[clip]) == count, f'{clip}: expected {count} frames, got {len(frames[clip])}'
        x, height, tiles = pad, 0, []
        metadata['clips'][clip] = {'row': row, 'frames': count, 'fps': fps, 'loop': loop}
        metadata['frames'][clip] = []
        for image in frames[clip]:
            image = resize_rgba(image, (cell, cell))
            box = image.getchannel('A').getbbox()
            assert box, f'{clip}: empty frame'
            tile = image.crop(box)
            metadata['frames'][clip].append(dict(x=x, y=y, w=tile.width, h=tile.height, ox=box[0], oy=box[1]))
            tiles.append((tile, x, y))
            x += tile.width+pad*2
            height = max(height, tile.height)
        rows.append((x, tiles))
        y += height+pad*2
    atlas = Image.new('RGBA', (max(row[0] for row in rows), y))
    for _, tiles in rows:
        for tile, x, ty in tiles:
            atlas.paste(tile, (x, ty))
    metadata['atlas'] = {'w': atlas.width, 'h': atlas.height}
    for quality in qualities:
        buffer = io.BytesIO()
        atlas.save(buffer, format='WEBP', quality=quality, method=6, exact=True)
        if buffer.tell() <= byte_limit:
            return buffer.getvalue(), metadata, quality
    raise RuntimeError(f'Atlas exceeds {byte_limit} bytes at quality {qualities[-1]}; keep the previous delivery and report it')


def decode(metadata, atlas, clip, index):
    """Rebuild one logical cell from the atlas image, as the game does."""
    r = metadata['frames'][clip][index]
    size = metadata['frame']['w'], metadata['frame']['h']
    cell = Image.new('RGBA', size)
    cell.paste(atlas.crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])), (r['ox'], r['oy']))
    return cell


def decode_all(metadata, webp_bytes):
    atlas = Image.open(io.BytesIO(webp_bytes)).convert('RGBA')
    return {clip: [decode(metadata, atlas, clip, i) for i in range(len(records))]
            for clip, records in metadata['frames'].items()}


def validate(webp_bytes, metadata, frames, clips=CLIPS, cell=CELL, pad=PAD,
             byte_limit=BYTE_LIMIT, held=(('death', -2, -1),)):
    """Check the decoded atlas against its source frames; return decoded cells.

    Raises AssertionError naming the first failed check: byte limit, atlas
    size, clip table, integer records, cell bounds, gutters and overlap, exact
    alpha and offsets against the reduced source, edge clipping, motion in every
    clip's source frames, opaque pixels outside records, and held frame pairs
    (`held`: (clip, i, j) pairs whose decoded alpha must be identical).
    """
    assert len(webp_bytes) <= byte_limit, f'{len(webp_bytes)} bytes exceeds {byte_limit}'
    atlas = Image.open(io.BytesIO(webp_bytes)).convert('RGBA')
    assert atlas.size == (metadata['atlas']['w'], metadata['atlas']['h'])
    assert metadata['version'] == 2 and (metadata['frame']['w'], metadata['frame']['h']) == (cell, cell)
    occupancy = Image.new('1', atlas.size)
    draw = ImageDraw.Draw(occupancy)
    decoded = {}
    for row, (clip, (count, fps, loop)) in enumerate(clips.items()):
        assert metadata['clips'][clip] == dict(row=row, frames=count, fps=fps, loop=loop), clip
        assert len(metadata['frames'][clip]) == count == len(frames[clip]), clip
        decoded[clip], sources = [], []
        for i, r in enumerate(metadata['frames'][clip]):
            x, y, w, h, ox, oy = (r[k] for k in ('x', 'y', 'w', 'h', 'ox', 'oy'))
            assert all(type(v) is int for v in r.values()), f'{clip}/{i}: non-integer record'
            assert 0 <= ox < ox+w <= cell and 0 <= oy < oy+h <= cell, f'{clip}/{i}: outside cell'
            assert pad <= x < x+w <= atlas.width-pad and pad <= y < y+h <= atlas.height-pad, f'{clip}/{i}: outside atlas'
            assert not occupancy.crop((x-pad, y-pad, x+w+pad, y+h+pad)).getbbox(), f'{clip}/{i}: overlapping crops or gutter'
            draw.rectangle((x, y, x+w-1, y+h-1), fill=1)
            tile = decode(metadata, atlas, clip, i)
            expected = resize_rgba(frames[clip][i], (cell, cell))
            assert tile.getchannel('A').tobytes() == expected.getchannel('A').tobytes(), f'{clip}/{i}: alpha/offset mismatch'
            bounds = tile.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox()
            assert bounds and min(bounds[:2]) >= 1 and max(bounds[2:]) <= cell-1, f'{clip}/{i}: figure clipped at cell edge {bounds}'
            decoded[clip].append(tile)
            sources.append(expected)
        # Motion is judged on the lossless reduced sources: lossy WebP noise
        # makes identical tiles decode differently and would pass a static clip.
        assert any(ImageChops.difference(sources[0], im).getbbox(alpha_only=False) for im in sources[1:]), f'{clip}: no motion'
    outside = ImageChops.multiply(atlas.getchannel('A'), occupancy.convert('L').point(lambda v: 255-v))
    assert not outside.getbbox(), 'Opaque pixels in gutters'
    for clip, i, j in held:
        assert decoded[clip][i].getchannel('A').tobytes() == decoded[clip][j].getchannel('A').tobytes(), f'{clip}: frames {i} and {j} are not held'
    return decoded


def save_decoded(decoded, folder):
    """Write decoded cells as <folder>/<clip>/NN.png (the layout critique.py reads)."""
    for clip, cells in decoded.items():
        (folder/clip).mkdir(parents=True, exist_ok=True)
        for i, tile in enumerate(cells):
            tile.save(folder/clip/f'{i:02}.png')


def movie(decoded, path, label, clips=CLIPS, seconds=8, scale=2, background=CREAM, pause=.45):
    """Five clips side by side on cream, H.264 yuv420p, 24 fps; verified with ffprobe.

    `decoded` comes from `validate`/`decode_all`, so the movie shows delivered
    pixels. Non-looping clips replay after a short settled pause. `label` must
    say what was rendered, e.g. 'CPU preview' or 'GPU'.
    """
    cell = next(iter(decoded.values()))[0].width
    side = cell*scale
    width, height = side*len(clips), side+32
    big = {c: [im.resize((side, side), Image.Resampling.NEAREST) for im in cells] for c, cells in decoded.items()}
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
               '-video_size', f'{width}x{height}', '-framerate', '24', '-i', '-', '-an',
               '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', '-crf', '18',
               '-movflags', '+faststart', str(path)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for f in range(seconds*24):
            canvas = Image.new('RGB', (width, height), background)
            draw = ImageDraw.Draw(canvas)
            for col, (clip, (count, fps, loop)) in enumerate(clips.items()):
                period = count/fps+(0 if loop else pause)
                index = min(count-1, int((f/24 % period)*fps))
                canvas.paste(big[clip][index], (col*side, 28), big[clip][index])
                draw.text((col*side+12, 8), f'{clip} | {cell} px at {scale}x | {label}', fill=(40, 34, 27))
            process.stdin.write(canvas.tobytes())
    finally:
        process.stdin.close()
    assert process.wait() == 0, 'Movie encoding failed'
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    stream = info['streams'][0]
    assert (stream['codec_name'], stream['pix_fmt'], stream['width'], stream['height'], int(stream['nb_frames'])) == ('h264', 'yuv420p', width, height, seconds*24)
    return info

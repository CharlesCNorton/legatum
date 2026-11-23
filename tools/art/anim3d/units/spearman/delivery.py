"""Trimmed 160px delivery, master export and decoded five-clip GPU review movie."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
MASTER = ROOT/'masters/spearman-3d-v2'
REVIEW = ROOT/'review/3d-v2'
OUTPUT = Path('app/src/assets/units/anim')
CLIPS = {'idle': (8, 10, True), 'move': (8, 12, True), 'attack': (10, 14, False),
         'hit': (4, 12, False), 'death': (10, 10, False)}
CELL, PAD = 160, 2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources(preview=False):
    master_hash = digest(MASTER/'spearman.blend')
    grade = MASTER/'painting-grade.json'
    grade_data = json.loads(grade.read_text())
    assert grade_data['master_sha256'] == master_hash, 'Stale grade'
    assert grade_data['reference_sha256'] == digest(Path('app/src/assets/units/spearman-256.png'))
    frames, manifests, hashes = {}, {}, {}
    for clip, (count, _, _) in CLIPS.items():
        folder = MASTER/'renders'/('e-'+clip)
        data = json.loads((folder/'render.json').read_text())
        blend = MASTER/'clips'/clip/(clip+'.blend')
        assert data['blend_sha256'] == digest(blend), f'{clip}: stale render'
        assert json.loads((blend.parent/'clip.json').read_text())['source_master_sha256'] == master_hash
        assert data['grade_sha256'] == digest(grade), f'{clip}: stale grade'
        assert preview or (data['resolution'] == 512 and data['device'] == 'GPU'), 'Finals require 512px GPU masters'
        manifests[clip] = data
        frames[clip] = []
        for i in range(count):
            path = folder/f'{i:02}.png'
            im = Image.open(path).convert('RGBA')
            assert im.size == (data['resolution'],)*2
            frames[clip].append(im)
            hashes[f'{clip}/{i:02}'] = digest(path)
    assert len({(m['engine'], m['device'], m['resolution'], m['samples']) for m in manifests.values()}) == 1, 'Mixed rendering settings'
    rest = json.loads((MASTER/'renders/c/render.json').read_text())
    assert rest['blend_sha256'] == master_hash and rest['grade_sha256'] == digest(grade)
    assert (rest['engine'], rest['device'], rest['resolution'], rest['samples']) == tuple(manifests['idle'][k] for k in ['engine', 'device', 'resolution', 'samples']), 'Rest and clip settings differ'
    return frames, manifests, hashes


def pack(preview=False):
    source, manifests, hashes = load_sources(preview)
    rows, metadata = [], {'version': 2, 'frame': {'w': CELL, 'h': CELL, 'ax': 127*CELL/256, 'ay': 221*CELL/256}, 'clips': {}, 'frames': {}}
    y = PAD
    for row, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
        x, height, tiles = PAD, 0, []
        metadata['clips'][clip] = {'row': row, 'frames': count, 'fps': fps, 'loop': loop}
        metadata['frames'][clip] = []
        for im in source[clip]:
            im = im.resize((CELL, CELL), Image.Resampling.LANCZOS)
            # Keep real alpha, including thin spear edges, without quantization.
            box = im.getchannel('A').getbbox()
            assert box, f'{clip}: empty source frame'
            tile = im.crop(box)
            record = dict(x=x, y=y, w=tile.width, h=tile.height, ox=box[0], oy=box[1])
            metadata['frames'][clip].append(record)
            tiles.append((tile, x, y))
            x += tile.width+PAD*2
            height = max(height, tile.height)
        rows.append((x, tiles))
        y += height+PAD*2
    atlas = Image.new('RGBA', (max(row[0] for row in rows), y))
    for _, tiles in rows:
        for im, x, y in tiles:
            atlas.paste(im, (x, y))
    metadata['atlas'] = {'w': atlas.width, 'h': atlas.height}
    for quality in [95, 90, 85, 80, 75]:
        buffer = io.BytesIO()
        atlas.save(buffer, format='WEBP', quality=quality, method=6, exact=True)
        if buffer.tell() <= 200000:
            break
    else:
        raise RuntimeError('Atlas exceeds 200000 bytes at quality 75; retain previous delivery')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/'spearman.webp').write_bytes(buffer.getvalue())
    (OUTPUT/'spearman.json').write_text(json.dumps(metadata, separators=(',', ':'))+'\n')
    report = {'preview': preview, 'bytes': buffer.tell(), 'quality': quality, 'frames': 40,
              'atlas_sha256': digest(OUTPUT/'spearman.webp'), 'metadata_sha256': digest(OUTPUT/'spearman.json'),
              'source_sha256': hashes, 'render_sources': manifests}
    (REVIEW/'spearman-delivery.json').write_text(json.dumps(report, indent=2)+'\n')
    # Never label an upscaled CPU preview a 512px master.
    if not preview:
        export = ROOT/'masters/spearman'
        for size in [512, 256]:
            for clip, images in source.items():
                directory = export/str(size)/clip
                directory.mkdir(parents=True, exist_ok=True)
                for i, im in enumerate(images):
                    im.resize((size, size), Image.Resampling.LANCZOS).save(directory/f'{i:02}.png')
            Image.open(MASTER/'renders/c/three-quarter.png').resize((size, size), Image.Resampling.LANCZOS).save(export/str(size)/'rest.png')
        (export/'delivery.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PACK', report['bytes'], 'bytes, quality', quality, '40 frames; preview:', preview)


def decode(meta, atlas, clip, index):
    r = meta['frames'][clip][index]
    cell = Image.new('RGBA', (CELL, CELL))
    cell.paste(atlas.crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])), (r['ox'], r['oy']))
    return cell


def validate():
    meta = json.loads((OUTPUT/'spearman.json').read_text())
    report = json.loads((REVIEW/'spearman-delivery.json').read_text())
    assert report['atlas_sha256'] == digest(OUTPUT/'spearman.webp')
    assert report['metadata_sha256'] == digest(OUTPUT/'spearman.json')
    assert 75 <= report['quality'] <= 100 and report['bytes'] == (OUTPUT/'spearman.webp').stat().st_size <= 200000
    source, _, hashes = load_sources(report['preview'])
    assert hashes == report['source_sha256']
    atlas = Image.open(OUTPUT/'spearman.webp').convert('RGBA')
    assert atlas.size == (meta['atlas']['w'], meta['atlas']['h'])
    assert meta['version'] == 2 and meta['frame'] == {'w': 160, 'h': 160, 'ax': 79.375, 'ay': 138.125}
    occupancy = Image.new('1', atlas.size)
    draw = ImageDraw.Draw(occupancy)
    decoded = {}
    for row, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
        assert meta['clips'][clip] == dict(row=row, frames=count, fps=fps, loop=loop)
        assert len(meta['frames'][clip]) == count
        decoded[clip] = []
        for i, r in enumerate(meta['frames'][clip]):
            x, y, w, h, ox, oy = (r[k] for k in ['x', 'y', 'w', 'h', 'ox', 'oy'])
            assert all(type(v) is int for v in r.values())
            assert 0 <= ox < ox+w <= CELL and 0 <= oy < oy+h <= CELL
            assert PAD <= x < x+w <= atlas.width-PAD and PAD <= y < y+h <= atlas.height-PAD
            box = (x-PAD, y-PAD, x+w+PAD, y+h+PAD)
            assert not occupancy.crop(box).getbbox(), f'{clip}/{i}: overlapping crops or gutter'
            draw.rectangle((x, y, x+w-1, y+h-1), fill=1)
            cell = decode(meta, atlas, clip, i)
            expected = source[clip][i].resize((CELL, CELL), Image.Resampling.LANCZOS)
            assert cell.getchannel('A').tobytes() == expected.getchannel('A').tobytes(), f'{clip}/{i}: alpha/offset mismatch'
            bounds = cell.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox()
            assert bounds and min(bounds[:2]) >= 1 and max(bounds[2:]) <= CELL-1, f'{clip}/{i}: clipping {bounds}'
            decoded[clip].append(cell)
        assert any(ImageChops.difference(decoded[clip][0], im).getbbox(alpha_only=False) for im in decoded[clip][1:]), f'{clip}: no motion'
    assert not ImageChops.multiply(atlas.getchannel('A'), occupancy.convert('L').point(lambda v: 255-v)).getbbox(), 'Opaque padding'
    terminal = MASTER/'renders/e-death'
    assert (terminal/'08.png').read_bytes() == (terminal/'09.png').read_bytes(), 'Death source not held'
    assert decoded['death'][-1].getchannel('A').tobytes() == decoded['death'][-2].getchannel('A').tobytes()
    sheet = Image.new('RGB', (5*320, 350), (224, 215, 191))
    d = ImageDraw.Draw(sheet)
    for i, clip in enumerate(CLIPS):
        im = decoded[clip][len(decoded[clip])//2].resize((320, 320), Image.Resampling.NEAREST)
        sheet.paste(im, (i*320, 26), im); d.text((i*320+12, 8), clip, fill=(40, 34, 27))
    sheet.save(REVIEW/'spearman-g-decoded-atlas.png')
    (REVIEW/'spearman-validation.json').write_text(json.dumps({'status': 'PASS', 'frames': 40, 'bytes': report['bytes'], 'quality': report['quality'], 'preview': report['preview']}, indent=2)+'\n')
    print('VALIDATE PASS: current hashes, 40 frames, clips, trim offsets, exact alpha, gutters, bounds, motion, held death, size and quality')


def movie():
    meta = json.loads((OUTPUT/'spearman.json').read_text())
    atlas = Image.open(OUTPUT/'spearman.webp').convert('RGBA')
    report = json.loads((REVIEW/'spearman-delivery.json').read_text())
    label = 'CPU preview' if report['preview'] else 'GPU'
    frames = {c: [decode(meta, atlas, c, i).resize((320, 320), Image.Resampling.NEAREST) for i in range(n)] for c, (n, _, _) in CLIPS.items()}
    path = REVIEW/f'spearman-round{os.environ.get("ROUND", "4")}.mp4'
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '1600x352', '-framerate', '24', '-i', '-', '-an', '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', '-crf', '18', '-movflags', '+faststart', str(path)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for f in range(8*24):
            canvas = Image.new('RGB', (1600, 352), (224, 215, 191)); draw = ImageDraw.Draw(canvas)
            for col, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
                # Non-loop gameplay clips replay with a short settled pause in review.
                period = count/fps+(0 if loop else .45)
                index = min(count-1, int((f/24 % period)*fps))
                im = frames[clip][index]
                canvas.paste(im, (col*320, 28), im)
                draw.text((col*320+12, 8), f'{clip} | 160 px at 2x | {label}', fill=(40, 34, 27))
            process.stdin.write(canvas.tobytes())
    finally:
        process.stdin.close()
    assert process.wait() == 0, 'Movie encoding failed'
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    stream = info['streams'][0]
    assert (stream['codec_name'], stream['pix_fmt'], stream['width'], stream['height'], int(stream['nb_frames'])) == ('h264', 'yuv420p', 1600, 352, 192)
    assert abs(float(info['format']['duration'])-8) < .05
    (REVIEW/'spearman-movie.json').write_text(json.dumps(info, indent=2)+'\n')
    print('MOVIE', path, '192 frames / 8 seconds / five simultaneous clips')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['pack', 'validate', 'movie'])
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    if args.stage == 'pack': pack(args.preview)
    elif args.stage == 'validate': validate()
    else: movie()

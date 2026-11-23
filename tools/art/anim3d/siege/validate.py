"""Validate v2 atlas by reconstructing logical frames and comparing source alpha."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from pack import CLIPS, LIMIT, MASTER, REVIEW, load_frames


def reconstruct(atlas, rect, cell):
    x, y, w, h, ox, oy = [rect[k] for k in ('x', 'y', 'w', 'h', 'ox', 'oy')]
    assert all(isinstance(v, int) for v in (x, y, w, h, ox, oy))
    assert w > 0 and h > 0 and 0 <= x <= atlas.width - w and 0 <= y <= atlas.height - h
    assert 0 <= ox <= cell - w and 0 <= oy <= cell - h
    frame = Image.new('RGBA', (cell, cell))
    # No alpha mask in paste: alpha is copied, never multiplied a second time.
    frame.paste(atlas.crop((x, y, x+w, y+h)), (ox, oy))
    return frame


def main():
    out = Path('app/src/assets/units/anim')
    data = (out / 'field-cannon.webp').read_bytes()
    meta = json.loads((out / 'field-cannon.json').read_text())
    report = json.loads((REVIEW / 'field-cannon-pack.json').read_text())
    atlas = Image.open(out / 'field-cannon.webp').convert('RGBA')
    assert meta['version'] == 2 and atlas.size == (meta['atlas']['w'], meta['atlas']['h'])
    assert len(data) <= LIMIT and report['quality'] >= 75 and report['alpha'] == 'lossless 8-bit'
    assert hashlib.sha256(data).hexdigest() == report['atlas_sha256']
    assert meta['frame'] == dict(w=160, h=160, ax=79.375, ay=138.125)
    source, _, hashes = load_frames(MASTER / 'renders')
    assert hashes == report['source_sha256'], 'Source frames changed since pack'
    occupied = Image.new('L', atlas.size); draw = ImageDraw.Draw(occupied)
    boxes, findings, shared = {}, [], {}
    sheet = Image.new('RGB', (10*160, 5*160), '#ddd3ba')
    for row, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
        info = meta['clips'][clip]
        assert (info['frames'], info['fps'], info['loop']) == (count, fps, loop)
        assert len(info['rects']) == count
        frames = []
        for i, rect in enumerate(info['rects']):
            frame = reconstruct(atlas, rect, 160)
            x, y, w, h = [rect[k] for k in ('x', 'y', 'w', 'h')]
            expected = source[(clip, i)].resize((160, 160), Image.Resampling.BICUBIC)
            signature = tuple(rect[k] for k in ('x', 'y', 'w', 'h', 'ox', 'oy'))
            if signature in shared:
                assert shared[signature] == expected.tobytes(), 'Shared rectangle has differing source frames'
            else:
                assert not occupied.crop((x, y, x+w, y+h)).getbbox(), 'Overlapping atlas rectangles'
                draw.rectangle((x, y, x+w-1, y+h-1), fill=255)
                shared[signature] = expected.tobytes()
            assert frame.getchannel('A').tobytes() == expected.getchannel('A').tobytes(), f'{clip}/{i}: alpha or offset drift'
            box = frame.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox()
            assert box
            boxes[f'{clip}/{i}'] = box
            if min(box[:2]) < 1 or max(box[2:]) > 159:
                findings.append(f'{clip}/{i}: clipping margin {box}')
            sheet.paste(frame, (i*160, row*160), frame)
            frames.append(frame)
        assert any(ImageChops.difference(frames[0], f).getbbox(alpha_only=False) for f in frames[1:]), f'{clip}: no motion'
        if clip == 'death':
            assert frames[-1].tobytes() == frames[-2].tobytes(), 'Decoded death hold changed'
    outside = ImageChops.multiply(atlas.getchannel('A'), ImageChops.invert(occupied))
    assert not outside.getbbox(), 'Nontransparent atlas padding'
    assert source[('death', 8)].tobytes() == source[('death', 9)].tobytes(), 'Terminal source pixels differ'
    sheet.save(REVIEW / 'field-cannon-g-decoded-atlas.png')
    delivery = Image.new('RGB', (816, 380), '#e0d7bf'); labels = ImageDraw.Draw(delivery)
    examples = [('Painting', Image.open('app/src/assets/units/field-cannon-256.png').convert('RGBA')),
                ('Rendered 3D', source[('idle', 0)]),
                ('Decoded 160px atlas', reconstruct(atlas, meta['clips']['idle']['rects'][0], 160))]
    for index, (label, frame) in enumerate(examples):
        x = 8 + 272 * index
        labels.text((x, 10), label, fill='#28221b')
        large = frame.resize((256, 256), Image.Resampling.LANCZOS)
        small = frame.resize((64, 64), Image.Resampling.LANCZOS)
        delivery.paste(large, (x, 36), large); delivery.paste(small, (x + 96, 302), small)
    delivery.save(REVIEW / 'field-cannon-g-delivery.png')
    (REVIEW / 'field-cannon-validation.json').write_text(json.dumps(dict(contract='PASS' if not findings else 'FAIL', bounds=boxes, findings=findings), indent=2))
    print('PASS: v2 rectangles/offsets, all 40 frames, exact alpha, anchor, padding, motion, held death, provenance, quality and byte cap')
    for finding in findings:
        print('FAIL:', finding)
    raise SystemExit(bool(findings))


if __name__ == '__main__':
    main()

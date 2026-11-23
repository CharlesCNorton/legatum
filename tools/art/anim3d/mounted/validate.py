"""Validate decoded trimmed delivery and bind it to current masters; not art approval."""
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageChops
from pack import CLIPS

root = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
p = Path('app/src/assets/units/anim')
meta = json.loads((p / 'horseman.json').read_text())
report = json.loads((root / 'review/3d-v2/horseman-pack.json').read_text())
im = Image.open(p / 'horseman.webp').convert('RGBA')
assert hashlib.sha256((p / 'horseman.webp').read_bytes()).hexdigest() == report['atlas_sha256']
assert hashlib.sha256((p / 'horseman.json').read_bytes()).hexdigest() == report['metadata_sha256']
assert im.size == (meta['atlas']['w'], meta['atlas']['h'])
assert (p / 'horseman.webp').stat().st_size <= 200000 and report['quality'] >= 75
assert meta['frame'] == {'w': 160, 'h': 160, 'ax': 79, 'ay': 138}
assert meta['version'] == 2 and meta['layout'] == 'trimmed-rows'
findings, boxes, occupied = [], {}, []
for row, (clip, (count, fps, loop)) in enumerate(CLIPS.items()):
    c = meta['clips'][clip]
    assert (c['row'], c['frames'], c['fps'], c['loop']) == (row, count, fps, loop)
    assert len(c['rects']) == count
    frames = []
    for i, r in enumerate(c['rects']):
        x, y, w, h, ox, oy = (r[k] for k in ('x', 'y', 'w', 'h', 'ox', 'oy'))
        assert 0 <= ox < ox+w <= 160 and 0 <= oy < oy+h <= 160
        assert 0 < x < x+w < im.width and 0 < y < y+h < im.height
        rect = (x, y, x+w, y+h)
        assert all(rect[2] <= a or b <= x or rect[3] <= c0 or d <= y for a,c0,b,d in occupied), 'Overlapping atlas frames'
        occupied.append(rect)
        tile = im.crop(rect)
        f = Image.new('RGBA', (160, 160)); f.paste(tile, (ox, oy))
        box = f.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox()
        assert box, f'{clip}/{i} empty'
        boxes[f'{clip}/{i}'] = box
        if box[0] < 1 or box[1] < 1 or box[2] > 159 or box[3] > 159:
            findings.append(f'{clip}/{i}: clipping margin {box}')
        source = root / 'masters/horseman-3d/renders' / ('e-'+clip) / f'{i:02}.png'
        assert hashlib.sha256(source.read_bytes()).hexdigest() == report['source_sha256'][f'{clip}/{i}']
        expected = Image.open(source).convert('RGBA').resize((160,160), Image.Resampling.LANCZOS)
        assert ImageChops.difference(expected.getchannel('A'), f.getchannel('A')).getextrema()[1] <= 4, 'Alpha error exceeds 4/255'
        expected_alpha=expected.getchannel('A').point(lambda a: round(round(a*31/255)*255/31))
        assert expected_alpha.tobytes()==f.getchannel('A').tobytes(), 'Trim reconstruction changed quantized alpha'
        frames.append(f)
    assert any(ImageChops.difference(frames[0], f).getbbox(alpha_only=False) for f in frames[1:]), f'{clip} has no motion'
    if clip == 'death':
        assert frames[-1].getchannel('A').tobytes() == frames[-2].getchannel('A').tobytes(), 'Death silhouette not held'
terminal = root / 'masters/horseman-3d/renders/e-death'
assert Image.open(terminal/'08.png').convert('RGBA').tobytes() == Image.open(terminal/'09.png').convert('RGBA').tobytes()
(root/'review/3d-v2/horseman-validation.json').write_text(json.dumps({'contract': 'FAIL' if findings else 'PASS', 'bounds': boxes, 'findings': findings}, indent=2))
print(f'VALIDATE: 40 frames, exact 32-level trim alpha reconstruction, motion, held death, quality {report["quality"]}, {report["bytes"]} bytes; {len(findings)} findings')
for finding in findings: print('FAIL:', finding)
raise SystemExit(bool(findings))

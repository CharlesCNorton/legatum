"""Trim 160px frames into clip rows; preserve all samples and quality >=75."""
import hashlib
import io
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
M = ROOT / 'masters/horseman-3d'
R = ROOT / 'review/3d-v2'
CLIPS = {'idle': (8, 10, True), 'move': (8, 12, True), 'attack': (10, 14, False),
         'hit': (4, 12, False), 'death': (10, 10, False)}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    out = Path('app/src/assets/units/anim')
    out.mkdir(parents=True, exist_ok=True)
    meta = {'version': 2, 'layout': 'trimmed-rows', 'frame': {'w': 160, 'h': 160, 'ax': 79, 'ay': 138}, 'clips': {}}
    hashes, renders, tiles = {}, {}, []
    y, width = 0, 0
    grade_hash = sha(M / 'grade.json')
    for row, (clip, (n, fps, loop)) in enumerate(CLIPS.items()):
        folder = M / 'renders' / ('e-' + clip)
        render = json.loads((folder / 'render.json').read_text())
        assert render.get('grade_sha256') == grade_hash, 'Rerender every clip after rest grade changes'
        assert render['blend_sha256'] == sha(M / 'clips' / (clip + '.blend')), f'Stale clip: {clip}'
        renders[clip] = render
        rects, x, height = [], 0, 0
        for i in range(n):
            path = folder / f'{i:02}.png'
            im = Image.open(path).convert('RGBA').resize((160, 160), Image.Resampling.LANCZOS)
            # Quantize alpha to 32 levels (maximum error 4/255); RGB is unchanged.
            im.putalpha(im.getchannel('A').point(lambda a: round(round(a*31/255)*255/31)))
            im.paste((0,0,0,0),mask=im.getchannel('A').point(lambda a: 255 if a==0 else 0))
            box = im.getchannel('A').getbbox()
            assert box, f'Empty frame {clip}/{i}'
            tile = im.crop(box)
            rect = dict(x=x+1, y=y+1, w=tile.width, h=tile.height, ox=box[0], oy=box[1])
            rects.append(rect)
            tiles.append((tile, rect))
            x += tile.width + 2
            height = max(height, tile.height + 2)
            hashes[f'{clip}/{i}'] = sha(path)
        meta['clips'][clip] = dict(row=row, frames=n, fps=fps, loop=loop, rects=rects)
        y += height
        width = max(width, x)
    assert len({r['engine'] for r in renders.values()}) == 1, 'Mixed engines'
    assert len({r['device'] for r in renders.values()}) == 1, 'Mixed devices'
    atlas = Image.new('RGBA', (width, y))
    for tile, rect in tiles:
        atlas.paste(tile, (rect['x'], rect['y']))
    for quality in [90, 85, 80, 75]:
        stream = io.BytesIO()
        atlas.save(stream, format='WEBP', quality=quality, method=6, exact=True)
        data = stream.getvalue()
        print(f'WebP quality {quality}: {len(data)} bytes')
        if len(data) <= 200000:
            break
    else:
        raise RuntimeError('40 frames exceed 200 KB at quality 75; delivery was not replaced')
    meta['atlas'] = {'w': width, 'h': y}
    (out / 'horseman.webp').write_bytes(data)
    (out / 'horseman.json').write_text(json.dumps(meta, separators=(',', ':')) + '\n')
    report = dict(bytes=len(data), quality=quality, alpha_levels=32, frames=40,
                  renders=renders, source_sha256=hashes, atlas_sha256=hashlib.sha256(data).hexdigest(),
                  metadata_sha256=sha(out / 'horseman.json'))
    (R / 'horseman-pack.json').write_text(json.dumps(report, indent=2))
    decoded=Image.open(io.BytesIO(data)).convert('RGBA')
    r=meta['clips']['idle']['rects'][0]
    token=Image.new('RGBA',(160,160))
    token.paste(decoded.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
    source=Image.open('app/src/assets/units/horseman-256.png').convert('RGBA')
    raw=Image.open(M/'renders/e-idle/00.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
    sheet=Image.new('RGB',(816,380),(224,215,191));draw=ImageDraw.Draw(sheet)
    for col,(name,img) in enumerate([('Painting',source),('Rendered idle',raw),('Decoded 160px delivery (enlarged)',token)]):
        x=8+272*col
        draw.text((x,10),name,fill=(40,34,27))
        large=img.resize((256,256),Image.Resampling.LANCZOS);sheet.paste(large,(x,36),large)
        small=img.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(x+96,302),small)
    sheet.save(R/'horseman-packed-review.png')
    print(f'PACK: {len(data)} bytes, quality {quality}, {width}x{y}, 40 trimmed 160px frames')

if __name__ == '__main__':
    main()

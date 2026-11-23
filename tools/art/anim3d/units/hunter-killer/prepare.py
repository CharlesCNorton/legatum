"""Register the original high-resolution painting to the shipped token's field."""
import hashlib
import json
from PIL import Image
from common import ASSETS, MASTER, SLUG, log

source = ASSETS / 'painting-source.png'
if not source.exists():
    raise SystemExit('Download the CC BY 4.0 source to assets/hunter-killer/painting-source.png first.')
im = Image.open(source).convert('RGBA')
fig = im.crop(im.getchannel('A').getbbox())
k = min(928 / fig.width, 928 / fig.height)
fig = fig.resize((round(fig.width*k), round(fig.height*k)), Image.Resampling.LANCZOS)
out = Image.new('RGBA', (1024, 1024))
out.alpha_composite(fig, ((1024-fig.width)//2, (1024-fig.height)//2))
out.save(ASSETS / 'projection.png')
# Fit the generated clean disc to the original stone's known camera landmarks.
# Its alpha never cuts Blender geometry; the original lower rim stays intact.
fill = Image.open(ASSETS / 'stone-fill-source.png').convert('RGBA')
box = fill.getchannel('A').point(lambda x: 255 if x > 240 else 0).getbbox()
fill = fill.crop(box).resize((928, 248), Image.Resampling.LANCZOS)
clean = Image.new('RGBA', out.size)
clean.alpha_composite(fill, (48, 592))
# The lower disc is unobscured below the lowest painted foot. Feather a mask
# above that line; never freeze any reference feet or contact shadows on the base.
stone = out.copy()
mask = Image.new('L', out.size)
for y in range(out.height):
    weight = max(0, min(1, (y / 4 - 184) / 4))
    if weight:
        for x in range(out.width):
            mask.putpixel((x, y), round(out.getpixel((x, y))[3] * weight))
stone.putalpha(mask)
clean.alpha_composite(stone)
clean.save(ASSETS / 'stone-projection.png')
(MASTER / 'inputs.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'source_url': f'https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/{SLUG}-source.png',
    'licence': 'CC BY 4.0', 'projection': 'alpha-bbox fit, 232/256 field; no warping',
}, indent=2))
log('Prepared full-source projection; read all six Blender skills, vehicle chapter, art skill and standing feedback 12–22.')

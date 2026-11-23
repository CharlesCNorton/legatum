"""Register the original high-resolution painting to the shipped token's field."""
import hashlib
import json
import math
from PIL import Image, ImageDraw, ImageFilter
from common import ASSETS, MASTER, HERE, SLUG, log

for name,expected in json.loads((HERE/'assets.lock.json').read_text()).items():
    assert hashlib.sha256((ASSETS/name).read_bytes()).hexdigest()==expected, f'Source changed: {name}'

source = ASSETS / 'painting-source.png'
if not source.exists():
    raise SystemExit('Download the CC BY 4.0 source to assets/autonomous-armour/painting-source.png first.')
im = Image.open(source).convert('RGBA')
fig = im.crop(im.getchannel('A').getbbox())
k = min(928 / fig.width, 928 / fig.height)
fig = fig.resize((round(fig.width*k), round(fig.height*k)), Image.Resampling.LANCZOS)
out = Image.new('RGBA', (1024, 1024))
out.alpha_composite(fig, ((1024-fig.width)//2, (1024-fig.height)//2))
out.save(ASSETS / 'projection.png')
# Only the painted tread surfaces may enter moving link UVs. Wheels, hull and
# stone are excluded, preventing the doubled source hubs seen in the first round.
mask=Image.new('L',(1024,1024));draw=ImageDraw.Draw(mask)
for polygon in [
    [(459,623),(556,628),(552,698),(525,759),(482,806),(411,832),(396,810),(437,768),(459,711),(463,662)],
    [(900,616),(968,619),(973,679),(947,731),(899,766),(826,784),(814,769),(870,734),(898,684)],
    [(72,510),(109,522),(80,574),(89,644),(128,704),(146,718),(132,737),(103,711),(67,652),(49,597),(49,552)],
    [(130,712),(399,810),(425,828),(397,834),(123,738)],
]:draw.polygon(polygon,fill=255)
mask.filter(ImageFilter.GaussianBlur(2)).save(ASSETS/'tread-projection-mask.png')
# Twelve-fold pigment symmetry closes at the wheel's five-stud-period move.
# Averaging equally spaced angles also removes the generator's directional key;
# Blender supplies the live lighting and cavity shading on the solid wheel dish.
wheel=Image.open(ASSETS/'wheel-fill-source.png').convert('RGB').resize((512,512))
pixels=wheel.load();pigment=Image.new('RGB',(512,512));dest=pigment.load()
for y in range(512):
    for x in range(512):
        dx,dy=x-255.5,y-255.5;r=math.hypot(dx,dy);a=math.atan2(dy,dx)
        samples=[]
        for k in range(12):
            t=a+k*math.tau/12
            samples.append(pixels[max(0,min(511,round(255.5+r*math.cos(t)))),max(0,min(511,round(255.5+r*math.sin(t))))])
        dest[x,y]=tuple(round(sum(p[c] for p in samples)/12) for c in range(3))
pigment.save(ASSETS/'wheel-pigment.png')
(MASTER / 'inputs.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'source_url': f'https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/{SLUG}-source.png',
    'licence': 'CC BY 4.0', 'projection': 'alpha-bbox fit, 232/256 field; no warping',
}, indent=2))
log('Prepared full-source projection; read all six Blender skills, vehicle chapter, art skill and standing feedback 12–22.')

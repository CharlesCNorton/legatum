"""Deterministic hand-brushed pigment maps sampled from the shipped painting."""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
MASTER = Path.home() / 'LegatumRuns/anim-pilot/masters/spearman-3d'


def main():
    out = MASTER / 'textures'
    out.mkdir(parents=True, exist_ok=True)
    source = Image.open(ROOT / 'app/src/assets/units/spearman-256.png').convert('RGBA')
    # Crops avoid the transparent surround, and preserve the actual ochre/red/linen palette.
    regions = {'bronze': (139, 119, 165, 155), 'red': (120, 61, 135, 70),
               'linen': (111, 151, 123, 166), 'skin': (106, 110, 115, 118),
               'stone': (112, 223, 145, 228), 'wood': (97, 128, 100, 184),
               'leather': (100, 207, 107, 214)}
    for name, box in regions.items():
        rng = random.Random(name)
        colors = [p[:3] for p in source.crop(box).getdata() if p[3] > 240]
        colors.sort(key=lambda p: sum(p))
        colors = colors[len(colors)//5:4*len(colors)//5]
        mean = tuple(int(sum(p[i] for p in colors)/len(colors)) for i in range(3))
        im = Image.new('RGB', (256, 256), mean)
        d = ImageDraw.Draw(im, 'RGBA')
        for _ in range(2200):
            x, y = rng.randrange(256), rng.randrange(256)
            c = rng.choice(colors)
            d.line((x, y, x+rng.randint(-5, 8), y+rng.randint(3, 24)), fill=(*c, rng.randrange(25, 95)), width=rng.randrange(1, 5))
        # Broad transparent glazes and short drybrush marks, not a uniform CG albedo.
        d = ImageDraw.Draw(im, 'RGBA')
        for x in range(256):
            shade = 0 if name == 'stone' else int(42*(.5+.5*math.sin(x*.072)) + 22*(x/256))
            d.line((x,0,x,255), fill=(38,21,8,shade))
        for _ in range(150):
            x,y=rng.randrange(256),rng.randrange(256)
            d.line((x,y,x+2,y+rng.randrange(4,14)),fill=(*colors[-1],100),width=1)
        im.filter(ImageFilter.GaussianBlur(.25)).save(out / f'{name}.png')
    # Source-painted detail maps for armour; hidden sides retain the sampled pigments.
    for name,box in {'cuirass':(119,116,132,143), 'helmet':(123,74,144,99),
                     'greave':(108,183,115,203), 'cloth':(109,149,125,169)}.items():
        crop=source.crop(box)
        under=Image.new('RGBA',crop.size,(164,117,55,255));under.alpha_composite(crop)
        patch=under.convert('RGB').resize((256,256),Image.Resampling.BICUBIC)
        pigment=Image.open(out/('linen.png' if name=='cloth' else 'bronze.png'))
        patch=Image.blend(pigment,patch,.55)
        patch.save(out/f'{name}.png')
    # Aspis ornament: painted radial sun, with ochre highlights and burnt umber engraving.
    im = Image.open(out / 'bronze.png').resize((512, 512))
    d = ImageDraw.Draw(im)
    for r in (242, 235, 213):
        d.ellipse((256-r, 256-r, 256+r, 256+r), outline='#69421e', width=4)
        d.arc((257-r, 257-r, 255+r, 255+r), 180, 335, fill='#e2bd74', width=3)
    for i in range(16):
        a = i*math.tau/16
        def p(r, angle): return (256+r*math.sin(angle), 256+r*math.cos(angle))
        d.polygon([p(47,a-.18), p(200 if i%2==0 else 159,a), p(47,a+.18)], fill='#70461f')
        d.polygon([p(49,a-.13), p(191 if i%2==0 else 151,a), p(52,a)], fill='#d9ac60')
        d.line([p(55,a),p(175 if i%2==0 else 138,a)], fill='#edca82', width=2)
    d.ellipse((210,210,302,302), fill='#9d692e', outline='#53391d', width=4)
    d.arc((218,218,294,294),180,320,fill='#ecc982',width=8)
    im.save(out/'shield.png')


if __name__ == '__main__': main()

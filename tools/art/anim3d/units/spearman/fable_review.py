"""Fable-b review sheets from the graded renders: rest triptych, clip strips at
256 and 160 px, looping GIFs and one 160 px contact sheet. Reads ANIM_ROOT's
master renders; writes spearman-fable-b-* into the shared review folder (or argv[1])."""
import os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

root = Path(os.environ['ANIM_ROOT'])
renders = root/'masters/spearman-3d-v2/renders'
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
CREAM = (224, 215, 191)
FPS = {'idle': 4, 'move': 6, 'attack': 14, 'hit': 12, 'death': 4}
painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')


def flat(im, size=None):
    if size and im.width != size:
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    bg = Image.new('RGBA', im.size, CREAM+(255,))
    return Image.alpha_composite(bg, im).convert('RGB')


def frames(clip):
    return [Image.open(p).convert('RGBA') for p in sorted((renders/('e-'+clip)).glob('[0-9][0-9].png'))]


rest = Image.open(renders/'c/three-quarter.png').convert('RGBA')
if rest.width != 256:
    rest = rest.resize((256, 256), Image.Resampling.LANCZOS)
a, b = flat(painting), flat(rest)
pa = painting.getchannel('A').point(lambda v: 255 if v > 96 else 0)
ra = rest.getchannel('A').point(lambda v: 255 if v > 96 else 0)
diff = Image.composite(Image.new('RGB', (256, 256), (150, 150, 150)), Image.new('RGB', (256, 256), (240, 240, 235)), ImageChops.multiply(pa, ra))
diff = Image.composite(Image.new('RGB', (256, 256), (220, 40, 40)), diff, ImageChops.subtract(ra, pa))
diff = Image.composite(Image.new('RGB', (256, 256), (40, 80, 220)), diff, ImageChops.subtract(pa, ra))
panels = [('Painting', a), ('Fable-b 3D rest', b), ('50/50 crossfade', Image.blend(a, b, .5)), ('Silhouette: red 3D only, blue painting only', diff)]
sheet = Image.new('RGB', (len(panels)*528+8, 36+512+8+160+8), CREAM)
draw = ImageDraw.Draw(sheet)
for i, (label, im) in enumerate(panels):
    x = 8+i*528
    draw.text((x, 10), label+' | 256 px shown 2x, then native 160 and 64', fill=(40, 34, 27))
    sheet.paste(im.resize((512, 512), Image.Resampling.LANCZOS), (x, 36))
    sheet.paste(im.resize((160, 160), Image.Resampling.LANCZOS), (x, 36+512+8))
    sheet.paste(im.resize((64, 64), Image.Resampling.LANCZOS), (x+176, 36+512+8+96))
sheet.save(out/'spearman-fable-b-restpose-compare.png')

contact_rows = []
for clip, fps in FPS.items():
    fs = frames(clip)
    if not fs:
        continue
    strip = Image.new('RGB', (8+len(fs)*264, 30+256+8+160+8), CREAM)
    draw = ImageDraw.Draw(strip)
    draw.text((8, 8), f'Spearman fable-b | {clip} | {len(fs)} frames at {fps} fps | native 256 px, then native 160 px', fill=(40, 34, 27))
    for i, im in enumerate(fs):
        strip.paste(flat(im, 256), (8+i*264, 30))
        strip.paste(flat(im, 160), (8+i*264+48, 30+256+8))
    strip.save(out/f'spearman-fable-b-{clip}-strip.png')
    for size in (256, 160):
        gif = [flat(im, size).quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for im in fs]
        hold = [round(1000/fps)]*len(gif)
        if clip in ('death', 'hit', 'attack'):
            hold[-1] = 900
        gif[0].save(out/f'spearman-fable-b-{clip}-{size}.gif', save_all=True, append_images=gif[1:], duration=hold, loop=0)
    contact_rows.append((clip, fs))
width = 8+max(len(fs) for _, fs in contact_rows)*164
contact = Image.new('RGB', (width+60, 8+len(contact_rows)*168), CREAM)
draw = ImageDraw.Draw(contact)
for y, (clip, fs) in enumerate(contact_rows):
    draw.text((6, 8+y*168+70), clip, fill=(40, 34, 27))
    for i, im in enumerate(fs):
        contact.paste(flat(im, 160), (60+i*164, 8+y*168))
contact.save(out/'spearman-fable-b-contact-160.png')
print('FABLE_REVIEW', out)

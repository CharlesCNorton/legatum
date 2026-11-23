#!/usr/bin/env python3
"""Prepare camera projection textures and filled occlusion patches outside git."""
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter
from units import UNITS
ROOT = Path(__file__).resolve().parents[3]
HOME = Path.home() / 'LegatumRuns/anim-pilot'

def polygon(points):
    im = Image.new('L',(256,256)); ImageDraw.Draw(im).polygon(points,fill=255); return im

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('slug',choices=UNITS); a=ap.parse_args()
    cfg=UNITS[a.slug]; dest=HOME/'masters'/a.slug; dest.mkdir(parents=True,exist_ok=True)
    src=Image.open(ROOT/f'app/src/assets/units/{a.slug}-256.png').convert('RGBA')
    src.save(dest/'painting.png')
    # Plain base surface reconstructed from the painting's unobstructed stone.
    # Same footprint, top ellipse, rim and warm pigment; no ground outside it.
    x0,y0,x1,y1=cfg['base']; rim=10; rx=(x1-x0)/2
    ry=(y1-y0-rim)/2; cx=(x0+x1)/2; cy=y0+ry
    # A continuous low cylinder. Copying scattered thresholded source pixels
    # retained pieces of the old rim across the new top, so never do that.
    scale=4; base=Image.new('RGBA',(256*scale,256*scale))
    for py in range(y0*scale,(y1+1)*scale):
        for px in range(x0*scale,(x1+1)*scale):
            x=(px+.5)/scale; y=(py+.5)/scale; u=(x-cx)/rx
            if abs(u)>1: continue
            h=ry*math.sqrt(1-u*u); top=cy-h; edge=cy+h
            if not top<=y<=edge+rim: continue
            grain=((int(x*7)*73856093 ^ int(y*7)*19349663)%17-8)*.12
            if y<=edge:
                light=2.3*(1-u)-1.4*(y-cy)/ry+grain
                colour=(242+light,222+light,186+light)
                if edge-y<.55: colour=(250,234,202)
            else:
                light=3*(1-u)-.3*(y-edge)+grain
                colour=(225+light,193+light,145+light)
            base.putpixel((px,py),tuple(max(0,min(255,round(c))) for c in colour)+(255,))
    base=base.resize((256,256),Image.Resampling.LANCZOS)
    # Baked contact shade only on the stone, never on an exterior plane.
    shadow=Image.new('RGBA',(256,256)); sd=ImageDraw.Draw(shadow)
    for foot in cfg['feet']:
        fx=sum(p[0] for p in foot)/len(foot); fy=max(p[1] for p in foot)-1
        sd.ellipse((fx-8,fy-2,fx+8,fy+2),fill=(85,65,38,48))
    shadow=shadow.filter(ImageFilter.GaussianBlur(1.4))
    shadow.putalpha(ImageChops.multiply(shadow.getchannel('A'),base.getchannel('A')))
    base.alpha_composite(shadow);base.save(dest/'base.png')
    # Keep source contact points; all other base pixels are removed from figure.
    figuremask=polygon([(0,0),(256,0),(256,y0-1),(0,y0-1)])
    for foot in cfg['feet']: figuremask=ImageChops.lighter(figuremask,polygon(foot))
    figure=src.copy(); figure.putalpha(ImageChops.multiply(src.getchannel('A'),figuremask))
    taken=Image.new('L',(256,256)); layers=[]
    # Explicit layer ownership: earlier masks own overlap (weapon before hand).
    for name,pivot,points,parent in cfg['parts']:
        mask=ImageChops.subtract(polygon(points),taken)
        mask=ImageChops.multiply(mask,figure.getchannel('A'))
        layer=src.copy(); layer.putalpha(mask); layer.save(dest/f'{name}.png')
        taken=ImageChops.lighter(taken,polygon(points))
        layers.append(dict(name=name,pivot=pivot,parent=parent))
    remaining=ImageChops.subtract(figure.getchannel('A'),taken)
    # Extend adjacent paint six pixels under articulated parts. This creates
    # overlap at joints and under shield edges instead of a transparent seam.
    # It cannot invent unseen anatomy; large reveals still need hand painting.
    body=src.copy(); body.putalpha(remaining)
    figure_alpha=figure.getchannel('A')
    for _ in range(6):
        old=body.copy(); alpha=old.getchannel('A')
        for y in range(1,255):
            for x in range(1,255):
                if alpha.getpixel((x,y)) or not figuremask.getpixel((x,y)): continue
                if not figure_alpha.getpixel((x,y)): continue
                neighbours=[old.getpixel((x+dx,y+dy)) for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)) if alpha.getpixel((x+dx,y+dy))>128]
                if neighbours:
                    body.putpixel((x,y),tuple(round(sum(c[k] for c in neighbours)/len(neighbours)) for k in range(3))+(255,))
    body.save(dest/'body.png')
    (dest/'model.json').write_text(json.dumps(dict(**cfg,layers=layers),indent=2))
    print(f'{a.slug}: prepared {len(layers)+2} projection layers in {dest}')
if __name__=='__main__': main()

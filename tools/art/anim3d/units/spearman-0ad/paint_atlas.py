"""Author flat pigment and ornament only: no illumination, AO or normal data."""
from pathlib import Path
import argparse, math
from PIL import Image, ImageDraw

PALETTE = [(184,125,53),(230,205,154),(165,38,39),(183,124,83),
           (94,53,32),(72,37,25),(212,165,82),(135,78,37),(255,255,255)]
def paint(path):
    image=Image.new('RGB',(1024,1024),(184,125,53));d=ImageDraw.Draw(image)
    # Eight padded swatches. Every uniform region samples its swatch centre.
    for i,c in enumerate(PALETTE):d.rectangle((i*64,0,i*64+63,255),fill=c)
    # Shield occupies the lower 768 px. Pigment variation is symmetric and decorative.
    cx,cy,r=512,640,354
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(202,150,68),outline=(109,62,29),width=10)
    d.ellipse((cx-r+24,cy-r+24,cx+r-24,cy+r-24),outline=(239,198,108),width=7)
    for i in range(12):
        a=i*math.tau/12
        pts=[(cx+math.sin(a+b)*rr,cy+math.cos(a+b)*rr) for b,rr in [(-.14,72),(0,276),(.14,72),(0,101)]]
        d.polygon(pts,fill=(119,69,33));d.line(pts[:3],fill=(239,198,108),width=5)
    d.ellipse((cx-76,cy-76,cx+76,cy+76),fill=(213,161,76),outline=(111,61,28),width=9)
    d.ellipse((cx-54,cy-54,cx+54,cy+54),outline=(239,198,108),width=5)
    # Flat front-helmet paint, not shadows: paired eye slots and engraved edges.
    d.rectangle((768,0,1023,255),fill=PALETTE[0])
    def hp(x,z):return (768+(x+.28)/.56*256,255-(z+.15)/.85*256)
    for sign in [-1,1]:
        eye=[(sign*.035,.31),(sign*.19,.32),(sign*.18,.265),(sign*.045,.27)]
        d.polygon([hp(x,z) for x,z in eye],fill=(48,28,20))
        d.line([hp(sign*.035,.35),hp(sign*.20,.36)],fill=PALETTE[6],width=5)
        d.line([hp(sign*.20,.23),hp(sign*.15,-.05)],fill=PALETTE[7],width=4)
    d.line([hp(-.055,-.035),hp(.055,-.035)],fill=PALETTE[5],width=4)
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);paint(p.parse_args().output)

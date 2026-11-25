"""Author flat pigment and ornament only: no illumination, AO or normal data."""
from pathlib import Path
import argparse, math
from PIL import Image, ImageDraw

PALETTE = [(146,92,36),(218,199,158),(123,23,30),(188,136,101),
           (94,53,32),(72,37,25),(212,165,82),(135,78,37),(255,255,255),(110,110,110)]
def paint(path):
    image=Image.new('RGB',(1024,1024),PALETTE[0]);d=ImageDraw.Draw(image)
    # Eight padded swatches. Every uniform region samples its swatch centre.
    for i,c in enumerate(PALETTE):d.rectangle((i*64,0,i*64+63,255),fill=c)
    # Broad bronze sunburst on an oxidised bronze field. These are flat
    # pigment boundaries, never directional highlights or painted occlusion.
    cx,cy,r=512,640,354
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(87,53,27),outline=(42,28,21),width=24)
    d.ellipse((cx-r+30,cy-r+30,cx+r-30,cy+r-30),outline=(171,114,47),width=10)
    for i in range(12):
        a=i*math.tau/12
        pts=[(cx+math.sin(a+b)*rr,cy+math.cos(a+b)*rr)
             for b,rr in [(-.23,75),(0,282),(.23,75)]]
        d.polygon(pts,fill=(211,157,68))
    d.ellipse((cx-88,cy-88,cx+88,cy+88),fill=(42,28,21))
    d.ellipse((cx-72,cy-72,cx+72,cy+72),fill=(211,157,68))
    # Flat front-helmet paint, not shadows: paired eye slots and engraved edges.
    d.rectangle((768,0,1023,255),fill=PALETTE[0])
    def hp(x,z):return (768+(x+.28)/.56*256,255-(z+.15)/.85*256)
    for sign in [-1,1]:
        eye=[(sign*.035,.31),(sign*.19,.32),(sign*.18,.265),(sign*.045,.27)]
        d.polygon([hp(x,z) for x,z in eye],fill=(48,28,20))
        d.line([hp(sign*.035,.35),hp(sign*.20,.36)],fill=PALETTE[6],width=5)
        d.line([hp(sign*.20,.23),hp(sign*.15,-.05)],fill=PALETTE[7],width=4)
    d.line([hp(-.055,-.035),hp(.055,-.035)],fill=PALETTE[5],width=4)
    # Broad painted ornament, not shading: bronze borders and engraved cuirass.
    d.rectangle((576,0,767,255),fill=PALETTE[0])
    d.rectangle((580,5,763,251),outline=PALETTE[7],width=4)
    d.line([(585,24),(614,45),(672,52),(730,45),(759,24)],fill=PALETTE[6],width=7)
    for x in [624,720]:
        d.arc((x-40,45,x+40,135),10,170,fill=PALETTE[7],width=5)
        d.arc((x-34,48,x+34,125),12,168,fill=PALETTE[6],width=3)
    for y in [152,184,215]:
        d.line([(596,y-6),(630,y),(672,y+3),(714,y),(748,y-6)],fill=PALETTE[7],width=3)
    for x in range(592,760,16):d.ellipse((x-2,235,x+2,239),fill=PALETTE[6])
    # Linen hem stripes: surface dye and seams, not occlusion between folds.
    d.rectangle((0,320,128,640),fill=PALETTE[1])
    for x in range(4,128,19):d.line([(x,324),(x+2,636)],fill=(188,157,110),width=2)
    for y in [596,608]:d.line([(2,y),(126,y)],fill=PALETTE[2],width=4)
    # Greave border and central incised motif.
    d.rectangle((896,320,1023,640),fill=PALETTE[0])
    d.rectangle((900,325,1019,636),outline=PALETTE[7],width=4)
    d.line([(960,334),(960,626)],fill=PALETTE[6],width=5)
    d.arc((930,336,990,435),0,180,fill=PALETTE[7],width=4)
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);paint(p.parse_args().output)

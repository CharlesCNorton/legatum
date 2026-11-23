"""Native-size evidence sheets. Never reshape a render to conceal misregistration."""
import os,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageEnhance
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/composite-archer';OUT=R/'review/3d-v2'
REF=Image.open('app/src/assets/units/composite-archer-256.png').convert('RGBA')
def sheet(stage, images, labels=None):
 ims=[REF]+[Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) if isinstance(p,(str,Path)) else p.resize((256,256),Image.Resampling.LANCZOS) for p in images]
 canvas=Image.new('RGB',(len(ims)*256,370),(38,34,30));d=ImageDraw.Draw(canvas)
 labels=['Painting']+(labels or ['Cycles CPU preview']*len(images))
 for i,(im,label) in enumerate(zip(ims,labels)):
  canvas.paste(im,(i*256,24),im);d.text((i*256+7,6),label,fill=(240,220,190));tiny=im.resize((64,64),Image.Resampling.LANCZOS);canvas.paste(tiny,(i*256+96,290),tiny)
 canvas.save(OUT/f'composite-archer-{stage}.png')
 return canvas
if __name__=='__main__':
 import sys
 stage=sys.argv[1];sheet(stage,[M/f'{stage}.png'])

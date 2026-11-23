#!/usr/bin/env python3
"""Pack rendered frames; validate the contract; make sheets and animated previews."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from units import CLIPS,UNITS
ROOT=Path(__file__).resolve().parents[3]; HOME=Path.home()/'LegatumRuns/anim-pilot'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('slug',choices=UNITS); args=ap.parse_args(); slug=args.slug
 master=HOME/'masters'/slug; review=HOME/'review'; review.mkdir(exist_ok=True,parents=True)
 output=ROOT/'app/src/assets/units/anim'; output.mkdir(exist_ok=True,parents=True)
 atlas=Image.new('RGBA',(2560,1280)); frames={}
 meta={'frame':dict(w=256,h=256,ax=UNITS[slug]['anchor'][0],ay=UNITS[slug]['anchor'][1]),'clips':{}}
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  frames[clip]=[Image.open(master/'frames'/clip/f'{i:02}.png').convert('RGBA') for i in range(n)]
  for i,im in enumerate(frames[clip]):
   assert im.size==(256,256); atlas.paste(im,(i*256,row*256))
  meta['clips'][clip]=dict(row=row,frames=n,fps=fps,loop=loop)
  # Preview non-looping clips repeats with a long final hold for easy inspection.
  durations=[round(1000/fps)]*n
  if not loop: durations[-1]=850
  frames[clip][0].save(review/f'{slug}-{clip}.webp',save_all=True,append_images=frames[clip][1:],duration=durations,loop=0,quality=85,method=6)
 quality=80
 while True:
  atlas.save(output/f'{slug}.webp',quality=quality,method=6,exact=True)
  size=(output/f'{slug}.webp').stat().st_size
  if size<=200_000:break
  quality-=5
  if quality<30:raise RuntimeError(f'{slug} cannot fit without unacceptable compression')
 (output/f'{slug}.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
 # Both backdrops, all frames, plus the original at 256. Inspection PNG remains outside git.
 sheet=Image.new('RGB',(1320,5*300),(242,234,216));d=ImageDraw.Draw(sheet)
 original=Image.open(ROOT/f'app/src/assets/units/{slug}-256.png').convert('RGBA')
 for row,(clip,ims) in enumerate(frames.items()):
  y=row*300;d.rectangle((0,y,1319,y+299),fill='#f2ead8');d.text((12,y+8),f'{slug} / {clip} / source left',fill='#2b2419');sheet.paste(original,(4,y+26),original)
  for j,bg in enumerate(['#888888','#f2ead8']):
   for i,im in enumerate(ims):
    x=278+i*102;yy=y+25+j*135;d.rectangle((x,yy,x+101,yy+128),fill=bg)
    thumb=im.resize((100,100),Image.Resampling.LANCZOS);sheet.paste(thumb,(x,yy+14),thumb);d.text((x+4,yy+114),str(i),fill='#2b2419')
 sheet.save(review/f'{slug}.png')
 print(json.dumps(dict(slug=slug,bytes=size,kB=round(size/1000,2),quality=quality,frames=sum(v[0] for v in CLIPS.values()))))
if __name__=='__main__':main()

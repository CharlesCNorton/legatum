#!/usr/bin/env python3
"""Validate delivery metadata, dimensions, alpha/padding, size and held death pose."""
import json
from pathlib import Path
from PIL import Image,ImageChops
from units import CLIPS,UNITS
ROOT=Path(__file__).resolve().parents[3]
def validate():
 for slug,cfg in UNITS.items():
  path=ROOT/'app/src/assets/units/anim'/slug
  meta=json.loads(path.with_suffix('.json').read_text())
  assert list(meta)==['frame','clips'],slug
  assert meta['frame']==dict(w=256,h=256,ax=cfg['anchor'][0],ay=cfg['anchor'][1]),slug
  assert list(meta['clips'])==list(CLIPS),slug
  atlas=Image.open(path.with_suffix('.webp')).convert('RGBA')
  assert atlas.size==(2560,1280),slug
  assert path.with_suffix('.webp').stat().st_size<=200_000,slug
  for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
   assert meta['clips'][clip]==dict(row=row,frames=n,fps=fps,loop=loop),(slug,clip)
   frames=[]
   for i in range(n):
    frame=atlas.crop((i*256,row*256,(i+1)*256,(row+1)*256));frames.append(frame)
    alpha=frame.getchannel('A');bounds=alpha.getbbox()
    assert bounds and 0<bounds[0]<bounds[2]<256 and 0<bounds[1]<bounds[3]<256,(slug,clip,i,'clipped silhouette')
    assert alpha.getextrema()==(0,255),(slug,clip,i,'missing alpha')
   if n<10:assert not atlas.crop((n*256,row*256,2560,(row+1)*256)).getchannel('A').getbbox(),(slug,clip,'padding')
   if clip=='death':
    # Lossy WebP can differ by a few pigment levels across adjacent blocks.
    a,b=frames[-2:];assert ImageChops.difference(a.getchannel('A'),b.getchannel('A')).getbbox() is None,(slug,'death must hold')
  print(f'{slug}: contract, alpha, padding, held death and size PASS')
if __name__=='__main__':validate()

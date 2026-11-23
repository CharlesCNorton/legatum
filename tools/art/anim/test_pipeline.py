#!/usr/bin/env python3
"""Synthetic packing integration test; fixtures are temporary, never delivered art."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
import pack,validate
from units import UNITS,CLIPS

class PackingTest(unittest.TestCase):
 def test_all_units_contract_and_frame_placement(self):
  with tempfile.TemporaryDirectory(prefix='legatum-anim-test-') as tmp:
   root=Path(tmp); home=root/'work'
   with patch.object(pack,'ROOT',root),patch.object(pack,'HOME',home),patch.object(validate,'ROOT',root):
    for slug,cfg in UNITS.items():
     assets=root/'app/src/assets/units';assets.mkdir(parents=True,exist_ok=True)
     reference=Image.new('RGBA',(256,256));ImageDraw.Draw(reference).ellipse((60,200,196,238),fill='#eedcbc')
     reference.save(assets/f'{slug}-256.png')
     for row,(clip,(count,_,_)) in enumerate(CLIPS.items()):
      dest=home/'masters'/slug/'frames'/clip;dest.mkdir(parents=True)
      for frame in range(count):
       im=reference.copy();index=min(frame,8) if clip=='death' else frame
       ImageDraw.Draw(im).rectangle((80+index,60,135+index,180),fill=(40+row*35,50+index*12,90,255))
       im.save(dest/f'{frame:02}.png')
     with patch('sys.argv',['pack.py',slug]),contextlib.redirect_stdout(io.StringIO()):pack.main()
     atlas=Image.open(assets/'anim'/f'{slug}.webp').convert('RGBA')
     for row,(clip,(count,_,_)) in enumerate(CLIPS.items()):
      for frame in range(count):
       pixel=atlas.getpixel((frame*256+110,row*256+100))
       expected=(40+row*35,50+(min(frame,8) if clip=='death' else frame)*12,90)
       self.assertLess(max(abs(pixel[i]-expected[i]) for i in range(3)),12,(slug,clip,frame))
     meta=json.loads((assets/'anim'/f'{slug}.json').read_text())
     self.assertEqual((meta['frame']['ax'],meta['frame']['ay']),cfg['anchor'])
    with contextlib.redirect_stdout(io.StringIO()):validate.validate()

if __name__=='__main__':unittest.main()

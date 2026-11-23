"""Checks for the lossy-color/lossless-alpha delivery contract."""
import importlib.util,unittest,io
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('finish.py'));delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
class DeliveryTests(unittest.TestCase):
 def test_grade_is_monotone_and_alpha_preserving(self):
  im=Image.new('RGBA',(256,256));im.putdata([(x,y,255-x,(x+y)%256) for y in range(256) for x in range(256)])
  p=delivery.grade_params(im)
  for lut in p['luts']:self.assertEqual(lut,sorted(lut))
  self.assertEqual(delivery.grade(im,p).getchannel('A').tobytes(),im.getchannel('A').tobytes())
 def test_premultiplied_reduction_has_no_black_halo(self):
  im=Image.new('RGBA',(512,512));im.paste((220,140,60,255),(151,41,361,471))
  small=delivery.reduced(im,{});edge=[p for p in small.get_flattened_data() if 20<p[3]<230]
  self.assertTrue(edge)
  self.assertTrue(all(abs(p[0]-220)<13 for p in edge))
 def test_webp_trim_reconstructs_exact_alpha(self):
  im=Image.new('RGBA',(160,160));im.putdata([(211,97,38,(x*3+y*7)%256 if 31<x<120 and 9<y<151 else 0) for y in range(160) for x in range(160)])
  box=im.getchannel('A').getbbox();crop=im.crop(box);buf=io.BytesIO();crop.save(buf,format='WEBP',quality=75,method=5,exact=True);decoded=Image.open(io.BytesIO(buf.getvalue())).convert('RGBA');restored=Image.new('RGBA',im.size);restored.paste(decoded,box[:2])
  self.assertEqual(im.getchannel('A').tobytes(),restored.getchannel('A').tobytes())
if __name__=='__main__':unittest.main()

"""Regression checks for temporal grade, trimmed alpha, and GPU provenance."""
import tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
from deliver import grade_lut, grade, logical_frame
from check_delivery import check

class DeliveryTests(unittest.TestCase):
    def image(self):
        im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
        d.ellipse((39,21,212,238),fill=(192,131,66,255))
        d.rectangle((60,80,130,190),fill=(55,32,21,180))
        return im
    def test_grade_preserves_alpha(self):
        im=self.image();out=grade(im,grade_lut(im,im))
        self.assertEqual(im.getchannel('A').tobytes(),out.getchannel('A').tobytes())
    def test_grade_is_monotone(self):
        im=self.image()
        for channel in grade_lut(im,im):self.assertEqual(channel,sorted(channel))
    def test_trim_reconstructs_exactly(self):
        im=logical_frame(self.image());box=im.getchannel('A').getbbox()
        cropped=im.crop(box);out=Image.new('RGBA',(160,160));out.paste(cropped,box[:2])
        self.assertEqual(im.tobytes(),out.tobytes())
    def test_transparent_rgb_does_not_bleed(self):
        a=self.image();b=a.copy();b.paste((255,0,255,0),mask=a.getchannel('A').point(lambda v:255 if v==0 else 0))
        self.assertEqual(logical_frame(a).tobytes(),logical_frame(b).tobytes())
    def test_incomplete_gpu_delivery_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):check(Path(folder),512,True)

if __name__=='__main__':unittest.main()

"""Regression checks for trim reconstruction and temporal grading invariants."""
import importlib.util,unittest,tempfile
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('unit_post',Path(__file__).with_name('post.py'))
post=importlib.util.module_from_spec(spec);spec.loader.exec_module(post)
class DeliveryTests(unittest.TestCase):
    def test_trim_offsets_preserve_semtransparent_pixels(self):
        atlas=Image.new('RGBA',(12,14));crop=Image.new('RGBA',(3,4),(80,100,120,83));atlas.paste(crop,(2,3))
        cell=post.restored(atlas,{'rects':[{'x':2,'y':3,'w':3,'h':4,'ox':49,'oy':71}]},0)
        self.assertEqual(cell.getbbox(),(49,71,52,75));self.assertEqual(cell.getpixel((49,71)),(80,100,120,83))
    def test_grade_preserves_alpha_and_is_monotonic(self):
        with tempfile.TemporaryDirectory() as d:
            old=post.M;post.M=Path(d);(post.M/'model.blend').write_bytes(b'test')
            try:
                im=Image.new('RGBA',(256,256))
                for x in range(256):
                    for y in range(256):im.putpixel((x,y),(x,x,x,y))
                post.fit_grade(im);first=post.grade(im)
                self.assertEqual(first.getchannel('A').tobytes(),im.getchannel('A').tobytes())
                self.assertEqual(first.tobytes(),post.grade(im).tobytes())
                for channel in 'RGB':
                    row=[first.getchannel(channel).getpixel((x,200)) for x in range(256)]
                    self.assertEqual(row,sorted(row))
            finally:post.M=old
if __name__=='__main__':unittest.main()

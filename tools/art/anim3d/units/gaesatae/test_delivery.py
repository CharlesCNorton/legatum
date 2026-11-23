"""Small regression checks for frame reconstruction and grading invariants."""
import json, tempfile, unittest
from pathlib import Path
from PIL import Image
import deliver as d

class DeliveryTests(unittest.TestCase):
    def test_trimmed_offsets_and_shared_hold(self):
        atlas=Image.new('RGBA',(12,9))
        patch=Image.new('RGBA',(4,3),(65,90,120,187));atlas.paste(patch,(2,4))
        r={'x':2,'y':4,'w':4,'h':3,'ox':52,'oy':109}
        with tempfile.TemporaryDirectory(dir=d.ROOT/'tmp') as temp:
            p=Path(temp)/'atlas.png';atlas.save(p)
            frames=d.unpack(p,{'clips':{'death':{'rects':[r,r]}}})['death']
        self.assertEqual(frames[0].getbbox(),(52,109,56,112))
        self.assertEqual(frames[0].getpixel((52,109)),(65,90,120,187))
        self.assertEqual(frames[0].tobytes(),frames[1].tobytes())
    def test_grade_preserves_alpha_and_input(self):
        im=Image.new('RGBA',(2,2),(40,90,180,77));original=im.tobytes()
        out=d.graded(im,{'scale':[1.1,.9,1],'offset':[2,-3,4]})
        self.assertEqual(out.getchannel('A').tobytes(),im.getchannel('A').tobytes())
        self.assertEqual(im.tobytes(),original)
        self.assertEqual(out.getpixel((0,0)),(46,78,184,77))
    def test_rgba_bicubic_alpha_survives_webp(self):
        import io
        im=Image.new('RGBA',(256,256));im.paste((150,90,35,193),(71,38,198,236))
        reduced=im.resize((160,160),Image.Resampling.BICUBIC)
        encoded=io.BytesIO();reduced.save(encoded,'WEBP',quality=75,exact=True)
        encoded.seek(0);decoded=Image.open(encoded).convert('RGBA')
        self.assertEqual(reduced.getchannel('A').tobytes(),decoded.getchannel('A').tobytes())

if __name__=='__main__':unittest.main()

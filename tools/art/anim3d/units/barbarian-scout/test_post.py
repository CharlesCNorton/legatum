"""Small delivery regressions; no Blender or render process required."""
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import post


class DeliveryTests(unittest.TestCase):
    def test_cpu_preview_does_not_create_512_master(self):
        with tempfile.TemporaryDirectory(dir=post.R/'tmp') as directory:
            master=Path(directory)/'master'; review=Path(directory)/'review'
            raw=master/'renders/c';raw.mkdir(parents=True);review.mkdir()
            im=Image.new('RGBA',(256,256),(90,60,30,0))
            im.paste((180,120,60,255),(70,20,190,230));im.save(raw/'00.png')
            (raw/'render.json').write_text(json.dumps({'device':'CPU','resolution':256,'samples':8}))
            with patch.object(post,'M',master),patch.object(post,'V',review):post.stage('c')
            with Image.open(master/'256/c/00.png') as result:
                self.assertEqual(result.size,(256,256))
            self.assertFalse((master/'512').exists())

    def test_gpu_gate_rejects_cpu_even_at_512(self):
        with tempfile.TemporaryDirectory(dir=post.R/'tmp') as directory:
            master=Path(directory);(master/'barbarian-scout.blend').write_bytes(b'test')
            raw=master/'renders/b';raw.mkdir(parents=True)
            (raw/'render.json').write_text(json.dumps({'device':'CPU','engine':'CYCLES','resolution':512}))
            with patch.object(post,'M',master),self.assertRaisesRegex(AssertionError,'not GPU512'):
                post.gpu_check()

    def test_grade_preserves_fractional_alpha(self):
        im=Image.new('RGBA',(256,1));im.putdata([(120,60,30,i) for i in range(256)])
        result=post.graded(im,[[min(255,i+20) for i in range(256)]]*3)
        self.assertEqual(result.getchannel('A').tobytes(),im.getchannel('A').tobytes())


if __name__=='__main__':unittest.main()

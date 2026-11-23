"""Small synthetic delivery regressions; no Blender or rendered-art quality claims."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location('crossbowman_post', Path(__file__).with_name('post.py'))
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.cwd = Path.cwd()
        self.old_master, self.old_review = post.M, post.V
        self.temp = tempfile.TemporaryDirectory(dir=post.R/'tmp')
        os.chdir(self.temp.name)
        post.M = Path('masters'); post.M.mkdir()
        post.V = Path('review'); post.V.mkdir()
        (post.M/'model.blend').write_bytes(b'synthetic model')
        (post.M/'grade.json').write_text(json.dumps({'model_sha256':post.digest(post.M/'model.blend')}))
        (post.M/'clips').mkdir()
        for name,(count,fps,loop) in post.CLIPS.items():
            clip=post.M/'clips'/f'{name}.blend'; clip.write_bytes(name.encode())
            clip.with_suffix('.json').write_text(json.dumps({'model_sha256':post.digest(post.M/'model.blend')}))
            folder=post.M/'frames/256'/('e-'+name); folder.mkdir(parents=True)
            for i in range(count):
                im=Image.new('RGBA',(256,256))
                offset=min(i,7) if name=='death' else i
                ImageDraw.Draw(im).ellipse((75+offset,40,165+offset,220),fill=(145,65,35,217))
                ImageDraw.Draw(im).rectangle((100,90,130,170),fill=(90,60,20,255))
                im.save(folder/f'{i:02d}.png')
            (folder/'render.json').write_text(json.dumps({'frames':count,'source_sha256':post.digest(clip),'grade_sha256':post.digest(post.M/'grade.json')}))
        post.pack()

    def tearDown(self):
        os.chdir(self.cwd)
        post.M,post.V=self.old_master,self.old_review
        self.temp.cleanup()

    def test_lossless_alpha_and_shared_terminal_rectangle(self):
        post.validate()
        meta=json.loads(Path('app/src/assets/units/anim/crossbowman.json').read_text())
        self.assertEqual(meta['clips']['death']['rects'][-1],meta['clips']['death']['rects'][-2])
        self.assertGreaterEqual(meta['quality'],75)

    def test_modified_master_is_rejected(self):
        path=post.M/'frames/256/e-attack/03.png'
        im=Image.open(path).convert('RGBA'); im.putpixel((100,100),(0,0,0,0)); im.save(path)
        with self.assertRaisesRegex(AssertionError,'Changed master'):
            post.validate()

    def test_offset_is_independently_checked(self):
        path=Path('app/src/assets/units/anim/crossbowman.json')
        meta=json.loads(path.read_text()); meta['clips']['idle']['rects'][0]['ox']+=1
        path.write_text(json.dumps(meta))
        receipt=json.loads((post.M/'pack.json').read_text()); receipt['metadata_sha256']=post.digest(path)
        (post.M/'pack.json').write_text(json.dumps(receipt))
        with self.assertRaisesRegex(AssertionError,'Changed alpha/offset'):
            post.validate()

    def test_changed_clip_is_rejected(self):
        (post.M/'clips/attack.blend').write_bytes(b'new clip')
        with self.assertRaisesRegex(AssertionError,'Changed clip'):
            post.validate()

if __name__=='__main__':
    unittest.main()

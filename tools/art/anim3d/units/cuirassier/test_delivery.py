"""End-to-end regression checks for the trimmed delivery contract; no Blender."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

UNIT = Path(__file__).resolve().parent
CLIPS = {'idle': (8,10,True), 'move': (8,12,True), 'attack': (10,14,False),
         'hit': (4,12,False), 'death': (10,10,False)}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(os.environ['ANIM_ROOT'])/'tmp')
        self.root = Path(self.temp.name)
        self.master = self.root/'masters/cuirassier'
        (self.master/'clips').mkdir(parents=True)
        (self.root/'review/3d-v2').mkdir(parents=True)
        (self.master/'cuirassier.blend').write_bytes(b'test master identity')
        (self.master/'grade.json').write_text('{}')
        for name,(count,_,_) in CLIPS.items():
            clip = self.master/'clips'/f'{name}.blend'
            clip.write_bytes(name.encode())
            folder = self.master/'renders'/f'e-{name}'
            folder.mkdir(parents=True)
            manifest = dict(engine='CYCLES',device='CPU',resolution=256,samples=8,
                            blend_sha256=sha(clip),source_master_sha256=sha(self.master/'cuirassier.blend'),
                            grade_sha256=sha(self.master/'grade.json'))
            (folder/'render.json').write_text(json.dumps(manifest))
            for index in range(count):
                frame = min(index,count-2) if name=='death' else index
                image = Image.new('RGBA',(256,256))
                draw = ImageDraw.Draw(image)
                draw.ellipse((50+frame,25,180+frame,230), fill=(70,50+frame*3,20,255))
                # Partial alpha inside the crop must survive, not merely its bbox.
                for alpha in range(1,255):
                    x=75+alpha%30; y=60+alpha//30
                    image.putpixel((x,y),(190,80,35,alpha))
                image.save(folder/f'{index:02}.png')
        rest = self.master/'renders/c'
        rest.mkdir(parents=True)
        manifest['blend_sha256']=sha(self.master/'cuirassier.blend')
        (rest/'render.json').write_text(json.dumps(manifest))

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self,name,success=True):
        process = subprocess.run([sys.executable,str(UNIT/f'{name}.py')],cwd=self.root,
                                 env={**os.environ,'ANIM_ROOT':str(self.root)},capture_output=True,text=True)
        self.assertEqual(process.returncode==0,success,process.stdout+process.stderr)

    def test_decoded_alpha_and_identical_death(self):
        self.run_script('pack')
        self.run_script('validate')
        meta=json.loads((self.root/'app/src/assets/units/anim/cuirassier.json').read_text())
        self.assertEqual(meta['clips']['death']['rects'][-1],meta['clips']['death']['rects'][-2])

    def test_shifted_trim_offset_is_rejected(self):
        self.run_script('pack')
        path=self.root/'app/src/assets/units/anim/cuirassier.json'
        meta=json.loads(path.read_text());meta['clips']['idle']['rects'][0]['ox']+=1
        path.write_text(json.dumps(meta))
        self.run_script('validate',False)

    def test_stale_grade_is_rejected(self):
        (self.master/'grade.json').write_text('{"changed":true}')
        self.run_script('pack',False)

    def test_mixed_render_settings_are_rejected(self):
        path=self.master/'renders/e-hit/render.json'
        data=json.loads(path.read_text());data['resolution']=512;path.write_text(json.dumps(data))
        self.run_script('pack',False)


if __name__=='__main__':
    unittest.main()

"""Small regression fixtures for trim reconstruction and stale/GPU rejection."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location('tagmatic_delivery', Path(__file__).with_name('deliver.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.master = root / 'masters'
        self.out = root / 'out'
        self.master.mkdir()
        self.paths = patch.multiple(d, M=self.master, OUT=self.out)
        self.paths.start()
        (self.master / 'tagmatic-soldier.blend').write_bytes(b'model fixture')
        (self.master / 'clips').mkdir()
        rest = self.master / 'renders/c'
        rest.mkdir(parents=True)
        Image.new('RGBA', (256, 256), (128, 80, 40, 255)).save(rest / '00.png')
        settings = {'resolution': 256, 'engine': 'CYCLES', 'device': 'CPU', 'samples': 8}
        (rest / 'render.json').write_text(json.dumps(settings))
        grade = {'luts': [list(range(256))] * 3,
                 'rest_render_sha256': d.sha(rest / 'render.json'),
                 'rest_frame_sha256': d.sha(rest / '00.png'),
                 'model_sha256': d.sha(self.master / 'tagmatic-soldier.blend')}
        (self.master / 'grade.json').write_text(json.dumps(grade))
        for clip, (count, fps, loop) in d.CLIPS.items():
            blend = self.master / 'clips' / f'{clip}.blend'
            blend.write_bytes(clip.encode())
            blend.with_suffix('.json').write_text(json.dumps({'source_sha256': grade['model_sha256']}))
            stage = 'e-' + clip
            rendered = self.master / 'renders' / stage
            frames = self.master / '256' / stage
            rendered.mkdir(parents=True)
            frames.mkdir(parents=True)
            meta = dict(settings, frames=count, blend_sha256=d.sha(blend))
            (rendered / 'render.json').write_text(json.dumps(meta))
            for i in range(count):
                sample = min(i, 8) if clip == 'death' else i
                image = Image.new('RGBA', (256, 256))
                draw = ImageDraw.Draw(image)
                draw.ellipse((44 + sample * 2, 30, 160 + sample, 225), fill=(180, 50 + sample, 30, 255))
                image.save(frames / f'{i:02}.png')
            review = {'render_sha256': d.sha(rendered / 'render.json'),
                      'grade_sha256': d.sha(self.master / 'grade.json'),
                      'frames256': {p.name: d.sha(p) for p in frames.glob('*.png')}}
            (rendered / 'review.json').write_text(json.dumps(review))

    def tearDown(self):
        self.paths.stop()
        self.tmp.cleanup()

    def test_all_forty_trimmed_frames_reconstruct_alpha(self):
        d.pack()
        d.validate()
        report = json.loads((self.master / 'validation.json').read_text())
        self.assertEqual(sum(c['frames'] for c in report['clips'].values()), 40)

    def test_wrong_offset_is_rejected_independently_of_metadata_hash(self):
        d.pack()
        path = self.out / 'tagmatic-soldier.json'
        meta = json.loads(path.read_text())
        meta['clips']['idle']['rects'][0]['ox'] += 1
        path.write_text(json.dumps(meta))
        proof_path = self.master / 'pack.json'
        proof = json.loads(proof_path.read_text())
        proof['metadata_sha256'] = d.sha(path)
        proof_path.write_text(json.dumps(proof))
        with self.assertRaisesRegex(AssertionError, 'trim offset/alpha mismatch'):
            d.validate()

    def test_changed_rest_frame_cannot_reuse_grade(self):
        (self.master / 'renders/c/00.png').write_bytes(b'changed')
        with self.assertRaisesRegex(AssertionError, 'Changed rest frame'):
            d.pack()

    def test_cpu_images_cannot_claim_gpu_master_delivery(self):
        folder = self.master / 'renders/b'
        folder.mkdir()
        (folder / 'render.json').write_text(json.dumps(dict(device='CPU', engine='CYCLES', resolution=512, samples=48, frames=3)))
        with self.assertRaisesRegex(AssertionError, 'not GPU512/48'):
            d.gpu_masters()


if __name__ == '__main__':
    unittest.main()

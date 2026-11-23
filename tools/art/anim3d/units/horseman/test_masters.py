"""GPU completion must reject stale or preview evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from check_masters import STAGES, check


class MasterGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='horseman-master-gate-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.master = self.root / 'masters/horseman-3d'
        (self.master / 'clips').mkdir(parents=True)
        for clip in ('idle', 'move', 'attack', 'hit', 'death'):
            (self.master / 'clips' / (clip + '.blend')).write_bytes(b'fixture blend')
        (self.master / 'horseman.blend').write_bytes(b'fixture blend')
        (self.master / 'grade.json').write_text('{}')
        for stage, count in STAGES.items():
            folder = self.master / 'renders' / stage
            folder.mkdir(parents=True)
            meta = dict(engine='CYCLES', device='GPU', resolution=512, samples=64,
                        blend_sha256=hashlib.sha256(b'fixture blend').hexdigest(),
                        grade_sha256=hashlib.sha256(b'{}').hexdigest())
            (folder / 'render.json').write_text(json.dumps(meta))
            for i in range(count):
                image = Image.new('RGBA', (512, 512), (80, 60, 40, 255))
                image.save(folder / f'{i:02}.png')
                for size in (512, 256):
                    archive = self.root / 'masters/horseman' / str(size) / stage
                    archive.mkdir(parents=True, exist_ok=True)
                    image.resize((size, size)).save(archive / f'{i:02}.png')

    def change_meta(self, **values):
        path = self.master / 'renders/c/render.json'
        meta = json.loads(path.read_text()); meta.update(values)
        path.write_text(json.dumps(meta))

    def test_current_gpu_evidence_passes(self):
        self.assertEqual(len(check(self.root)), 9)

    def test_cpu_is_not_gpu(self):
        self.change_meta(device='CPU')
        with self.assertRaisesRegex(AssertionError, 'GPU512 required'):
            check(self.root)

    def test_changed_blend_invalidates_evidence(self):
        (self.master / 'horseman.blend').write_bytes(b'changed')
        with self.assertRaisesRegex(AssertionError, 'stale blend'):
            check(self.root)

    def test_stale_gallery_is_rejected(self):
        Image.new('RGBA', (256, 256)).save(self.root / 'masters/horseman/256/c/00.png')
        with self.assertRaisesRegex(AssertionError, 'stale archived pixels'):
            check(self.root)


if __name__ == '__main__':
    unittest.main()

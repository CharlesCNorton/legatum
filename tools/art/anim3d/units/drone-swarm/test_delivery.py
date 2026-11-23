"""Regression checks against real rendered artifacts; no Blender job is launched."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('drone_delivery', Path(__file__).with_name('deliver.py'))
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryEvidenceTests(unittest.TestCase):
    def test_real_delivery_reconstructs(self):
        _, frames = delivery.validate()
        self.assertEqual(sum(map(len, frames.values())), 40)
        self.assertEqual(frames['death'][-1].tobytes(), frames['death'][-2].tobytes())

    def test_wrong_trim_offset_is_rejected(self):
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            value = original_read(path, *args, **kwargs)
            if path.name == 'drone-swarm.json':
                metadata = json.loads(value)
                metadata['clips']['idle']['sprites'][0]['ox'] += 1
                return json.dumps(metadata)
            return value
        with patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(AssertionError, 'alpha/offset mismatch'):
                delivery.validate()

    def test_modified_atlas_is_rejected(self):
        original_sha = delivery.sha
        def sha(path):
            return 'changed' if path.name == 'drone-swarm.webp' else original_sha(path)
        with patch.object(delivery, 'sha', sha):
            with self.assertRaisesRegex(AssertionError, 'changed atlas'):
                delivery.validate()

    def test_cpu_frames_cannot_claim_gpu(self):
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            value = original_read(path, *args, **kwargs)
            if path.name == 'render.json':
                metadata = json.loads(value)
                metadata['device'] = 'CPU'
                return json.dumps(metadata)
            return value
        with patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(AssertionError, 'GPU512 required'):
                delivery.gpu_check()


if __name__ == '__main__':
    unittest.main()

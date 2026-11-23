"""Corrupt a private delivery copy: ensure validation catches player-visible errors."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import deliver


class DeliveryRejections(unittest.TestCase):
    def setUp(self):
        self.original = deliver.A
        self.temp = tempfile.TemporaryDirectory(dir=deliver.ROOT/'tmp')
        deliver.A = Path(self.temp.name)
        for suffix in ('json','webp'):
            shutil.copyfile(self.original/f'{deliver.SLUG}.{suffix}', deliver.A/f'{deliver.SLUG}.{suffix}')
        self.metadata = json.loads((deliver.A/f'{deliver.SLUG}.json').read_text())

    def tearDown(self):
        deliver.A = self.original
        self.temp.cleanup()

    def rejects(self, metadata):
        (deliver.A/f'{deliver.SLUG}.json').write_text(json.dumps(metadata))
        with self.assertRaises(AssertionError):
            deliver.validate()

    def test_valid_delivery(self):
        deliver.validate()

    def test_displaced_trim_offset(self):
        data = copy.deepcopy(self.metadata)
        data['clips']['idle']['rects'][0]['ox'] += 1
        self.rejects(data)

    def test_wrong_source_rectangle(self):
        data = copy.deepcopy(self.metadata)
        data['clips']['idle']['rects'][0]['x'] += 1
        self.rejects(data)

    def test_wrong_clip_timing(self):
        data = copy.deepcopy(self.metadata)
        data['clips']['attack']['fps'] += 1
        self.rejects(data)


if __name__ == '__main__':
    unittest.main()

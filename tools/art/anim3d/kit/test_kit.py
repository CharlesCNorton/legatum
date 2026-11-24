"""Delivery edge regression and note handoff contract."""
import tempfile
import numpy as np
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.images import resize_rgba
from kit.report import append_evidence
from PIL import Image


class KitTests(unittest.TestCase):
    def test_transparent_magenta_does_not_fringe_white(self):
        source = Image.new('RGBA', (8, 2), (255, 0, 255, 0))
        for y in range(2):
            for x in range(4):
                source.putpixel((x, y), (255, 255, 255, 255))
        small = resize_rgba(source, (4, 1))
        for r, g, b, a in np.asarray(small).reshape(-1, 4):
            if a:
                self.assertEqual((r, g, b), (255, 255, 255))
        self.assertTrue(any(0 < p[3] < 255 for p in np.asarray(small).reshape(-1, 4)))

    def test_light_is_averaged_in_linear_space(self):
        source = Image.new('RGBA', (2, 1), (0, 0, 0, 255))
        source.putpixel((1, 0), (255, 255, 255, 255))
        result = resize_rgba(source, (1, 1)).getpixel((0, 0))
        self.assertTrue(185 <= result[0] <= 190, result)
        self.assertEqual(result[3], 255)

    def test_focus_stays_last_after_repeated_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'note.md'
            focus = 'FOCUS a: anatomy\nFOCUS b: paint\nFOCUS c: motion\n'
            path.write_text('Critique\n\n'+focus)
            append_evidence(path, 'CPU metrics')
            append_evidence(path, 'GPU metrics')
            self.assertTrue(path.read_text().endswith(focus))
            self.assertLess(path.read_text().index('CPU metrics'), path.read_text().index('GPU metrics'))


if __name__ == '__main__':
    unittest.main()

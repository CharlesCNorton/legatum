"""Regression checks for reference reduction and calibration invalidation."""
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.images import resize_rgba
from kit.part_paint import push_pull
import look_receipt

class LookTests(unittest.TestCase):
    def test_display_reduction_matches_reference_policy_and_ignores_hidden_rgb(self):
        image = Image.new('RGBA', (2, 1), (0, 0, 0, 255))
        image.putpixel((1, 0), (255, 255, 255, 255))
        self.assertEqual(resize_rgba(image, (1, 1), space='display').getpixel((0, 0))[0], 128)
        self.assertGreater(resize_rgba(image, (1, 1)).getpixel((0, 0))[0], 180)
        image.putpixel((0, 0), (255, 0, 255, 0))
        r, g, b, a = resize_rgba(image, (1, 1), space='display').getpixel((0, 0))
        self.assertEqual((r, g, b), (255, 255, 255))
        self.assertGreater(a, 0)

    def test_part_fill_never_introduces_neighbour_colour(self):
        rgb = np.zeros((8, 8, 3), dtype=np.float32)
        rgb[:] = [0, 255, 0]
        rgb[2:6, 2:6] = [125, 45, 22]
        weight = np.zeros((8, 8), dtype=np.float32); weight[2:6, 2:6] = 1
        self.assertTrue(np.allclose(push_pull(rgb, weight), [125, 45, 22]))

    def test_stale_master_or_texture_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            master = Path(directory); folder = master/'look'; folder.mkdir()
            for name in ('spearman.blend', 'spearman-source.png'):
                (master/name).write_bytes(b'initial')
            (folder/'front-cloak.png').write_bytes(b'paint')
            # Real reference and shader source hashes participate in the receipt too.
            look_receipt.write(master, folder)
            self.assertTrue(look_receipt.verify(master, folder))
            for path in (master/'spearman.blend', folder/'front-cloak.png'):
                original = path.read_bytes(); path.write_bytes(b'changed')
                with self.assertRaises(AssertionError): look_receipt.verify(master, folder)
                path.write_bytes(original)

if __name__ == '__main__': unittest.main()

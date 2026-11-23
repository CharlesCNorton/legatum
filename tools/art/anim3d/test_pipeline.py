"""Small regressions for stochastic held frames and stable animation grading."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from grade import apply, fit
from sequence import render_samples


class PipelineTests(unittest.TestCase):
    def test_held_sample_is_rendered_once_and_byte_identical(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            def render(frame, path):
                calls.append(frame)
                # Simulate different stochastic output on every renderer call.
                path.write_bytes(f'{frame}:noise-{len(calls)}'.encode())
            render_samples([25, 28, 47, 47], directory, render)
            self.assertEqual(calls, [25, 28, 47])
            self.assertEqual((Path(directory)/'02.png').read_bytes(), (Path(directory)/'03.png').read_bytes())

    def test_grade_ignores_transparency_preserves_alpha_and_tonal_order(self):
        src = Image.new('RGBA', (256, 2))
        ref = Image.new('RGBA', src.size)
        for x in range(256):
            src.putpixel((x, 0), (x, x, x, 255))
            ref.putpixel((x, 0), (min(255, x+30), x, max(0, x-20), 255))
            src.putpixel((x, 1), (255, 0, 255, 0))
            ref.putpixel((x, 1), (0, 255, 0, 0))
        lut = fit(src, ref)
        result = apply(src, lut)
        self.assertEqual(result.getchannel('A').tobytes(), src.getchannel('A').tobytes())
        self.assertGreater(result.getpixel((100, 0))[0], 100)
        self.assertLess(result.getpixel((100, 0))[2], 100)
        for channel in lut: self.assertEqual(channel, sorted(channel))
        # The same pixel gets the same colour even when its frame composition changes.
        changed = Image.new('RGBA', (1, 1), src.getpixel((100, 0)))
        self.assertEqual(apply(changed, lut).getpixel((0, 0)), result.getpixel((100, 0)))


if __name__ == '__main__':
    unittest.main()

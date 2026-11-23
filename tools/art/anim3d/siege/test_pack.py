"""Regression checks for trimmed-frame placement and lossless transparency."""
import io
import unittest
from PIL import Image, ImageDraw
from pack import compose, encode
from validate import reconstruct
from grade import fit, grade


class TrimmedAtlasTests(unittest.TestCase):
    def test_offset_reconstruction_keeps_subpixel_alpha_and_anchor(self):
        frames = {}
        for clip, i, box in [('idle', 0, (37, 17, 80, 140)), ('death', 0, (4, 92, 150, 143))]:
            image = Image.new('RGBA', (160, 160))
            draw = ImageDraw.Draw(image)
            draw.rectangle(box, fill=(191, 113, 45, 123))
            draw.line((box[0], box[1], box[2], box[3]), fill=(37, 55, 98, 255), width=3)
            frames[(clip, i)] = image
        atlas, rects = compose(frames, width=200)
        decoded = Image.open(io.BytesIO(encode(atlas, 75))).convert('RGBA')
        for key, original in frames.items():
            self.assertEqual(reconstruct(atlas, rects[key], 160).tobytes(), original.tobytes())
            result = reconstruct(decoded, rects[key], 160)
            self.assertEqual(result.getchannel('A').tobytes(), original.getchannel('A').tobytes())
            # The destination is offset minus a fixed logical anchor; no bbox recentering.
            self.assertEqual(rects[key]['ox'], original.getchannel('A').getbbox()[0])

    def test_master_reduction_preserves_bicubic_alpha_exactly(self):
        master = Image.new('RGBA', (512, 512))
        draw = ImageDraw.Draw(master)
        draw.ellipse((31, 80, 450, 460), fill=(180, 120, 60, 255))
        draw.line((15, 17, 470, 380), fill=(40, 70, 90, 175), width=5)
        atlas, rects = compose({('idle', 0): master})
        decoded = Image.open(io.BytesIO(encode(atlas, 75))).convert('RGBA')
        actual = reconstruct(decoded, rects[('idle', 0)], 160)
        expected = master.resize((160, 160), Image.Resampling.BICUBIC)
        self.assertEqual(actual.getchannel('A').tobytes(), expected.getchannel('A').tobytes())

    def test_identical_hold_shares_one_encoded_rectangle(self):
        frame = Image.new('RGBA', (160, 160))
        ImageDraw.Draw(frame).ellipse((25, 55, 125, 145), fill=(90, 70, 40, 235))
        atlas, rects = compose({('death', 8): frame, ('death', 9): frame.copy()})
        self.assertEqual(rects[('death', 8)], rects[('death', 9)])
        self.assertEqual(len(rects), 2)  # Both playback samples remain.
        decoded = Image.open(io.BytesIO(encode(atlas, 75))).convert('RGBA')
        self.assertEqual(reconstruct(decoded, rects[('death', 8)], 160).tobytes(),
                         reconstruct(decoded, rects[('death', 9)], 160).tobytes())

    def test_invalid_offset_is_rejected(self):
        atlas = Image.new('RGBA', (30, 30))
        with self.assertRaises(AssertionError):
            reconstruct(atlas, dict(x=0, y=0, w=30, h=30, ox=150, oy=0), 160)

    def test_grade_is_fixed_across_frames_and_preserves_alpha(self):
        source = Image.new('RGBA', (16, 16), (190, 140, 90, 255))
        rest = Image.new('RGBA', (16, 16), (130, 120, 100, 255))
        calibration = fit(rest, source)
        motion = rest.copy(); motion.putpixel((0, 0), (255, 255, 255, 37))
        before, after = grade(rest, calibration), grade(motion, calibration)
        self.assertEqual(before.getpixel((8, 8)), after.getpixel((8, 8)))
        self.assertEqual(after.getchannel('A').tobytes(), motion.getchannel('A').tobytes())


if __name__ == '__main__':
    unittest.main()

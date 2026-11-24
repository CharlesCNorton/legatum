#!/usr/bin/env python3
"""Synthetic checks for critique.py: run with the anim-pilot venv Python."""

import argparse
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

import critique


class CritiqueTest(unittest.TestCase):
    def test_lab_reference_and_offset(self):
        white = critique.rgb_to_lab(np.array([[[255, 255, 255]]]))[0, 0]
        black = critique.rgb_to_lab(np.array([[[0, 0, 0]]]))[0, 0]
        np.testing.assert_allclose(white, [100, 0, 0], atol=0.01)
        np.testing.assert_allclose(black, [0, 0, 0], atol=0.01)
        target = np.zeros((256, 256), dtype=bool)
        target[40:90, 50:80] = True
        moved = critique.shift_array(target, 2, -3)
        score, dx, dy, aligned = critique.best_iou(target, moved)
        self.assertEqual((score, dx, dy), (1.0, -2, 3))
        np.testing.assert_array_equal(aligned, target)

    def test_end_to_end_alpha_and_background_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            painting = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(painting)
            draw.rectangle((50, 40, 79, 89), fill=(120, 75, 40, 255))
            render = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            ImageDraw.Draw(render).rectangle((52, 37, 81, 86), fill=(120, 75, 40, 255))
            paint_path, rest_path = root / "paint.png", root / "rest.png"
            painting.save(paint_path)
            render.save(rest_path)
            frames = root / "frames"
            for clip in critique.CLIPS:
                (frames / clip).mkdir(parents=True)
                render.save(frames / clip / "00.png")
                render.save(frames / clip / "01.png")
            feet = root / "feet.png"
            render.save(feet)
            out = root / "out"
            args = argparse.Namespace(slug="test-unit", painting=paint_path, rest=rest_path,
                                      frames=frames, feet=feet, out=out, round=2)
            for expected_mask in ("alpha", "corner background key"):
                metrics = critique.run(args)
                self.assertEqual(metrics["painting_mask_source"], expected_mask)
                self.assertEqual(metrics["silhouette_iou"], 1.0)
                self.assertEqual(metrics["best_render_offset_px"], {"x": -2, "y": 3})
                self.assertAlmostEqual(metrics["mean_delta_e_cie76"], 0, places=6)
                self.assertTrue(metrics["silhouette_pass"] and metrics["colour_pass"])
                self.assertEqual(metrics["frame_counts"], dict.fromkeys(critique.CLIPS, 2))
                with Image.open(out / "test-unit-round2-side-by-side.png") as side:
                    self.assertEqual(side.size, (512, 256))
                with Image.open(out / "test-unit-round2-contact-sheet.png") as contact:
                    self.assertEqual(contact.size, (320, 910))
                self.assertEqual((out / "test-unit-round2-feet-check.png").read_bytes(), feet.read_bytes())
                self.assertEqual(json.loads((out / "test-unit-round2-metrics.json").read_text()), metrics)
                if expected_mask == "alpha":
                    opaque = Image.new("RGB", (256, 256), (246, 242, 230))
                    opaque.paste(painting, mask=painting.getchannel("A"))
                    opaque.save(paint_path)
            self.assertEqual((out / "test-unit-round2-note.md").read_text().count("### Automated critique"), 2)

    def test_blurred_delta_e_ignores_speckle_but_sees_a_tone_shift(self):
        yy, xx = np.mgrid[0:256, 0:256]
        mask = np.zeros((256, 256), dtype=bool)
        mask[40:200, 60:180] = True
        speckle = np.where(((xx + yy) % 2 == 0)[..., None], (150, 90, 50), (110, 60, 30)).astype(np.uint8)
        shifted = np.roll(speckle, 1, axis=1)
        raw = np.linalg.norm(critique.rgb_to_lab(speckle) - critique.rgb_to_lab(shifted), axis=2)[mask].mean()
        blurred = np.linalg.norm(critique.rgb_to_lab(critique.blurred_rgb(speckle, mask))
                                 - critique.rgb_to_lab(critique.blurred_rgb(shifted, mask)), axis=2)[mask].mean()
        self.assertGreater(raw, 12)
        self.assertLess(blurred, 1.5)
        darker = (speckle * 0.8).astype(np.uint8)
        tone = np.linalg.norm(critique.rgb_to_lab(critique.blurred_rgb(speckle, mask))
                              - critique.rgb_to_lab(critique.blurred_rgb(darker, mask)), axis=2)[mask].mean()
        self.assertGreater(tone, 6)
        flat = np.full((256, 256, 3), 128, dtype=np.uint8)
        np.testing.assert_allclose(critique.blurred_rgb(flat, mask)[mask], 128, atol=0.01)

    def test_regions_report_where_the_colour_is_off(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            painting = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            ImageDraw.Draw(painting).rectangle((50, 40, 149, 199), fill=(150, 90, 50, 255))
            render = painting.copy()
            ImageDraw.Draw(render).rectangle((50, 150, 149, 199), fill=(220, 200, 170, 255))
            painting.save(root / "paint.png")
            render.save(root / "rest.png")
            for clip in critique.CLIPS:
                (root / "frames" / clip).mkdir(parents=True)
                render.save(root / "frames" / clip / "00.png")
            args = argparse.Namespace(slug="test-unit", painting=root / "paint.png", rest=root / "rest.png",
                                      frames=root / "frames", feet=None, out=root / "out", round=1,
                                      region=["top=50,40,150,120", "feet=50,160,150,200", "empty=0,0,10,10"])
            metrics = critique.run(args)
            self.assertLess(metrics["regions"]["top"]["mean_delta_e_blurred"], 0.5)
            self.assertGreater(metrics["regions"]["feet"]["mean_delta_e_blurred"], 30)
            self.assertEqual(metrics["regions"]["empty"], {"box": [0, 0, 10, 10], "overlap_pixels": 0})
            self.assertFalse(metrics["colour_pass"])
            self.assertEqual(metrics["colour_metric"].split()[0], "mean_delta_e_blurred")
            note = (root / "out" / "test-unit-round1-note.md").read_text()
            self.assertIn("Regions (blurred ΔE): top 0.0, feet", note)
            self.assertTrue((root / "out" / "test-unit-round1-deltae-blurred-heatmap.png").is_file())


if __name__ == "__main__":
    unittest.main()

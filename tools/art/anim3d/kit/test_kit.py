"""Delivery edge regression and note handoff contract."""
import json
import tempfile
import numpy as np
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.images import resize_rgba
from kit.report import append_evidence
from kit import atlas, grade, regions
from PIL import Image, ImageDraw


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


def figure(shift=0, colour=(180, 60, 40, 255), size=320):
    """Synthetic sprite: a body, a thin spear and a base, on transparency."""
    image = Image.new('RGBA', (size, size))
    draw = ImageDraw.Draw(image)
    draw.ellipse((90, 250, 230, 290), fill=(233, 207, 160, 255))
    draw.rectangle((130+shift, 90, 190+shift, 260), fill=colour)
    draw.line((210+shift, 40, 210+shift, 270), fill=(90, 90, 100, 255), width=3)
    return image


def clip_frames():
    return {clip: [figure(shift=3*i if i < count-2 or clip != 'death' else 3*(count-2))
                   for i in range(count)] for clip, (count, _, _) in atlas.CLIPS.items()}


class AtlasTests(unittest.TestCase):
    def test_pack_decode_validate_round_trip(self):
        frames = clip_frames()
        data, meta, quality = atlas.pack(frames, anchor=(79.375, 138.125))
        self.assertLessEqual(len(data), atlas.BYTE_LIMIT)
        self.assertIn(quality, atlas.QUALITIES)
        self.assertEqual(sum(len(v) for v in meta['frames'].values()), 40)
        decoded = atlas.validate(data, meta, frames)
        self.assertEqual(decoded['idle'][0].size, (160, 160))
        self.assertEqual(json.loads(json.dumps(meta)), meta)

    def test_validate_rejects_shifted_offset_and_missing_hold(self):
        frames = clip_frames()
        data, meta, _ = atlas.pack(frames, anchor=(80, 138))
        broken = json.loads(json.dumps(meta))
        broken['frames']['move'][3]['ox'] += 1
        with self.assertRaisesRegex(AssertionError, 'move/3'):
            atlas.validate(data, broken, frames)
        moving = clip_frames()
        moving['death'][-1] = figure(shift=60)
        data, meta, _ = atlas.pack(moving, anchor=(80, 138))
        with self.assertRaisesRegex(AssertionError, 'not held'):
            atlas.validate(data, meta, moving)

    def test_pack_refuses_to_exceed_byte_limit(self):
        with self.assertRaisesRegex(RuntimeError, 'exceeds'):
            atlas.pack(clip_frames(), anchor=(80, 138), byte_limit=500)

    def test_static_clip_is_rejected(self):
        frames = clip_frames()
        frames['idle'] = [figure() for _ in range(8)]
        data, meta, _ = atlas.pack(frames, anchor=(80, 138))
        with self.assertRaisesRegex(AssertionError, 'idle: no motion'):
            atlas.validate(data, meta, frames)


class GradeTests(unittest.TestCase):
    def test_identity_when_render_matches_painting(self):
        image = figure(size=256)
        tables = grade.fit(image, image, strength=1)
        self.assertEqual(grade.apply(image, tables).tobytes(), image.tobytes())

    def test_grade_moves_tone_toward_painting_and_keeps_alpha(self):
        painting = figure(colour=(200, 80, 50, 255), size=256)
        render = figure(colour=(120, 60, 60, 255), size=256)
        graded = grade.apply(render, grade.fit(render, painting, strength=.8))
        self.assertEqual(graded.getchannel('A').tobytes(), render.getchannel('A').tobytes())
        r, g, b, _ = graded.getpixel((160, 150))
        self.assertEqual((r, g, b), (184, 76, 52))
        for table in grade.fit(render, painting):
            self.assertEqual(table, sorted(table))

    def test_stale_grade_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            figure(size=256).save(folder/'rest.png'); figure(size=256).save(folder/'painting.png')
            (folder/'unit.blend').write_bytes(b'master v1')
            grade.fit_file(folder/'rest.png', folder/'painting.png', folder/'unit.blend', folder/'grade.json')
            self.assertEqual(grade.load(folder/'grade.json', folder/'unit.blend')['strength'], .8)
            (folder/'unit.blend').write_bytes(b'master v2')
            with self.assertRaisesRegex(AssertionError, 'Stale grade'):
                grade.load(folder/'grade.json', folder/'unit.blend')


class RegionTests(unittest.TestCase):
    def test_region_iou_sees_a_local_change_the_whole_image_hides(self):
        painting = figure(size=256)
        thin = painting.copy()
        ImageDraw.Draw(thin).rectangle((130, 200, 150, 240), fill=(0, 0, 0, 0))
        whole = regions.region_iou(painting, thin)
        legs = regions.region_iou(painting, thin, (120, 195, 200, 245))
        self.assertGreater(whole, .9)
        self.assertLess(legs, whole)
        self.assertEqual(regions.region_iou(painting, painting, (120, 195, 200, 245)), 1.0)

    def test_pale_pixels_and_rgb_error(self):
        image = figure(size=256)
        box = (130, 100, 160, 130)
        self.assertEqual(regions.pale_pixels(image, box), 0)
        patched = image.copy()
        ImageDraw.Draw(patched).rectangle((135, 105, 144, 114), fill=(215, 205, 190, 255))
        self.assertEqual(regions.pale_pixels(patched, box), 100)
        self.assertEqual(regions.region_rgb_mae(image, image, box), 0)
        self.assertGreater(regions.region_rgb_mae(image, patched, box), 0)
        report = regions.compare(image, image, patched, regions={'torso': box}, pale={'patch': box})
        self.assertEqual(report['patch']['pale_pixels'], {'before': 0, 'after': 100})
        self.assertEqual(regions.scale_box((138, 103, 162, 140)), (86, 64, 101, 88))
        self.assertEqual(regions.comparison_sheet([('Painting', image), ('After', patched)]).size, (544, 572))


if __name__ == '__main__':
    unittest.main()

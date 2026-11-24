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
from kit import atlas, feet, grade, part_paint, regions, registration
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

    def test_reviewer_stats_and_prop_width(self):
        image = figure(size=256)
        stats = regions.region_stats(image, (130, 100, 160, 130))
        self.assertEqual(stats['pixels'], 900)
        self.assertEqual(stats['mean_rgb'], [180.0, 60.0, 40.0])
        self.assertEqual(stats['luminance_mean'], stats['luminance_p90'])
        self.assertEqual(regions.region_stats(image, (0, 0, 10, 10)), {'pixels': 0})
        self.assertEqual(regions.span_width(image, 60, 200, 230), 3)

    def test_frame_steps_flags_wasted_and_teleporting_frames(self):
        moving = [figure(shift=4*i) for i in range(8)]
        self.assertEqual(regions.frame_steps(moving+[moving[-1]])['findings'], [])
        wasted = regions.frame_steps(moving[:5]+[moving[4]]*4)
        self.assertEqual(wasted['findings'], ['frames [5, 6, 7] barely change before the held tail'])
        teleport = regions.frame_steps(moving[:4]+[figure(shift=70+4*i) for i in range(4)])
        self.assertEqual(teleport['findings'], ['frames [4] jump more than 2.5x the median step'])
        self.assertEqual(regions.frame_steps([moving[0]]*4)['findings'], ['clip does not move'])


def walk_rows(drift=0.0, speed=1.2):
    """Left foot planted and sliding back at the virtual speed; right foot swinging."""
    rows = []
    for i in range(8):
        y = speed*i/24
        left = {'planted': True, 'ankle': [.12, y, .2], 'sole_z': .106, 'contact_mode': 'heel' if i < 4 else 'toe',
                'contact_point': [.12+drift*i, y, .106], 'heading': 2.0, 'heading_projection_m': .25}
        right = {'planted': False, 'ankle': [-.13, -y, .3], 'sole_z': .106+.02*i, 'contact_mode': 'toe',
                 'contact_point': [-.13, -y, .2], 'heading': 30.0, 'heading_projection_m': .05}
        rows.append({'frame': 25+i, 'feet': {'l': left, 'r': right}})
    return rows


class FeetTests(unittest.TestCase):
    def test_planted_foot_moving_at_virtual_speed_has_no_slip(self):
        checks = feet.measure(walk_rows(), 1.2, .106)
        self.assertAlmostEqual(checks['max_sole_contact_slip_m'], 0, places=9)
        self.assertEqual(checks['planted_samples'], 8)
        self.assertEqual(checks['max_planted_heading_degrees'], 2.0)
        self.assertEqual(checks['max_raw_foot_yaw_degrees'], 30.0)
        self.assertEqual(checks['max_readable_heading_degrees'], 2.0)

    def test_lateral_drift_is_slip_and_fails_the_limit(self):
        checks = feet.measure(walk_rows(drift=.002), 1.2, .106)
        self.assertAlmostEqual(checks['max_sole_contact_slip_m'], .006, places=6)
        checks.update(loop_seam_m=0, max_root_xy_correction_m=.01, max_foot_ik_correction_m=.01, max_sole_translation_m=.01)
        self.assertEqual(len(feet.failures(checks)), 1)
        self.assertIn('max_sole_contact_slip_m', feet.failures(checks)[0])
        self.assertEqual(len(feet.failures({})), len(feet.LIMITS))

    def test_step_width_and_swing_lift(self):
        width = feet.step_width(walk_rows(), rest_width=.5)
        self.assertAlmostEqual(width['mean_m'], .25)
        self.assertAlmostEqual(width['mean_over_rest'], .5)
        lift = feet.swing_lift(walk_rows(), .106)
        self.assertAlmostEqual(lift['r'], .14)
        self.assertEqual(lift['l'], 0.0)


class RegistrationTests(unittest.TestCase):
    def test_fit_recovers_a_known_scale_and_offset(self):
        source = Image.new('RGBA', (640, 640))
        draw = ImageDraw.Draw(source)
        draw.ellipse((200, 520, 460, 590), fill=(233, 207, 160, 255))
        draw.rectangle((270, 150, 380, 540), fill=(170, 60, 40, 255))
        draw.ellipse((300, 250, 420, 370), fill=(200, 150, 60, 255))
        draw.line((240, 60, 240, 560), fill=(150, 110, 70, 255), width=9)
        truth = (2.43, 14.0, -9.0)
        reference = registration.reduce_to_canvas(registration.pad(source), *truth)
        result = registration.fit(source, reference)
        self.assertLess(abs(result['scale']/truth[0]-1), .001)
        self.assertLess(abs(result['x0']-truth[1]), .3)
        self.assertLess(abs(result['y0']-truth[2]), .3)
        self.assertLessEqual(result['error'], result['bbox_estimate']['error'])
        self.assertEqual(registration.registration_tuple(result)[2:4], (0, 0))
        self.assertEqual(registration.registered_reference(source, result).size, (256, 256))


class PartPaintTests(unittest.TestCase):
    def test_push_pull_keeps_owned_pixels_and_fills_holes_from_them(self):
        rgb = np.zeros((64, 64, 3), dtype=np.float32)
        rgb[:, :32] = (200, 40, 30)      # the part's own paint
        rgb[:, 32:] = (20, 200, 220)     # a neighbour's paint it must not inherit
        owned = np.zeros((64, 64), dtype=bool)
        owned[:, :32] = True
        filled = part_paint.part_texture(rgb, owned)
        np.testing.assert_allclose(filled[:, :32], rgb[:, :32], atol=.01)
        np.testing.assert_allclose(filled[:, 40:], np.broadcast_to((200, 40, 30), (64, 24, 3)), atol=1)
        low = part_paint.low_frequency(rgb, owned.astype(np.float32), cell=16)
        self.assertEqual(low.shape, (16, 16, 3))
        np.testing.assert_allclose(low.reshape(-1, 3).mean(0), (200, 40, 30), atol=2)

    def test_palette_runs_dark_to_light_with_increasing_positions(self):
        rng = np.random.default_rng(3)
        value = rng.uniform(.1, 1, size=(4000, 1))
        pixels = value*np.array([[230, 120, 60]])
        result = part_paint.palette(pixels)
        luminance = [np.dot(c, part_paint.LUMA) for c in result['colours']]
        self.assertEqual(luminance, sorted(luminance))
        self.assertEqual(result['positions'], sorted(set(result['positions'])))
        self.assertEqual(len(result['colours']), len(part_paint.QUANTILES))
        lit = part_paint.palette(pixels, light=rng.uniform(.4, .6, size=4000))
        self.assertGreater(lit['positions'][0], .39)
        self.assertLess(lit['positions'][-1], .7)

    def test_masks(self):
        mask = np.zeros((20, 20), dtype=bool)
        mask[8:12, 8:12] = True
        distance = part_paint.grow_distance(mask, 3)
        self.assertEqual((distance[10, 10], distance[10, 13], distance[0, 0]), (0, 2, 4))
        self.assertEqual(int(part_paint.erode(mask, 1).sum()), 4)


if __name__ == '__main__':
    unittest.main()

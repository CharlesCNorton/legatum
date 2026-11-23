#!/usr/bin/env python3
"""CPU-only regression checks; temporary fixtures are never delivered art."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
import pack
import validate
import prepare
from units import UNITS, CLIPS


class PackingTest(unittest.TestCase):
    def test_all_units_contract_frame_placement_and_missing_base(self):
        with tempfile.TemporaryDirectory(prefix='legatum-anim-test-') as tmp:
            root = Path(tmp)
            home = root / 'work'
            with patch.object(pack, 'ROOT', root), patch.object(pack, 'HOME', home), patch.object(validate, 'ROOT', root):
                for slug, cfg in UNITS.items():
                    assets = root / 'app/src/assets/units'
                    assets.mkdir(parents=True, exist_ok=True)
                    base = Image.new('RGBA', (256, 256))
                    ImageDraw.Draw(base).ellipse(cfg['base'], fill='#eedcbc')
                    master = home / 'masters' / slug
                    master.mkdir(parents=True)
                    base.save(master / 'base.png')
                    for row, (clip, (count, _, _)) in enumerate(CLIPS.items()):
                        dest = master / 'foreground' / clip
                        dest.mkdir(parents=True)
                        for frame in range(count):
                            im = Image.new('RGBA', (256, 256))
                            index = min(frame, 8) if clip == 'death' else frame
                            ImageDraw.Draw(im).rectangle((80+index, 60, 135+index, 180), fill=(40+row*35, 50+index*12, 90, 255))
                            im.save(dest / f'{frame:02}.png')
                            if clip == 'idle' and frame == 0:
                                Image.alpha_composite(base, im).save(assets / f'{slug}-256.png')
                    with patch('sys.argv', ['pack.py', slug]), contextlib.redirect_stdout(io.StringIO()):
                        pack.main()
                    atlas = Image.open(assets / 'anim' / f'{slug}.webp').convert('RGBA')
                    report = json.loads((home / 'review' / f'{slug}-pack.json').read_text())
                    self.assertGreaterEqual(report['quality'], 60)
                    for row, (clip, indices) in enumerate(report['source_indices'].items()):
                        for col, frame in enumerate(indices):
                            pixel = atlas.getpixel((col*256+110, row*256+100))
                            expected = (40+row*35, 50+(min(frame, 8) if clip == 'death' else frame)*12, 90)
                            self.assertLess(max(abs(pixel[i]-expected[i]) for i in range(3)), 12, (slug, clip, frame))
                with contextlib.redirect_stdout(io.StringIO()):
                    validate.validate(masters_dir=home / 'masters')
                # Regression for pass 1: a fully clipped stone must fail validation.
                path = assets / 'anim/spearman.webp'
                atlas = Image.open(path).convert('RGBA')
                atlas.paste((0, 0, 0, 0), (0, 204, 256, 256))
                atlas.save(path, lossless=True)
                with self.assertRaisesRegex(AssertionError, 'stone'):
                    validate.validate(['spearman'], masters_dir=home / 'masters')

    def test_stone_occlusion_does_not_hide_movement_or_recolour(self):
        base = Image.new('RGBA', (256, 256))
        ImageDraw.Draw(base).rectangle((60, 230, 195, 242), fill='#eedcbc')
        rim = [(x,y) for y in range(232,240) for x in range(64,192)]
        figure = Image.new('RGBA', base.size)
        ImageDraw.Draw(figure).rectangle((110,220,140,244), fill='#603020')
        frame = Image.alpha_composite(base,figure)
        validate.check_stone(frame, base, rim, figure.getchannel('A'), ('occlusion',))
        for broken in (Image.new('RGBA', base.size), Image.new('RGBA', base.size, '#603020')):
            with self.assertRaisesRegex(AssertionError, 'stone'):
                validate.check_stone(broken, base, rim, figure.getchannel('A'), ('broken',))
        from PIL import ImageChops
        shifted = Image.alpha_composite(ImageChops.offset(base, 0, -5), figure)
        with self.assertRaisesRegex(AssertionError, 'stone'):
            validate.check_stone(shifted, base, rim, figure.getchannel('A'), ('shifted',))
        with self.assertRaisesRegex(AssertionError, 'insufficient exposed stone'):
            validate.check_stone(frame, base, rim, Image.new('L',base.size,255), ('mask',))

    def test_reference_rim_uses_base_alpha_and_ignores_foreground_palette(self):
        base = Image.new('RGBA', (256, 256))
        ImageDraw.Draw(base).ellipse((72, 204, 178, 244), fill='#eedcbc')
        rim = validate.reference_rim(base)
        self.assertGreater(len(rim), 80)
        # A dark fallen figure can cover part of the front rim without changing it.
        figure = Image.new('RGBA', base.size)
        ImageDraw.Draw(figure).rectangle((105, 219, 143, 245), fill='#5b322a')
        frame = Image.alpha_composite(base, figure)
        validate.check_stone(frame, base, rim, figure.getchannel('A'), ('dark figure',))
        for p in rim:
            if figure.getchannel('A').getpixel(p) == 0:
                frame.putpixel(p, (30, 40, 50, 255))
        with self.assertRaisesRegex(AssertionError, 'stone pigment/position changed'):
            validate.check_stone(frame, base, rim, figure.getchannel('A'), ('changed base',))

    def test_prepared_layers_keep_source_coverage_and_own_loose_fragments(self):
        from PIL import ImageChops
        with tempfile.TemporaryDirectory() as tmp, patch.object(prepare, 'HOME', Path(tmp)):
            for slug,cfg in UNITS.items():
                with patch('sys.argv', ['prepare.py',slug]), contextlib.redirect_stdout(io.StringIO()):
                    prepare.main()
                master=Path(tmp)/'masters'/slug
                source=Image.open(master/'painting.png').convert('RGBA')
                allowed=prepare.polygon([(0,0),(256,0),(256,cfg['base'][1]-1),(0,cfg['base'][1]-1)])
                for foot in cfg['feet']: allowed=ImageChops.lighter(allowed,prepare.polygon(foot))
                expected=ImageChops.multiply(source.getchannel('A'),allowed)
                coverage=Image.open(master/'body.png').getchannel('A')
                for name,*_ in cfg['parts']:
                    coverage=ImageChops.lighter(coverage,Image.open(master/(name+'.png')).getchannel('A'))
                self.assertIsNone(ImageChops.subtract(expected,coverage).getbbox(),slug)
                # No scraps of limbs/kit outside the torso region remain on body.
                torso=prepare.polygon(cfg['body_region'])
                loose=ImageChops.subtract(Image.open(master/'body.png').getchannel('A'),torso)
                self.assertIsNone(loose.getbbox(),slug)

    def test_alpha_coverage_error_and_hidden_rgb(self):
        im = Image.new('RGBA', (256, 1))
        for a in range(256): im.putpixel((a, 0), (255, 123, 77, a))
        cleaned = pack.clean_alpha(im)
        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(cleaned.getpixel((255, 0)), (255, 123, 77, 255))
        self.assertLessEqual(max(abs(a-cleaned.getpixel((a, 0))[3]) for a in range(256)), 4)

    def test_profiles_preserve_duration_strike_and_death_hold(self):
        for profile in pack.PROFILES:
            self.assertIn(profile['move'], [list(range(8)), [0, 2, 4, 6]])
            for clip, indices in profile.items():
                n, fps, loop = CLIPS[clip]
                data = pack.clip_metadata(clip, indices, 0)
                old = n/fps if loop else (n-1)/fps
                new = len(indices)/data['fps'] if loop else (len(indices)-1)/data['fps']
                self.assertAlmostEqual(old, new)
            self.assertTrue({0, 2, 3, 4, 9} <= set(profile['attack']))
            self.assertEqual(profile['death'][-2:], [8, 9])

    def test_budget_reduces_frames_without_crossing_quality_floor(self):
        im = Image.new('RGBA', (256, 256))
        frames = {c: [im] * n for c, (n, _, _) in CLIPS.items()}
        with patch.object(pack, 'encode', side_effect=[b'x'*200001, b'x'*200001, b'x'*200001, b'x'*190000, b'x'*200001, b'x'*195000]) as encoder:
            data, profile, quality, _ = pack.fit_atlas(frames)
        self.assertEqual(len(data), 195000)
        self.assertEqual(profile, pack.PROFILES[-1])
        self.assertEqual(quality, 70)
        self.assertTrue(all(call.args[1] >= 60 for call in encoder.call_args_list))

    def test_budget_failure_keeps_previous_delivery(self):
        im = Image.new('RGBA', (256, 256))
        frames = {c: [im] * n for c, (n, _, _) in CLIPS.items()}
        with patch.object(pack, 'encode', return_value=b'x'*200001):
            with self.assertRaisesRegex(RuntimeError, 'no output replaced'):
                pack.fit_atlas(frames)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            existing = output / 'spearman.webp'
            existing.write_bytes(b'previous delivery')
            with patch('sys.argv', ['pack.py', 'spearman', '--output-dir', str(output)]), patch.object(pack.Image, 'open', return_value=im), patch.object(pack, 'fit_atlas', side_effect=RuntimeError('budget')):
                with self.assertRaisesRegex(RuntimeError, 'budget'): pack.main()
            self.assertEqual(existing.read_bytes(), b'previous delivery')


if __name__ == '__main__': unittest.main()

"""Integration regressions against the current candidate, in an isolated copy.

Run after finish.py pack. Never mutate the real delivery or source masters.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import subprocess
from PIL import Image
import finish
import frame_jobs


class CheckpointChecks(unittest.TestCase):
    def test_interrupted_stage_keeps_verified_frame_but_no_manifest(self):
        with tempfile.TemporaryDirectory(prefix='musketman-checkpoint-') as directory:
            root = Path(directory)
            (root/'clips').mkdir()
            (root/'clips/hit.blend').write_bytes(b'isolated source fixture')
            out = root/'renders/e-hit'
            out.mkdir(parents=True)
            with mock.patch.object(frame_jobs, 'MASTER', root), mock.patch.dict(os.environ, {'RESOLUTION': '16'}):
                expected = dict(frame_jobs.settings('e-hit'), index=0, frame=1)
                path = out/'00.png'
                Image.new('RGBA', (16, 16), (50, 30, 20, 255)).save(path)
                path.with_suffix('.json').write_text(json.dumps(dict(expected, png_sha256=frame_jobs.sha(path))))
                (out/'render.json').write_text('old completed stage')
                # Frame 0 must resume without a Blender call. A trapped frame 1
                # is retried once, and must not leave a completed-stage receipt.
                failed = subprocess.CompletedProcess(['blender'], 133)
                with mock.patch.object(frame_jobs.subprocess, 'run', return_value=failed) as execute:
                    with self.assertRaises(subprocess.CalledProcessError):
                        frame_jobs.run('e-hit')
                    self.assertEqual(execute.call_count, 2)
                    self.assertTrue(all(call.kwargs['env']['RENDER_INDEX'] == '1' for call in execute.call_args_list))
                self.assertFalse((out/'render.json').exists())
                self.assertTrue(frame_jobs.matches(path, expected))
                self.assertFalse(frame_jobs.matches(path, dict(expected, device='other-device')))
                path.write_bytes(path.read_bytes()+b'changed')
                self.assertFalse(frame_jobs.matches(path, expected))


class DeliveryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = Path.cwd()
        cls.original_m, cls.original_v = finish.M, finish.V
        cls.temp = tempfile.TemporaryDirectory(prefix='musketman-delivery-')
        cls.root = Path(cls.temp.name)
        finish.M, finish.V = cls.root/'masters', cls.root/'review'
        finish.M.mkdir(); finish.V.mkdir()
        for name in ('renders', 'clips'):
            shutil.copytree(cls.original_m/name, finish.M/name)
        for name in ('musketman.blend', 'grade.json', 'pack.json'):
            shutil.copy2(cls.original_m/name, finish.M/name)
        cls.output = cls.root/'app/src/assets/units/anim'
        cls.output.mkdir(parents=True)
        for ext in ('json', 'webp'):
            shutil.copy2(cls.cwd/f'app/src/assets/units/anim/{finish.SLUG}.{ext}', cls.output)
        os.chdir(cls.root)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.cwd)
        finish.M, finish.V = cls.original_m, cls.original_v
        cls.temp.cleanup()

    def corrupt(self, path, replacement, message=None):
        old = path.read_bytes()
        try:
            path.write_bytes(replacement)
            with self.assertRaises(AssertionError):
                finish.validate()
        finally:
            path.write_bytes(old)

    def test_valid_delivery(self):
        finish.validate()

    def test_changed_atlas_rejected(self):
        path = self.output/f'{finish.SLUG}.webp'
        self.corrupt(path, path.read_bytes()+b'changed')

    def test_changed_source_frame_rejected(self):
        path = finish.M/'renders/e-move/00.png'
        self.corrupt(path, path.read_bytes()+b'changed')

    def test_changed_rest_rejected(self):
        path = finish.M/'renders/c-textured-lit/00.png'
        self.corrupt(path, path.read_bytes()+b'changed')

    def test_wrong_trim_detected_independently_of_hash(self):
        path = self.output/f'{finish.SLUG}.json'
        report_path = finish.M/'pack.json'
        old, old_report = path.read_bytes(), report_path.read_bytes()
        try:
            metadata = json.loads(old)
            metadata['clips']['idle']['rects'][0]['ox'] += 1
            path.write_text(json.dumps(metadata))
            report = json.loads(old_report)
            report['metadata_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            report_path.write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError, 'alpha/offset mismatch'):
                finish.validate()
        finally:
            path.write_bytes(old); report_path.write_bytes(old_report)

    def test_cpu_cannot_issue_gpu_receipt(self):
        path=finish.M/'renders/b-plain/render.json'
        original=path.read_bytes()
        try:
            data=json.loads(original);data['device']='CPU';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError, 'not final GPU output'):
                finish.gpu_receipt()
        finally:
            path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()

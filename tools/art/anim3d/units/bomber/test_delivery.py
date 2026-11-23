"""Regression checks for stale delivery and the explicit GPU gate (no Blender)."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('deliver.py'))
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryChecks(unittest.TestCase):
    def test_grade_is_monotone_and_bounded(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(delivery, 'M', Path(folder)):
            (Path(folder) / 'bomber.blend').write_bytes(b'fixture')
            luts = delivery.grade_luts(delivery.REF)
            for lut in luts:
                self.assertEqual(lut, sorted(lut))
                self.assertTrue(all(abs(a-b) <= 24 for a,b in enumerate(lut)))

    def test_cpu_master_is_rejected_by_gpu_gate(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(delivery, 'M', Path(folder)):
            raw = Path(folder) / 'raw/512/b'
            raw.mkdir(parents=True)
            (raw/'render.json').write_text(json.dumps({'engine':'CYCLES','device':'CPU','resolution':512,'samples':96}))
            with self.assertRaisesRegex(AssertionError, 'not final GPU512'):
                delivery.gpu_check()

    def test_stale_master_is_rejected_before_review(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(delivery, 'M', Path(folder)):
            master = Path(folder)
            (master/'bomber.blend').write_bytes(b'new master')
            raw = master/'raw/512/c'
            raw.mkdir(parents=True)
            (raw/'render.json').write_text(json.dumps({'master_sha256':'old master'}))
            with self.assertRaisesRegex(RuntimeError, 'Missing complete render'):
                delivery.review('c')

    def test_gpu_script_records_missing_input_without_rendering(self):
        with tempfile.TemporaryDirectory() as folder:
            env=dict(os.environ,ANIM_ROOT=folder,ROUND='preflight')
            result=subprocess.run(['tools/art/anim3d/units/bomber/gpu.sh'],env=env,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            review=Path(folder)/'review/3d-v2'
            self.assertIn('failed round=preflight', (review/'bomber-gpu-status.txt').read_text())
            self.assertTrue((review/'bomber-gpu-roundpreflight.log').exists())
            self.assertFalse((review/'bomber-gpu-roundpreflight.json').exists())

    def test_video_metadata_is_checked(self):
        invalid = {'streams':[{'codec_name':'h264','pix_fmt':'yuv420p','width':1600,'height':348,'nb_frames':'239'}], 'format':{'duration':'8'}}
        with patch.object(delivery.subprocess,'check_output',return_value=json.dumps(invalid).encode()):
            with self.assertRaises(AssertionError):
                delivery.verify_video(Path('test.mp4'))


if __name__ == '__main__':
    unittest.main()

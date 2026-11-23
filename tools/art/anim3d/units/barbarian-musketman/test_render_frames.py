"""Exercise interruption recovery without a GPU or touching real masters."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import render_frames as render


class FrameRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.blend = self.root / 'scene.blend'
        self.blend.write_bytes(b'blend-v1')
        self.patches = [patch.object(render, 'M', self.root),
                        patch.object(render, 'stage_blend', return_value=self.blend),
                        patch.object(render, 'review'),
                        patch.dict(os.environ, RESOLUTION='16', SAMPLES='3', CYCLES_DEVICE='CPU')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def succeed(self, args, env):
        path = self.root / 'renders/e-idle' / f'{int(env["FRAME_INDEX"]):02}.png'
        Image.new('RGBA', (16, 16), (100, 80, 60, 255)).save(path)
        return subprocess.CompletedProcess(args, 0)

    def test_restart_reuses_only_matching_completed_frames(self):
        with patch.object(render.subprocess, 'run', side_effect=self.succeed) as run:
            render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 2)
            render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 2)
            (self.root/'renders/e-idle/01.png').write_bytes(b'broken')
            render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 3)
            self.blend.write_bytes(b'blend-v2')
            render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 5)

    def test_trap_retry_is_bounded_and_does_not_publish_partial_stage(self):
        with patch.object(render.subprocess, 'run', return_value=subprocess.CompletedProcess([], 133)) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 2)
        self.assertFalse((self.root/'renders/e-idle/render.json').exists())

    def test_resume_after_interruption(self):
        def interrupted(args, env):
            return self.succeed(args, env) if env['FRAME_INDEX']=='0' else subprocess.CompletedProcess(args, 1)
        with patch.object(render.subprocess, 'run', side_effect=interrupted):
            with self.assertRaises(subprocess.CalledProcessError):
                render.render_stage('e-idle', [1, 2])
        self.assertFalse((self.root/'renders/e-idle/render.json').exists())
        with patch.object(render.subprocess, 'run', side_effect=self.succeed) as run:
            render.render_stage('e-idle', [1, 2])
            self.assertEqual(run.call_count, 1)
        self.assertEqual(json.loads((self.root/'renders/e-idle/render.json').read_text())['frames'], 2)


if __name__ == '__main__':
    unittest.main()

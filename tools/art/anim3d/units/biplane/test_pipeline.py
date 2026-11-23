"""Regression checks for interrupted/stale GPU handoffs, without Blender."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import preflight

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.master=self.root/'masters/biplane';self.master.mkdir(parents=True)
        self.assets=self.root/'assets/biplane';self.assets.mkdir(parents=True)
        self.unit=self.root/'unit';self.unit.mkdir()
        self.patcher=patch.multiple(preflight,ROOT=self.root,M=self.master,UNIT=self.unit)
        self.patcher.start()
        (self.master/'biplane.blend').write_bytes(b'current master')
        (self.master/'unpainted.blend').write_bytes(b'plain master')
        (self.assets/'projection.png').write_bytes(b'painting')
        (self.unit/'scene.py').write_text('# original geometry')
        (self.master/'inputs.json').write_text(json.dumps({'projection.png':preflight.sha(self.assets/'projection.png')}))
        (self.master/'build-inputs.json').write_text(json.dumps({'master_sha256':preflight.sha(self.master/'biplane.blend'),'scripts':{'scene.py':preflight.sha(self.unit/'scene.py')}}))
    def tearDown(self):
        self.patcher.stop();self.tmp.cleanup()
    def test_matching_inputs(self):preflight.inputs()
    def test_changed_geometry_requires_rebuild(self):
        (self.unit/'scene.py').write_text('# changed geometry')
        with self.assertRaisesRegex(AssertionError,'rebuild required'):preflight.inputs()
    def test_changed_painting_rejected(self):
        (self.assets/'projection.png').write_bytes(b'different painting')
        with self.assertRaisesRegex(AssertionError,'changed asset'):preflight.inputs()
    def test_changed_master_rejected(self):
        (self.master/'biplane.blend').write_bytes(b'changed blend')
        with self.assertRaisesRegex(AssertionError,'Master changed'):preflight.inputs()
    def test_cpu512_does_not_establish_gpu_pass(self):
        raw=self.master/'raw/b';raw.mkdir(parents=True)
        (raw/'render.json').write_text(json.dumps({'engine':'CYCLES','device':'CPU','resolution':512}))
        with self.assertRaisesRegex(AssertionError,'not GPU512'):preflight.gpu()
    def test_old_gpu_source_rejected(self):
        raw=self.master/'raw/b';raw.mkdir(parents=True)
        (raw/'render.json').write_text(json.dumps({'engine':'CYCLES','device':'GPU','resolution':512,'samples':64,'blend_sha256':'stale'}))
        with self.assertRaisesRegex(AssertionError,'stale source'):preflight.gpu()

if __name__=='__main__':unittest.main()

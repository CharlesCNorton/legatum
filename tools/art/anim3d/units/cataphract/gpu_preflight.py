"""Fail before a host pass if Metal is unavailable; never silently use CPU."""
import bpy, os, json, hashlib
from pathlib import Path
root=Path(os.environ['ANIM_ROOT'])
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for name,digest in lock['files'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,('Changed source input',name)
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
gpus=[d.name for d in prefs.devices if d.type=='METAL']
assert gpus,'Metal GPU required for cataphract final pass; CPU previews are separate'
print('CATAPHRACT_GPU_PREFLIGHT',bpy.app.version_string,gpus)

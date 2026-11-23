"""Fail before a host pass if Metal is unavailable; never silently use CPU."""
import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
gpus=[d.name for d in prefs.devices if d.type=='METAL']
assert gpus,'Metal GPU required for cataphract final pass; CPU previews are separate'
print('CATAPHRACT_GPU_PREFLIGHT',bpy.app.version_string,gpus)

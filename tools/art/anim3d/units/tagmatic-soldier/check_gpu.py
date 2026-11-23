"""Fail before rebuilding if the requested host Metal device is absent."""
import bpy
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
devices = [d for d in prefs.devices if d.type == 'METAL']
if not devices:
    raise RuntimeError('Tagmatic final pass requires Metal GPU; no CPU fallback')
print('METAL_GPU_READY', [d.name for d in devices])

"""Fail before overwriting masters if the explicitly requested GPU is absent."""
import bpy

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
gpu = [d for d in prefs.devices if d.type == 'METAL']
if not gpu:
    raise RuntimeError('Requested Metal GPU is unavailable; no CPU fallback')
print('GPU PREFLIGHT', [d.name for d in gpu])

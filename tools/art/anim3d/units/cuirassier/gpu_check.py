"""Fail before expensive rebuilds when the requested host GPU is unavailable."""
import bpy

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
assert any(device.type == 'METAL' for device in prefs.devices), 'Metal GPU required; CPU previews are not a final GPU pass'
print('METAL_GPU_AVAILABLE')

"""Fail before changing masters if the requested Metal device is unavailable."""
import bpy
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
assert any(d.type == 'METAL' for d in prefs.devices), 'No Metal Cycles GPU; CPU fallback is forbidden'
print('CAVALRY_METAL_PREFLIGHT_OK')

"""Fail before a costly rebuild if the requested final device is unavailable."""
import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.get_devices()
assert any(d.type=='METAL' for d in prefs.devices), 'Metal GPU required; refusing CPU fallback'
print('GPU_PREFLIGHT_OK', [(d.name,d.type) for d in prefs.devices if d.type=='METAL'])

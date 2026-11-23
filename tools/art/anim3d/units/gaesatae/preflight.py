"""Require an actual Cycles GPU before touching saved masters."""
import bpy, os
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type=os.environ.get('CYCLES_BACKEND','METAL');prefs.get_devices()
assert any(d.type!='CPU' for d in prefs.devices),'Requested GPU unavailable; refusing CPU fallback'
print('GPU_PREFLIGHT_OK',[(d.name,d.type) for d in prefs.devices])

"""Fail before modifying CPU evidence when the lead host cannot expose Metal."""
import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.get_devices()
devices=[d.name for d in prefs.devices if d.type=='METAL']
assert devices, 'Metal GPU unavailable; CPU evidence was preserved. Run gpu.sh on the lead host.'
print('Metal devices:', devices)

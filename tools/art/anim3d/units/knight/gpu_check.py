import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL';prefs.get_devices()
assert any(d.type=='METAL' for d in prefs.devices),'Metal GPU unavailable; CPU fallback is forbidden for gpu.sh'
print('METAL_AVAILABLE')

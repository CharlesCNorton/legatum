"""Discover Metal under a CPU startup slot before reserving the GPU render slot."""
import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.get_devices()
metal=[d.name for d in prefs.devices if d.type=='METAL']
if not metal:raise RuntimeError('Metal GPU unavailable; run gpu.sh on the lead host. No CPU fallback.')
print('METAL PREFLIGHT PASS',metal)

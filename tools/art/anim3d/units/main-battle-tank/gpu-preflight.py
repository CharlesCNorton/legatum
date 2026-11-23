"""Fail before touching render outputs when the host has no Metal Cycles device."""
import bpy
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.get_devices()
devices=[d for d in prefs.devices if d.type=='METAL']
if not devices:raise RuntimeError('Tank GPU pass requires a Metal Cycles device; CPU previews remain untouched')
print('METAL READY', [d.name for d in devices])

"""Reject unavailable GPU before rebuilding or replacing any review evidence."""
import bpy, os
prefs=bpy.context.preferences.addons['cycles'].preferences
backend=os.environ.get('CYCLES_BACKEND','METAL');prefs.compute_device_type=backend;prefs.get_devices()
devices=[d for d in prefs.devices if d.type==backend]
assert devices,f'No {backend} device; no CPU fallback'
print('GPU_READY',backend,[d.name for d in devices])

"""Fail early on a host without the requested GPU, before any cloth rebakes."""
import os
import bpy

bpy.context.scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
backend = os.environ.get('CYCLES_BACKEND', 'METAL')
prefs.compute_device_type = backend
prefs.get_devices()
devices = [d for d in prefs.devices if d.type == backend]
assert devices, f'No Cycles {backend} GPU; run gpu.sh on the GPU host'
for device in prefs.devices:
    device.use = device in devices
print('SPEARMAN_GPU_PREFLIGHT', bpy.app.version_string, backend,
      [d.name for d in devices], flush=True)

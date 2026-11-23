"""Fail before destructive work if the requested GPU cannot actually be selected."""
import bpy
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
devices = [d for d in prefs.devices if d.type == 'METAL']
if not devices:
    raise RuntimeError('Metal GPU required; this sandbox can run CPU previews only')
for device in prefs.devices:
    device.use = device.type == 'METAL'
# Enumerated hardware is insufficient in a sandbox; prove the render context.
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = 16
scene.render.resolution_percentage = 100
assert scene.camera, 'Factory-startup camera is required by preflight'
bpy.ops.render.render()
print('GPU_PREFLIGHT_PASS', [d.name for d in devices])

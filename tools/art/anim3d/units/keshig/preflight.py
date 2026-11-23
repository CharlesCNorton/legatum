import bpy
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
assert any(d.type=='METAL' for d in p.devices),'Metal GPU required; no CPU fallback'
for d in p.devices:d.use=d.type=='METAL'
print('KESHIG_METAL_READY')

"""Serial renders with explicit device provenance and exact terminal holds."""
import bpy
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from mathutils import Vector

R = Path(os.environ['ANIM_ROOT'])
M = R / 'masters/fighter'
stage = sys.argv[sys.argv.index('--') + 1]
size = int(os.environ.get('RESOLUTION', '256'))
folder = M / 'renders' / str(size) / stage
folder.mkdir(parents=True, exist_ok=True)
manifest = folder / 'render.json'
manifest.unlink(missing_ok=True)
clip = stage[2:] if stage.startswith('e-') else ('move' if stage == 'g' else None)
blend = M / (clip + '.blend' if clip else ('plain.blend' if stage == 'b' else 'fighter.blend'))
bpy.ops.wm.open_mainfile(filepath=str(blend))
sc = bpy.context.scene
if sc.camera is None:
    raise RuntimeError('No render camera')
engine = os.environ.get('RENDER_ENGINE', 'CYCLES')
sc.render.engine = engine
if engine == 'CYCLES':
    sc.cycles.device = os.environ.get('CYCLES_DEVICE', 'CPU')
    sc.cycles.samples = int(os.environ.get('SAMPLES', '8'))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 5
    if sc.cycles.device == 'GPU':
        backend = os.environ.get('CYCLES_BACKEND', 'METAL')
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = backend
        prefs.get_devices()
        gpu = [d for d in prefs.devices if d.type == backend]
        if not gpu:
            raise RuntimeError(f'{backend} device unavailable; no CPU fallback')
        for d in prefs.devices:
            d.use = d.type == backend
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.resolution_percentage = 100
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '8'
sc.render.film_transparent = True
# Finite shutter softens propeller aliasing without replacing solid blades with a disc.
sc.render.use_motion_blur = stage.startswith('e-') and clip in ('idle', 'move', 'attack')
sc.render.motion_blur_shutter = .65
if stage == 'b':
    clay = bpy.data.materials.new('Plain clay')
    clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.46, .45, .41, 1)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.startswith(('BASE', 'DISPLAY', 'FX-')):
            o.data.materials.clear()
            o.data.materials.append(clay)
if clip:
    meta = json.loads((M / 'clips.json').read_text())
    assert meta['source_sha256'] == hashlib.sha256((M / 'fighter.blend').read_bytes()).hexdigest(), 'Stale clips'
    frames = list(range(1, meta['clips'][clip]['frames'] + 1))
else:
    frames = [1]
views = ('top', 'front') if stage == 'g' else ('hero',)
outputs = []
for view in views:
    if view != 'hero':
        target = Vector((0, 0, 1.9))
        offset = Vector((0, 0, 10)) if view == 'top' else Vector((10, 0, .2))
        sc.camera.location = target + offset
        sc.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
        horizontal=sc.camera.rotation_euler.to_matrix() @ Vector((1,0,0))
        vertical=sc.camera.rotation_euler.to_matrix() @ Vector((0,1,0))
        extent=0.0
        for sample in frames:
            sc.frame_set(sample)
            for obj in sc.objects:
                if obj.type!='MESH' or obj.hide_render:continue
                for corner in obj.bound_box:
                    point=obj.matrix_world @ Vector(corner)-target
                    extent=max(extent,abs(point.dot(horizontal)),abs(point.dot(vertical)))
        sc.camera.data.ortho_scale=2*extent*1.08
    previous_state = None
    for i, f in enumerate(frames):
        sc.frame_set(f)
        name = f'{view}-{i:03d}.png' if stage == 'g' else f'{i:03d}.png'
        path = folder / name
        # Check every rendered object's full transform/visibility before copying a hold.
        state = [(o.name, tuple(v for row in o.matrix_world for v in row), o.hide_render)
                 for o in sc.objects if o.type in ('MESH', 'LIGHT', 'CAMERA')]
        state += [(o.name, tuple(k.value for k in o.data.shape_keys.key_blocks))
                  for o in sc.objects if o.type == 'MESH' and o.data.shape_keys]
        if clip == 'death' and i >= 8 and state == previous_state:
            shutil.copyfile(folder / outputs[-1], path)
        else:
            sc.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
        previous_state = state
        outputs.append(name)
manifest.write_text(json.dumps({
    'stage': stage, 'resolution': size, 'engine': engine,
    'device': sc.cycles.device if engine == 'CYCLES' else 'GPU',
    'samples': sc.cycles.samples,
    'motion_blur': sc.render.use_motion_blur,
    'shutter': sc.render.motion_blur_shutter,
    'blend_sha256': hashlib.sha256(blend.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256((M / 'fighter.blend').read_bytes()).hexdigest(),
    'frames': {n: hashlib.sha256((folder / n).read_bytes()).hexdigest() for n in outputs},
}, indent=2))
print('RENDER COMPLETE', stage, size)

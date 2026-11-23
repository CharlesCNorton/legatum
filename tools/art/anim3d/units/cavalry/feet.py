"""Actual evaluated hooves, top/front cutaway views over the complete move cycle."""
import bpy, os, json, hashlib
from pathlib import Path
from mathutils import Vector

root = Path(os.environ['ANIM_ROOT']); master = root/'masters/cavalry'
clip = master/'clips/move.blend'
bpy.ops.wm.open_mainfile(filepath=str(clip)); scene = bpy.context.scene
assert json.loads((master/'clips/move.json').read_text())['source_master_sha256'] == hashlib.sha256((master/'cavalry.blend').read_bytes()).hexdigest()
scene.render.engine = 'CYCLES'; scene.cycles.device = os.environ.get('CYCLES_DEVICE', 'CPU')
if scene.cycles.device == 'GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    assert any(d.type == 'METAL' for d in prefs.devices)
    for device in prefs.devices: device.use = device.type == 'METAL'
resolution = int(os.environ.get('RESOLUTION', '192')); samples = int(os.environ.get('SAMPLES', '4'))
scene.cycles.samples = samples; scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = resolution
scene.render.resolution_percentage = 100; scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
out = master/'feet'; out.mkdir(exist_ok=True); (out/'manifest.json').unlink(missing_ok=True)
horse = bpy.data.objects['Horse']
for ob in scene.objects:
    if ob.type in {'MESH','CURVE'}: ob.hide_render = True
clay = bpy.data.materials.new('Foot diagnostic warm dark clay'); clay.use_nodes = True
shader = clay.node_tree.nodes['Principled BSDF']; shader.inputs['Base Color'].default_value = (.12,.07,.035,1)
shader.inputs['Roughness'].default_value = .7
records = []
for i in range(8):
    scene.frame_set(i+1); bpy.context.view_layer.update()
    ev = horse.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    coords = [ev.matrix_world @ v.co for v in me.vertices]
    # Cutaway removes only the occluding upper body from diagnostic copies.
    faces = [tuple(p.vertices) for p in me.polygons if all(coords[v].z < .72 for v in p.vertices)]
    mesh = bpy.data.meshes.new('Evaluated lower legs'); mesh.from_pydata(coords, [], faces); mesh.update()
    ev.to_mesh_clear()
    feet = bpy.data.objects.new('Evaluated feet review only', mesh); scene.collection.objects.link(feet); mesh.materials.append(clay)
    for p in mesh.polygons: p.use_smooth = True
    groups = {}
    for name in ['FF.L', 'FF.R', 'FFB.L', 'FFB.R']:
        index = horse.vertex_groups[name].index
        indices = [v.index for v in horse.data.vertices if any(g.group == index and g.weight > .5 for g in v.groups)]
        points = [coords[k] for k in indices]
        low = min(p.z for p in points)
        sole = [p for p in points if p.z < low+.025]
        center = sum(sole, Vector())/len(sole)
        groups[name] = {'sole_center':list(center), 'lowest_z':low}
    records.append(groups)
    for view, pos, target, scale in [('top',(0,.1,6),(0,.1,0),3), ('front',(0,-6,.5),(0,0,.5),2.4)]:
        camera = scene.camera; camera.location = pos
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type = 'ORTHO'; camera.data.ortho_scale = scale; camera.data.shift_x = 0; camera.data.shift_y = 0
        dest = out/view; dest.mkdir(exist_ok=True)
        scene.render.filepath = str(dest/f'{i:03}.png'); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(feet, do_unlink=True); bpy.data.meshes.remove(mesh)
manifest = {'engine':'CYCLES', 'device':scene.cycles.device, 'resolution':resolution, 'samples':samples,
            'clip_sha256':hashlib.sha256(clip.read_bytes()).hexdigest(), 'frames':8,
            'method':'Evaluated lower-leg cutaway, top and front; native Quaternius foot axes unchanged',
            'sole_samples':records}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('CAVALRY_FEET_RENDERED')

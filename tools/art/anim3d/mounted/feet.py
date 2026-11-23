"""Render actual deformed lower limbs from above and the travel direction.

These are diagnostic copies of each sampled mesh, not skeleton stick figures.
Upper surfaces are omitted only in the diagnostic copy so hooves remain visible.
No motion, bone orientation, source geometry or delivery material is modified.
"""
import hashlib
import json
import os
from pathlib import Path
import bpy
from mathutils import Vector

root = Path(os.environ['ANIM_ROOT'])
blend = root/'masters/horseman-3d/clips/move.blend'
out = root/'masters/horseman/feet-check'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene
horse = bpy.data.objects['Horse']
frames = json.loads(scene['sample_frames'])
assert len(frames)==8
names = ('front.L','front.R','back.L','back.R')
colours = ((.12,.40,.68,1),(.08,.50,.32,1),(.66,.27,.08,1),(.52,.16,.44,1))
materials = []
for name,colour in zip(names,colours):
    material = bpy.data.materials.new('Diagnostic '+name)
    material.diffuse_color = colour
    material.use_nodes = True
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colour
    material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8
    materials.append(material)


def family(vertex):
    weights = [0.,0.,0.,0.]
    for g in vertex.groups:
        name = horse.vertex_groups[g.group].name
        for i,key in enumerate(names):
            front,side = key.split('.')
            prefixes = ('Front','FF.','IKFront') if front=='front' else ('Back','FFB.','IKBack')
            if name.endswith('.'+side) and name.startswith(prefixes):
                weights[i] += g.weight
    return max(range(4),key=lambda i:weights[i])


samples = []
for frame in frames:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    obj = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    points = [obj.matrix_world@v.co for v in mesh.vertices]
    groups = [family(v) for v in mesh.vertices]
    faces,assignments = [],[]
    hoof = [set() for _ in names]
    for polygon in mesh.polygons:
        indices = list(polygon.vertices)
        group = max(range(4),key=lambda i:sum(groups[v]==i for v in indices))
        if max(points[v].z for v in indices)<.85:
            faces.append(indices)
            assignments.append(group)
        if mesh.materials[polygon.material_index].name=='Horn hooves':
            hoof[group].update(indices)
    measurements = {}
    for name,ids in zip(names,hoof):
        assert ids,name
        floor = min(points[i].z for i in ids)
        sole = [points[i] for i in ids if points[i].z<floor+.025]
        centre = sum(sole,Vector())/len(sole)
        measurements[name] = {'sole_z':floor,'sole_centroid':list(centre),'support':floor<.135}
    samples.append((frame,[tuple(p) for p in points],faces,assignments,measurements))
    obj.to_mesh_clear()

for obj in scene.objects:
    if obj.type not in ('LIGHT','CAMERA'):
        obj.hide_render = True
# One real finite floor, with a physical grid to expose stance drift.
floor_mat = bpy.data.materials.new('Diagnostic cream floor')
floor_mat.diffuse_color = (.72,.64,.48,1)
floor_mat.use_nodes = True
floor_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72,.64,.48,1)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.08))
floor = bpy.context.object
floor.name = 'Diagnostic floor'
floor.dimensions = (3,3,.06)
floor.data.materials.append(floor_mat)
grid_mat = bpy.data.materials.new('Diagnostic grid')
grid_mat.diffuse_color = (.24,.22,.18,1)
for axis in (0,1):
    for i in range(-6,7):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(i*.25 if axis==0 else 0,0 if axis==0 else i*.25,.113))
        obj = bpy.context.object
        obj.name = 'Diagnostic quarter metre grid'
        obj.dimensions = (.004,3,.004) if axis==0 else (3,.004,.004)
        obj.data.materials.append(grid_mat)
scene.render.engine = 'CYCLES'
scene.cycles.device = os.environ.get('CYCLES_DEVICE','CPU')
if scene.cycles.device=='GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    assert any(d.type=='METAL' for d in prefs.devices),'No Metal; no CPU fallback'
    for device in prefs.devices:
        device.use = device.type=='METAL'
scene.cycles.samples = int(os.environ.get('SAMPLES','8'))
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 3
scene.render.resolution_x = scene.render.resolution_y = int(os.environ.get('FEET_RESOLUTION','128'))
scene.render.resolution_percentage = 100
scene.render.use_persistent_data = True
camera = scene.camera
for index,(frame,points,faces,assignments,_) in enumerate(samples):
    mesh = bpy.data.meshes.new('Actual sampled lower limbs')
    mesh.from_pydata(points,[],faces)
    for material in materials:
        mesh.materials.append(material)
    for polygon,group in zip(mesh.polygons,assignments):
        polygon.material_index = group
        polygon.use_smooth = True
    obj = bpy.data.objects.new('Diagnostic limbs',mesh)
    scene.collection.objects.link(obj)
    for view,position,target,scale in [('top',(0,0,6),(0,0,0),2.7),('front',(0,-6,.5),(0,0,.5),1.65)]:
        camera.location = position
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = scale
        camera.data.shift_x = camera.data.shift_y = 0
        scene.render.filepath = str(out/f'{view}-{index:02}.png')
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.meshes.remove(mesh)
report = {'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
          'engine':'CYCLES','device':scene.cycles.device,'resolution':scene.render.resolution_x,
          'samples':scene.cycles.samples,'travel_direction_world':[0,-1,0],
          'note':'Actual lower-limb meshes; fixed 25cm grid. In-place source walk, so stance moves backward relative to body. Contact alone does not prove no sliding.',
          'frames':[{'frame':f,'hooves':m} for f,_,_,_,m in samples]}
(out/'report.json').write_text(json.dumps(report,indent=2))
print('FEET_RENDER_OK: 16 diagnostic views from actual mesh samples')

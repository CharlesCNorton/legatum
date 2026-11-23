"""Actual front/top move samples: mechanical equivalent of the feet review."""
import bpy, os, json, subprocess, hashlib
from pathlib import Path
from mathutils import Vector

root=Path(os.environ['ANIM_ROOT']);master=root/'masters/artillery'
bpy.ops.wm.open_mainfile(filepath=str(master/'artillery-move.blend'))
scene=bpy.context.scene;camera=scene.camera
resolution=int(os.environ.get('RESOLUTION','256'))
scene.render.resolution_x=scene.render.resolution_y=resolution
scene.cycles.samples=min(int(os.environ.get('SAMPLES','12')),32)
scene.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
if scene.cycles.device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    assert any(d.type=='METAL' for d in prefs.devices)
    for d in prefs.devices:d.use=d.type=='METAL'
clay=bpy.data.materials.new('MAT-running-gear-review');clay.diffuse_color=(.26,.29,.30,1)
clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.26,.29,.30,1)
clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7
wheels=[bpy.data.objects['RIG-wheel '+str(sign)] for sign in [-1,1]]
visible={o.name for w in wheels for o in w.children_recursive}
visible.update(o.name for o in scene.objects if any(s in o.name for s in ['Axle','trail','Trail','spade','Spade']))
for o in scene.objects:
    if o.type!='MESH':continue
    if o.name=='GEO-stationary cream disc':continue
    o.animation_data_clear();o.hide_render=o.name not in visible
    if not o.hide_render:
        for i in range(len(o.data.materials)):o.data.materials[i]=clay
frames=[];report=[]
for label,position in [('front',(5,0,1.1)),('top',(0,0,6))]:
    camera.location=position
    camera.rotation_euler=(Vector((0,0,.4))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=2.85
    for i in range(8):
        scene.frame_set(i+1)
        path=master/'contact-views'/f'{label}-{i:02}.png';path.parent.mkdir(exist_ok=True)
        scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append(str(path))
        if label=='front':
            axes=[list(w.matrix_world.to_quaternion()@Vector((0,1,0))) for w in wheels]
            assert (Vector(axes[0])-Vector(axes[1])).length<1e-5
            lights=[bpy.data.objects['RIG-fixed light '+w.name] for w in wheels]
            carriage=bpy.data.objects['RIG-carriage']
            for w,light in zip(wheels,lights):
                assert (light.matrix_world.translation-w.matrix_world.translation).length<1e-5
                assert abs(light.matrix_world.to_quaternion().dot(carriage.matrix_world.to_quaternion()))>1-1e-5
            report.append({'sample':i,'parallel_axles':True,'rolling_axes':axes,'light_frames_follow_without_rolling':True})
(master/'contact-review.json').write_text(json.dumps({'device':scene.cycles.device,'resolution':resolution,'samples':report,'clip_sha256':hashlib.sha256((master/'artillery-move.blend').read_bytes()).hexdigest(),'renders':{str(Path(p).relative_to(master)):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in frames},'scope':'in-place mechanical rolling, parallel wheel axes; no world-travel or human gait claim'},indent=2))
subprocess.run([str(root/'venv/bin/python'),str(Path(__file__).with_name('review.py')),'g-feet-check'],check=True)

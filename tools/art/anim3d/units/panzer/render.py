"""Serial actual geometry renders. GPU requests fail rather than silently using CPU."""
import bpy,os,sys,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/panzer'
stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('panzer-plain.blend' if stage=='b' else 'panzer.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
assert sc.camera is not None
sc.render.engine='CYCLES';device=os.environ.get('CYCLES_DEVICE','CPU')
if device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    assert any(d.type=='METAL' for d in prefs.devices),'Metal unavailable'
    for d in prefs.devices:d.use=d.type=='METAL'
sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
(out/'render.json').unlink(missing_ok=True)
for p in out.glob('*.png'):p.unlink()
def render(name):
    sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
if clip:
    frames=json.loads(sc['sample_frames'])
    if stage=='d':frames=[frames[i] for i in [0,2,4,9]]
    if stage=='g':
        clay=bpy.data.materials.new('Running gear inspection clay');clay.use_nodes=True
        clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.35,.28,.18,1)
        sc.view_layers[0].material_override=clay
        for view,pos in [('top',(0,0,10)),('front',(10,0,1.5))]:
            sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,.75))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
            sc.camera.data.ortho_scale=4.8
            for i,f in enumerate(frames):sc.frame_set(f);render(f'{view}-{i:02}')
    else:
        for i,f in enumerate(frames):
            if i>0 and f==frames[i-1]:shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
            sc.frame_set(f);render(f'{i:02}')
else:
    if stage=='b':
        for name,pos in [('three-quarter',(5.7,-10,4.7)),('front',(10,0,4)),('side',(0,-10,4))]:
            sc.camera.location=pos;sc.camera.rotation_euler=(Vector((.05,0,1.02))-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(name)
    else:render('three-quarter')
(out/'render.json').write_text(json.dumps({'engine':'CYCLES','device':device,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string},indent=2))
print('RENDER_READY',stage)

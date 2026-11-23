"""Render single previews or baked keyframes, with explicit CPU/GPU engine selection."""
import bpy,os,sys,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(os.environ['ANIM_ROOT']); M=ROOT/'masters/main-battle-tank'
stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('main-battle-tank-plain.blend' if stage=='b' else 'main-battle-tank.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
if sc.camera is None or sc.camera.type!='CAMERA':raise RuntimeError('Tank master has no assigned camera')
for o in bpy.data.objects:
    if 'effect' in o and max(o.scale)<.001:o.hide_render=True;o.scale=(1,)*3
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.render.threads_mode='FIXED';sc.render.threads=3
if sc.render.engine=='CYCLES':
    device=os.environ.get('CYCLES_DEVICE','CPU')
    if device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        metal=[d for d in prefs.devices if d.type=='METAL']
        if not metal:raise RuntimeError('Metal Cycles requested but no Metal device is available')
        for d in prefs.devices:d.use=d.type=='METAL'
    sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
(out/'render.json').unlink(missing_ok=True)
if stage=='b':bpy.data.objects['Vehicle suspension root'].location.z=-.11
if clip:
    assert sc['source_sha256']==hashlib.sha256((M/'main-battle-tank.blend').read_bytes()).hexdigest(), 'Clip uses stale source master'
    frames=json.loads(sc['sample_frames'])
    if stage=='d':frames=[frames[i] for i in [0,3,4,9]]
    views=[('top',(0,0,10)),('front',(10,0,1.0))] if stage=='g' else [('hero',None)]
    for view,position in views:
        if position:
            sc.camera.location=position;sc.camera.rotation_euler=(Vector((0,0,.7))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        for i,frame in enumerate(frames):
            dest=out/(f'{view}-{i:02}.png' if stage=='g' else f'{i:02}.png')
            if i>0 and frame==frames[i-1]:shutil.copyfile(out/f'{i-1:02}.png',dest);continue
            sc.frame_set(frame);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)

else:
    views=[('three-quarter',(6,-14,3.3)),('front',(9,0,4.4)),('side',(0,-10,4.6))] if stage=='b' else [('three-quarter',(6,-14,3.3))]
    for name,pos in views:
        sc.camera.location=pos;target=Vector((.20,0,.86))
        if stage=='details':
            basis=sc.camera.rotation_euler.to_matrix();shift=basis @ Vector((-15,18,0))*5.35/256
            target+=shift;sc.camera.location+=shift;sc.camera.data.ortho_scale=2.7
        sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'host Metal','resolution':sc.render.resolution_x,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_master_sha256':hashlib.sha256((M/'main-battle-tank.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string},indent=2))
print('RENDER_READY',out)

"""Render true 3D masters, with explicit CPU/GPU provenance and stale-output guards."""
import bpy, os, sys, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/legionary'
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('legionary-plain.blend' if stage=='b' else 'legionary.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
assert sc.camera,'Missing camera'
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
if sc.render.engine=='CYCLES':
    sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
    if device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        available=[d for d in prefs.devices if d.type=='METAL'];assert available,'Metal unavailable; no CPU fallback'
        for d in prefs.devices:d.use=d.type=='METAL'
res=int(os.environ.get('RESOLUTION','256' if stage=='b' else '512'))
sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100
sc.render.use_persistent_data=True
out=M/'renders'/stage/'raw';out.mkdir(parents=True,exist_ok=True);manifest=out.parent/'render.json';manifest.unlink(missing_ok=True)
if clip:
    frames=json.loads(sc['sample_frames']);frames=[frames[i] for i in [0,2,4,9]] if stage=='d' else frames
    for i,f in enumerate(frames):
        sc.frame_set(f);sc.render.filepath=str(out/f'{i:02}.png')
        if i and f==frames[i-1]:shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png')
        else:bpy.ops.render.render(write_still=True)
else:
    views=[('rest',None),('front',(0,-8,3.55)),('side',(8,0,3.55))] if stage=='b' else [('rest',None)]
    for name,pos in views:
        if pos:sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,.915))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
manifest.write_text(json.dumps({'stage':stage,'engine':sc.render.engine,'device':device,'samples':sc.cycles.samples,'resolution':res,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_master_sha256':sc.get('source_master_sha256'),'blender':bpy.app.version_string,'frames':frames if clip else list(p.stem for p in out.glob('*.png'))},indent=2))
print('RENDER_READY',stage)

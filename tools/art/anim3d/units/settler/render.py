"""Resumable PNG masters; GPU fail-fast; terminal death held byte-for-byte."""
import bpy,os,json,hashlib,subprocess,shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render(stage):
    clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'death' if stage=='death-check' else None
    path=M/'clips'/f'{clip}.blend' if clip else M/('settler-plain.blend' if stage=='b' else 'settler.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    assert sc.camera is not None,'Saved camera required'
    sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
    if sc.render.engine=='CYCLES':
        sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
        if device=='GPU':
            prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
            for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
            if not found:raise RuntimeError('No Metal Cycles device; refusing silent CPU fallback')
    size=int(os.environ.get('RESOLUTION','256' if stage=='b' else '512'))
    sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
    sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.use_persistent_data=True
    out=M/'renders'/stage/'raw';out.mkdir(parents=True,exist_ok=True);manifest=out.parent/'render.json';manifest.unlink(missing_ok=True)
    if clip:
        frames=json.loads(sc['sample_frames']);frames=[frames[i] for i in [0,2,5,9]] if stage=='d' else frames
        if stage=='death-check':frames=[frames[-1]]
        items=[(f'{i:02}',f) for i,f in enumerate(frames)]
    else:items=[('rest',1),('side',1),('back',1)] if stage=='b' else [('rest',1)]
    for i,(name,f) in enumerate(items):
        sc.frame_set(f);dest=out/(name+'.png')
        if stage=='b':
            if name!='rest':
                sc.camera.location={'side':(7,0,3.0),'back':(0,7,3.0)}[name]
                sc.camera.rotation_euler=(Vector((0,0,.88))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        if clip=='death' and stage.startswith('e-') and i==len(items)-1:
            shutil.copyfile(out/(items[-2][0]+'.png'),dest);continue
        sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
    data={'stage':stage,'engine':sc.render.engine,'device':device,'samples':sc.cycles.samples,'resolution':size,'blend_sha256':sha(path),'master_sha256':sha(M/'settler.blend') if stage!='b' else sha(path),'blender':bpy.app.version_string,'frames':{n:sha(out/(n+'.png')) for n,f in items}}
    manifest.write_text(json.dumps(data,indent=2))
    subprocess.run([str(R/'venv/bin/python'),str(HERE/'review.py'),stage],check=True)

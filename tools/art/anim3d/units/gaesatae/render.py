"""Sequential renders, explicit device selection, resumable hash-bound PNG masters."""
import bpy, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(os.environ['ANIM_ROOT']);M=ROOT/'masters/gaesatae'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
size=int(os.environ.get('RESOLUTION','256'));device=os.environ.get('CYCLES_DEVICE','CPU');samples=int(os.environ.get('SAMPLES','8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render_stage(stage):
    clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
    path=M/'clips'/f'{clip}.blend' if clip else M/('finished-plain.blend' if stage=='b' else 'gaesatae.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    sc.render.engine='CYCLES';sc.cycles.device=device;sc.cycles.samples=samples;sc.cycles.use_denoising=True
    if device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type=os.environ.get('CYCLES_BACKEND','METAL');prefs.get_devices()
        found=False
        for d in prefs.devices:
            d.use=d.type!='CPU';found=found or d.use
        assert found,'Requested GPU unavailable; refusing CPU fallback'
    sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
    assert sc.camera,'Missing painting camera'
    if clip:
        assert sc['source_sha256']==sha(M/'gaesatae.blend'),'Stale clip master'
        frames=json.loads(sc['sample_frames']);frames=[frames[i] for i in (0,2,5,9)] if stage=='d' else frames
    else:frames=[1]
    out=M/'renders'/str(size)/stage;out.mkdir(parents=True,exist_ok=True)
    manifest=out/'render.json';manifest.unlink(missing_ok=True)
    hashes=[]
    for i,f in enumerate(frames):
        dest=out/f'{i:02}.png'
        if stage=='e-death' and i==9:shutil.copyfile(out/'08.png',dest)
        else:
            sc.frame_set(f);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
        hashes.append(sha(dest))
    manifest.write_text(json.dumps({'stage':stage,'engine':'CYCLES','device':device,'samples':samples,'resolution':size,'blend_sha256':sha(path),'source_sha256':sha(M/'gaesatae.blend') if (M/'gaesatae.blend').exists() else None,'frames':hashes},indent=2)+'\n')
    print('RENDER_READY',stage,device,size,flush=True)
for s in (['b','c','d']+['e-'+c for c in CLIPS] if stage=='all' else [stage]):
    render_stage(s)
    subprocess.run([str(ROOT/'venv/bin/python'),str(Path(__file__).with_name('deliver.py')),'--stage',s],check=True)

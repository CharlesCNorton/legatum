"""Serial CPU previews or explicit Metal Cycles GPU pass, immediate review publish."""
import bpy,os,sys,json,hashlib,subprocess,shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout';HERE=Path(__file__).resolve().parent
arg=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
stages=['b','c','d','e-idle','e-move','e-attack','e-hit','e-death'] if arg=='all' else [arg]
for stage in stages:
    clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
    path=M/'clips'/clip/(clip+'.blend') if clip else M/('plain.blend' if stage=='b' else 'barbarian-scout.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
    if sc.cycles.device=='GPU':
        pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
        devices=[d for d in pref.devices if d.type=='METAL'];assert devices,'No Metal GPU; refusing silent CPU fallback'
        for d in pref.devices:d.use=d in devices
    res=int(os.environ.get('RESOLUTION','512'));sc.render.resolution_x=sc.render.resolution_y=res
    sc.cycles.use_denoising=True;sc.cycles.seed=21;sc.cycles.use_animated_seed=False
    out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
    frames=[1,1,1] if stage=='b' else [1,3,5,9] if stage=='d' else list(range(1,sc['clip_count']+1)) if clip else [1]
    for i,frame in enumerate(frames):
        sc.frame_set(frame)
        if stage=='b':
            sc.camera.location=[(0,-6,2.46),(3.5,-5,2.46),(6,0,2.46)][i]
            sc.camera.rotation_euler=(Vector((0,0,.67))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        if clip=='death' and i==len(frames)-1:
            rig=bpy.data.objects['Scout • MPFB rig']
            current=[tuple(v for row in p.matrix for v in row) for p in rig.pose.bones]
            sc.frame_set(frames[-2]);previous=[tuple(v for row in p.matrix for v in row) for p in rig.pose.bones]
            assert max(abs(a-b) for aa,bb in zip(current,previous) for a,b in zip(aa,bb))<1e-6,'Death pose is not held'
            shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
        sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
    (out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':res,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':sc.get('source_sha256',hashlib.sha256((M/'barbarian-scout.blend').read_bytes()).hexdigest()),'frames':frames},indent=2))
    subprocess.run([str(R/'venv/bin/python'),str(HERE/'post.py'),stage],check=True)
    print('RENDER_READY',out,flush=True)

"""Serial still/sequence renders. CPU previews and explicit Metal GPU finals."""
import bpy,os,sys,json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/phalangite';D=Path(__file__).parent
stage=sys.argv[sys.argv.index('--')+1];resolution=int(os.environ.get('RESOLUTION','256'))
stages=['b','c','d','e-idle','e-move','e-attack','e-hit','e-death'] if stage=='all' else [stage]
for stage in stages:
    clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
    plain=M/'fitted-plain.blend'
    if not plain.exists() or plain.stat().st_mtime<(M/'plain.blend').stat().st_mtime:plain=M/'plain.blend'
    path=M/'clips'/f'{clip}.blend' if clip else plain if stage=='b' else M/'phalangite.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    assert sc.camera is not None
    if clip:assert sc["source_sha256"]==hashlib.sha256((M/"phalangite.blend").read_bytes()).hexdigest(),"Rebuild stale clips"
    sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
    if sc.render.engine=='CYCLES':
        sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
        if sc.cycles.device=='GPU':
            prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
            available=[d for d in prefs.devices if d.type=='METAL'];assert available,'Metal GPU required; no silent CPU fallback'
            for device in prefs.devices:device.use=device.type=='METAL'
    sc.render.resolution_x=sc.render.resolution_y=resolution
    out=M/'renders'/str(resolution)/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
    frames=list(range(1,json.loads(sc['clip'])['frames']+1)) if clip else [0]
    if stage=='d':frames=[1,3,5,8]
    if stage=='e-death':frames[-1]=frames[-2]
    if stage=='b':frames=[0,0,0]
    for i,frame in enumerate(frames):
        if stage=='e-death' and i==len(frames)-1:
            shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
        if stage=='b' and i:
            from mathutils import Vector
            look=Vector((.42,0,1.08));sc.camera.location=look+Vector((0,-7,2) if i==1 else (7,0,2));sc.camera.rotation_euler=(look-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.frame_set(frame);sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
    report={'stage':stage,'resolution':resolution,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'master_sha256':hashlib.sha256((M/'phalangite.blend').read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(frames),'sample_frames':frames}
    (out/'render.json').write_text(json.dumps(report,indent=2))
    subprocess.run([str(R/'venv/bin/python'),str(D/'deliver.py'),'review',stage,str(resolution)],check=True)
    if stage!='b':
        report['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(out/'render.json').write_text(json.dumps(report,indent=2))
print('PHALANGITE_RENDER_COMPLETE')

"""Sequential, resumable Cycles reviews. GPU is explicitly required when requested."""
import sys,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
path=MASTER/('refined-plain.blend' if stage=='b' else 'master.blend')
if stage.startswith('e-'):path=MASTER/(stage[2:]+'.blend')
if stage=='d':path=MASTER/'attack.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));sc=settings(res,samples)
out=MASTER/'renders'/str(res)/stage;out.mkdir(parents=True,exist_ok=True)
manifest=out/'manifest.json';manifest.unlink(missing_ok=True)
if stage.startswith('e-'):
    frames=range(1,CLIPS[stage[2:]][0]+1)
elif stage=='d':frames=[1,4,6,10]
else:frames=[1]
for i,f in enumerate(frames):
    sc.frame_set(f)
    if stage=='e-death' and i==9:
        # Both terminal samples have the same rig and prop transforms. Avoid
        # denoiser rounding causing a false motion signal on the held pose.
        def transforms():
            bpy.context.view_layer.update()
            return [[list(row) for row in o.matrix_world] for o in sc.objects]+[[list(row) for row in p.matrix] for o in sc.objects if o.type=='ARMATURE' for p in o.pose.bones]
        final=transforms();sc.frame_set(9);previous=transforms();sc.frame_set(10)
        assert all(abs(a-b)<1e-6 for ma,mb in zip(final,previous) for ra,rb in zip(ma,mb) for a,b in zip(ra,rb)), 'Death is not settled'
        shutil.copyfile(out/'08.png',out/'09.png')
    else:render(out/f'{i:02d}.png')
if stage=='b':
    for i,loc in enumerate([(4,-6,2.9),(6,0,2.6)],1):
        sc.camera.location=loc;sc.camera.rotation_euler=(Vector((.06,0,.91))-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(out/f'{i:02d}.png')
manifest.write_text(json.dumps({'stage':stage,'resolution':res,'samples':samples,'engine':sc.render.engine,'device':sc.cycles.device,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(list(out.glob('*.png')))},indent=2))
log(f'Rendered {stage}: {res}px, Cycles {sc.cycles.device}, {samples} samples; raw frames preserved.')

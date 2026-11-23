"""Serial CPU/GPU rendering. Never spawns Blender; every output records its source."""
import bpy,os,json,hashlib,shutil
from mathutils import Vector
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-crossbowman';stage=os.environ.get('STAGE','b');size=int(os.environ.get('RESOLUTION','256'))
clips={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
source=M/('plain.blend' if stage=='b' else 'clips/'+stage[2:]+'.blend' if stage.startswith('e-') else 'model.blend')
if stage=='d':source=M/'clips/attack.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
if sc.cycles.device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
    for device in prefs.devices:device.use=device.type=='METAL';found|=device.use
    if not found:raise RuntimeError('Metal GPU required; refusing silent CPU fallback')
sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
out=M/'renders'/str(size)/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
frames=list(range(1,clips[stage[2:]]+1)) if stage.startswith('e-') else [1,3,5,8] if stage=='d' else [0,0,0] if stage=='b' else [0]
for i,f in enumerate(frames):
    if stage=='b':
        sc.camera.location=[(0,-7,3.15),(3,-7,3.15),(7,0,2.6)][i]
        sc.camera.rotation_euler=(Vector((0,0,.90))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
    sc.frame_set(f)
    if stage=='e-death' and i>=8:
        state=[tuple(v for row in o.matrix_world for v in row) for o in sc.objects]+[tuple(v for row in p.matrix for v in row) for o in sc.objects if o.type=='ARMATURE' for p in o.pose.bones]
        assert state==held_state,'Terminal death is not held'
        shutil.copy2(out/'07.png',out/f'{i:02d}.png');continue
    if stage=='e-death' and i==7:held_state=[tuple(v for row in o.matrix_world for v in row) for o in sc.objects]+[tuple(v for row in p.matrix for v in row) for o in sc.objects if o.type=='ARMATURE' for p in o.pose.bones]
    sc.render.filepath=str(out/f'{i:02d}.png');assert sc.camera;bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'stage':stage,'resolution':size,'frames':len(frames),'engine':'CYCLES','device':sc.cycles.device,'samples':sc.cycles.samples,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2))

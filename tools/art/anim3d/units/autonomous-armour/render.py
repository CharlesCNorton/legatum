"""Render resumable stage evidence; commit a manifest only after all frames succeed."""
import os, sys, json, hashlib, shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from common import MASTER, CLIPS, SLUG, log
stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
path=MASTER/'clips'/f'{clip}.blend' if clip else MASTER/('plain.blend' if stage=='b' else 'finished.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
assert sc.camera and sc.camera.type=='CAMERA'
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
sc.render.threads_mode='FIXED';sc.render.threads=3
if sc.render.engine=='CYCLES':
    device=os.environ.get('CYCLES_DEVICE','CPU')
    if device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        assert any(d.type=='METAL' for d in prefs.devices),'No Metal device; refusing CPU fallback'
        for d in prefs.devices:d.use=d.type=='METAL'
    sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
folder=MASTER/'renders'/stage;folder.mkdir(parents=True,exist_ok=True)
(folder/'render.json').unlink(missing_ok=True)
outputs=[]
def render(name):
    p=folder/f'{name}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);outputs.append(p)
if stage=='g':
    sc.camera.data.ortho_scale=5.5
    for view,pos,target in [('top',(0,0,12),(0,0,0)),('front',(12,0,3),(0,0,.6))]:
        sc.camera.location=pos;sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        for i,frame in enumerate(json.loads(sc['sample_frames'])):
            sc.frame_set(frame);render(f'{view}-{i:02}')
elif clip:
    frames=json.loads(sc['sample_frames'])
    if stage=='d':frames=[frames[i] for i in [0,2,3,7]]
    for i,frame in enumerate(frames):
        if i and frame==frames[i-1]:
            p=folder/f'{i:02}.png';shutil.copyfile(outputs[-1],p);outputs.append(p)
        else:sc.frame_set(frame);render(f'{i:02}')
else:
    render('rest')
    if stage=='b':
        for name,pos in [('side',(0,-12,5)),('front',(12,0,5))]:
            sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.44))-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(name)
    if stage=='details':
        sc.camera.data.ortho_scale=3;sc.camera.rotation_euler=(Vector((.1,0,1.75))-sc.camera.location).to_track_quat('-Z','Y').to_euler();render('close')
report={'stage':stage,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'master_sha256':hashlib.sha256((MASTER/'finished.blend').read_bytes()).hexdigest() if stage!='b' else None,'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},'blender':bpy.app.version_string}
(folder/'render.json').write_text(json.dumps(report,indent=2));log(f'Rendered {stage}: {len(outputs)} PNGs, {report["resolution"]} px, {report["engine"]} {report["device"]}, {report["samples"]} samples.')

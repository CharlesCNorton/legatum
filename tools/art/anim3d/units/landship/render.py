"""Sequential render entry point. CPU previews and explicitly selected GPU finals."""
import bpy,os,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/landship'
args=sys.argv[sys.argv.index('--')+1:];stage=args[0]
clip=stage[2:] if stage.startswith('e-') else None
path=M/'clips'/f'{clip}.blend' if clip else M/('plain.blend' if stage=='b' else 'landship.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
res=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=res
sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
if os.environ.get('CYCLES_DEVICE','CPU')=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();gpus=[d for d in prefs.devices if d.type=='METAL'];assert gpus,'No Metal device; refusing CPU fallback'
    for d in prefs.devices:d.use=d in gpus
    sc.cycles.device='GPU'
else:sc.cycles.device='CPU'
folder=M/'renders'/stage;folder.mkdir(parents=True,exist_ok=True)
receipt=folder/'render.json';receipt.unlink(missing_ok=True)
sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True
cam=sc.camera;loc=cam.location.copy();rot=cam.rotation_euler.copy()
def render(name,frame=1):
    assert sc.camera is not None
    sc.frame_set(frame);sc.render.filepath=str(folder/f'{name}.png');bpy.ops.render.render(write_still=True)
if clip:
    count={'idle':8,'move':8,'attack':10,'hit':4,'death':10}[clip]
    for i in range(count):
        if clip=='death' and i==9:
            import shutil;shutil.copyfile(folder/'08.png',folder/'09.png')
        else:render(f'{i:02}',i+1)
elif stage=='b':
    render('hero')
    for name,p in [('front',(7,0,3)),('side',(0,-8,3))]:
        cam.location=p;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();render(name)
elif stage=='d':
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips/attack.blend'));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=res;s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('SAMPLES','8'));s.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc=s
    for f in [1,3,4,7]:render(f'{f:02}',f)
elif stage=='g':
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move.blend'));sc=bpy.context.scene;sc.render.resolution_x=sc.render.resolution_y=res;sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');cam=sc.camera
    # Mechanical contact review uses physical materials, so texture cannot conceal motion.
    for o in sc.objects:
        if o.type=='MESH' and o.data.materials and '_projected' in o.data.materials[0].name:
            mat=o.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;l.new(n.get('Principled BSDF').outputs[0],n.get('Material Output').inputs['Surface'])
    for view,p in [('top',(0,0,9)),('front',(8,0,1.3))]:
        cam.location=p;cam.rotation_euler=(Vector((0,0,1.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=6
        for f in range(1,9):render(f'{view}-{f:02}',f)
else:render('hero')
path=M/'clips/attack.blend' if stage=='d' else M/'clips/move.blend' if stage=='g' else path
receipt.write_text(json.dumps({'stage':stage,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resolution':res,'engine':'CYCLES','device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':sc.cycles.samples},indent=2))

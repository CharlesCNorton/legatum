"""Serial, resumable renders; manifests reject stale/incomplete sequences."""
import bpy,os,sys,json,hashlib
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/fighter'
stage=sys.argv[sys.argv.index('--')+1];size=int(os.environ.get('RESOLUTION','256'))
folder=M/'renders'/str(size)/stage;folder.mkdir(parents=True,exist_ok=True)
manifest=folder/'render.json';manifest.unlink(missing_ok=True)
clip=stage[2:] if stage.startswith('e-') else None
blend=M/(clip+'.blend' if clip else ('plain.blend' if stage=='b' else 'fighter.blend'))
bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene
if sc.camera is None:raise RuntimeError('No render camera')
engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.render.engine=engine
if engine=='CYCLES':
    sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
    if sc.cycles.device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
        gpu=[d for d in prefs.devices if d.type=='METAL']
        if not gpu:raise RuntimeError('Metal device unavailable; no CPU fallback')
        for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.film_transparent=True
if stage=='b':
    clay=bpy.data.materials.new('Plain clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.46,.45,.41,1)
    for o in bpy.data.objects:
        if o.type=='MESH' and not o.name.startswith(('BASE','DISPLAY','FX-')):o.data.materials.clear();o.data.materials.append(clay)
if clip:
    meta=json.loads((M/'clips.json').read_text());assert meta['source_sha256']==hashlib.sha256((M/'fighter.blend').read_bytes()).hexdigest(),'Stale clips'
    frames=list(range(1,meta['clips'][clip]['frames']+1))
else:frames=[1]
for i,f in enumerate(frames):
    sc.frame_set(f);sc.render.filepath=str(folder/f'{i:03d}.png');bpy.ops.render.render(write_still=True)
manifest.write_text(json.dumps({'stage':stage,'resolution':size,'engine':engine,'device':getattr(sc.cycles,'device','GPU'),'samples':sc.cycles.samples,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((M/'fighter.blend').read_bytes()).hexdigest(),'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('*.png'))}},indent=2))
print('RENDER COMPLETE',stage,size)

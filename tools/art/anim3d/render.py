"""Render masters with CPU previews or host Eevee. No silent engine fallback."""
import bpy,os,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/spearman-3d-v2'
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'b'
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=master/'clips'/clip/(clip+'.blend') if clip else master/'spearman.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':sc.cycles.device='CPU';sc.cycles.samples=int(os.environ.get('SAMPLES','16'))
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
sc.render.threads_mode='FIXED';sc.render.threads=4
out=master/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
if clip:
 assert sc.get('cloth_baked'), 'Per-clip cloth must be baked before rendering'
 frames=json.loads(sc['sample_frames'])
 if stage=='d': frames=[frames[i] for i in [0,2,4,9]]
 for i,frame in enumerate(frames):
  sc.frame_set(frame);sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
else:
 views=[('front',(0,-7,3.0)),('three-quarter',(2.5,-7,3.0)),('side',(7,-.3,3.0))] if stage=='b' else [('three-quarter',(2.5,-7,3.0))]
 for name,pos in views:
  sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.25))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string},indent=2))
print('RENDER_READY',out)

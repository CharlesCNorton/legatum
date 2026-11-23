import bpy,os,json,hashlib,shutil
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane';stage=os.environ['STAGE'];size=int(os.environ.get('RESOLUTION','256'))
path=M/(f'{stage[2:]}.blend' if stage.startswith('e-') else ('attack.blend' if stage=='d' else 'biplane.blend'))
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
assert sc.camera is not None
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'))
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
 for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
 if not found:raise RuntimeError('Metal GPU unavailable; no silent CPU fallback')
sc.render.resolution_x=sc.render.resolution_y=size
out=M/'raw'/stage;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
if stage=='b':
 clay=bpy.data.materials.new('Plain geometry review');clay.diffuse_color=(.55,.55,.55,1);sc.view_layers[0].material_override=clay
if stage.startswith('e-'):frames=list(range(1,sc.frame_end+1))
elif stage=='d':frames=[1,4,6,10]
else:frames=[1]
for i,f in enumerate(frames):
 if stage=='e-death' and i==len(frames)-1:
  def pose(frame):
   sc.frame_set(frame);bpy.context.view_layer.update()
   return [(o.name,tuple(round(v,6) for row in o.matrix_world for v in row),o.hide_render) for o in sc.objects]
  assert pose(f-1)==pose(f),'Terminal death transforms are not held'
  shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png')
  continue
 sc.frame_set(f);sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
manifest.write_text(json.dumps({'stage':stage,'resolution':size,'samples':sc.cycles.samples,'device':sc.cycles.device,'engine':sc.render.engine,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(frames),'terminal_hold_verified':stage=='e-death'},indent=2))

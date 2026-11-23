"""Serial Blender stages; no nested Blender processes. All masters external."""
import bpy,os,sys,runpy,json,hashlib,subprocess
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/scout';HERE=Path(__file__).resolve().parent
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'round'
def log(message):
 with (R/'review/3d-v2/scout-log.md').open('a') as f:f.write(message+'\n')
 print(message,flush=True)
def run(name):runpy.run_path(str(HERE/(name+'.py')),run_name='__main__')
def review(stage):subprocess.run([str(R/'venv/bin/python'),str(HERE/'review.py'),stage],check=True)
def render(stage):
 clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
 path=M/'clips'/(clip+'.blend') if clip else M/('scout-unpainted.blend' if stage=='b' else 'scout.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;assert sc.camera
 sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.render.threads_mode='FIXED';sc.render.threads=3
 if sc.render.engine=='CYCLES' and sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  found=False
  for dev in prefs.devices:dev.use=dev.type=='METAL';found|=dev.use
  assert found,'No Metal Cycles device; explicit CPU setting required in sandbox'
 size=int(os.environ.get('RESOLUTION','512' if stage!='b' else '256'));sc.render.resolution_x=sc.render.resolution_y=size
 out=M/'renders'/stage/'raw';out.mkdir(parents=True,exist_ok=True);manifest=out.parent/'render.json';manifest.unlink(missing_ok=True)
 samples=json.loads(sc['samples']) if clip else [1,1,1] if stage=='b' else [1]
 if stage=='d':samples=[samples[i] for i in [0,2,5,9]]
 for i,frame in enumerate(samples):
  sc.frame_set(frame);sc.render.filepath=str(out/f'{i:02}.png')
  if stage=='b' and i>0:
   from mathutils import Vector
   sc.camera.data.ortho_scale=2.5;sc.camera.location=(0,-7,2.7) if i==1 else (7,-.3,2.7);sc.camera.rotation_euler=(Vector((0,0,1))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  if clip=='death' and i==9:
   import shutil;shutil.copyfile(out/'08.png',out/'09.png')
  else:bpy.ops.render.render(write_still=True)
 manifest.write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':size,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(samples)},indent=2))
 review(stage);log('Rendered '+stage+' '+str(size)+' px '+sc.render.engine+'/'+sc.cycles.device)
if stage in ['build','round','preview']:
 log('Using six Blender skills: MPFB anatomy, solid folded clothing/bevels, textured Principled materials, warm key/cool rim, painting camera, authored keys/secondary cloth, denoised RGBA sequences.');run('build');run('register');render('b')
if stage in ['paint','round']:run('paint');render('c');render('c-details')
if stage in ['animate','round']:run('animate')
if stage in ['round','final']:
 if stage=='final':render('c');render('c-details')
 render('d')
 for clip in ['idle','move','attack','hit','death']:render('e-'+clip)
 run('audit')
elif stage in ['b','c','c-details','d'] or stage.startswith('e-'):render(stage)

if stage=='audit':run('audit')
if stage=='refresh':
 clip=os.environ.get('CLIP');assert clip in ['idle','move','attack','hit','death'],'Set CLIP for a targeted refresh'
 run('animate')
 if clip=='attack':render('d')
 render('e-'+clip);run('audit')

if stage=='register':run('register');render('b')

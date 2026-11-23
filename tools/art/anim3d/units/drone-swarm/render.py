"""Render stages and save independent keyed mechanical clip masters."""
import bpy,sys,os,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/drone-swarm';stage=sys.argv[sys.argv.index('--')+1]
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
UP=Vector((0,.28,math.sqrt(1-.28**2)));VIEW=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))
def setup(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;assert sc.camera is not None
 engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.render.engine=engine
 if engine=='CYCLES':
  sc.cycles.samples=samples;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.cycles.use_animated_seed=False;sc.cycles.seed=17
  device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.device=device
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
   for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
   if not found:raise RuntimeError('Metal GPU unavailable; no silent fallback')
 sc['source_master_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
 return sc

def render(sc,path):
 path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def curves(action):
 if hasattr(action,'fcurves'):return action.fcurves
 return [f for l in action.layers for s in l.strips for b in s.channelbags for f in b.fcurves]

def animate(sc,clip):
 n,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n
 roots=[bpy.data.objects['RIG-drone'+str(i)] for i in (1,2,3)];rests=[o.location.copy() for o in roots];rotors=[o for o in bpy.data.objects if o.name.startswith('RIG-') and ' rotor' in o.name];gimbals=[bpy.data.objects['RIG-drone'+str(i)+' gimbal'] for i in (1,2,3)]
 base=bpy.data.objects['GEO-stationary cream base'];basepos=base.location.copy();top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box)
 targets=[basepos+Vector((-.7,.5,0)),basepos+Vector((.6,.1,0)),basepos+Vector((-.05,-.65,0))]
 # Different settling orientations keep the three mechanical wrecks distinguishable.
 terminal=[(.52,.48,-.3),(-.4,-.42,.5),(.35,.30,-.22)];restrot=[o.rotation_euler.copy() for o in rotors]
 for j in range(n+1 if loop else n):
  t=j/n if loop else min(j,8)/8 if clip=='death' else j/(n-1);phase=math.tau*t;sc.frame_set(j+1)
  for k,(root,rest,gm) in enumerate(zip(roots,rests,gimbals)):
   root.location=rest.copy();root.rotation_euler=(0,0,0);gm.rotation_euler=(0,0,0)
   if clip=='idle':
    wave=math.sin(phase+k*1.5)-math.sin(k*1.5);root.location+=UP*(.018*wave);root.rotation_euler.x=.025*wave;root.rotation_euler.y=.018*math.sin(phase);gm.rotation_euler.z=.035*(math.sin(phase+k*.5)-math.sin(k*.5))
   if clip=='move':
    wave=math.sin(phase+k*.7)-math.sin(k*.7);root.location+=RIGHT*(.07*math.sin(phase))+UP*(.04*wave);root.rotation_euler.x=.09*wave;root.rotation_euler.y=.055*(math.cos(phase+k*.7)-math.cos(k*.7));root.rotation_euler.z=.025*wave;gm.rotation_euler.x=-.05*math.sin(phase)
   if clip=='attack':
    # Backward anticipation then a staggered forward/downward attack run, returning.
    local=max(0,min(1,(t-k*.035)/(.93)));lunge=math.sin(math.pi*local)**2;anticipation=math.sin(min(1,t/.22)*math.pi)*.08 if t<.22 else 0
    root.location+=RIGHT*(.23*lunge-anticipation)-UP*(.16*lunge)+VIEW*(.18*lunge);root.rotation_euler.x=.16*lunge;root.rotation_euler.y=-.09*lunge;root.rotation_euler.z=.07*math.sin(phase);gm.rotation_euler.x=.24*lunge
   if clip=='hit':
    h=[0,1,-.45,0][j];root.location+=UP*(.01*h*(1-.16*k))-RIGHT*(.045*h);root.rotation_euler.x=.065*h;root.rotation_euler.y=.04*h;gm.rotation_euler.z=.13*h
   if clip=='death':
    q=max(0,min(1,(t-k*.05)/(.78-k*.05)));fall=q*q*(3-2*q);target=targets[k];root.location=rest.lerp(target,fall);root.rotation_euler=tuple(v*fall for v in terminal[k]);gm.rotation_euler.x=.3*fall
    # Calculate real geometry contact at each sample; stop at the cream pedestal.
    bpy.context.view_layer.update();points=[];deps=bpy.context.evaluated_depsgraph_get()
    for ob in root.children_recursive:
     if ob.type!='MESH':continue
     ev=ob.evaluated_get(deps);me=ev.to_mesh();points.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
    if min(points)<top+.015:root.location.z+=top+.015-min(points)
   root.keyframe_insert('location');root.keyframe_insert('rotation_euler');gm.keyframe_insert('rotation_euler')
  for k,o in enumerate(rotors):
   o.rotation_euler=restrot[k].copy()
   # A blade is half-turn symmetric; n+1 boundary matches at the loop seam.
   spin=j*math.pi/4
   if clip=='death':spin=min(j,6)*math.pi/4+min(j,8)*.07
   o.rotation_euler.z+=(-1 if k%2 else 1)*spin;o.keyframe_insert('rotation_euler')
 # Rotor orientation must be final before evaluating the actual touchdown.
  if clip=='death':
   bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
   for root in roots:
    points=[]
    for ob in root.children_recursive:
     if ob.type!='MESH':continue
     ev=ob.evaluated_get(deps);me=ev.to_mesh();points.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
    if min(points)<top+.015:root.location.z+=top+.015-min(points)
    root.keyframe_insert('location')
 for o in roots+rotors+gimbals:
  o.animation_data.action.name=clip+' | '+o.name
  for f in curves(o.animation_data.action):
   for p in f.keyframe_points:p.interpolation='LINEAR'
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))

stages=['b','c','d',*['e-'+c for c in CLIPS]] if stage=='all' else [stage]
for part in stages:
 sc=setup(M/('plain.blend' if part=='b' else 'drone-swarm.blend'));out=M/'raw'/str(res)/part;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if part=='b':
  clay=bpy.data.materials.new('MAT-clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.42,.42,1);sc.view_layers[0].material_override=clay;render(sc,out/'000.png');center=Vector((0,0,2.55));original=sc.camera.location.copy()
  for i,angle in enumerate((.55,1.2),1):
   sc.camera.data.ortho_scale=7;sc.camera.location=center+Matrix.Rotation(angle,4,'Z') @ (original-center);sc.camera.rotation_euler=(center-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(sc,out/f'{i:03}.png')
 elif part=='c':render(sc,out/'000.png')
 elif part=='g':
  # Flying machines have landing struts, not a walk gait. Show the complete
  # move cycle from front and top so blade/strut clearance remains reviewable.
  animate(sc,'move');center=Vector((0,0,2.55));sc.camera.data.ortho_scale=7
  for view,pos in enumerate((center+Vector((0,-14,0)),center+Vector((0,0,14)))):
   sc.camera.location=pos;sc.camera.rotation_euler=(center-pos).to_track_quat('-Z','Y').to_euler()
   for i in range(8):sc.frame_set(i+1);render(sc,out/f'{view*8+i:03}.png')
 elif part=='d':
  animate(sc,'attack')
  for i,f in enumerate((1,4,7,10)):sc.frame_set(f);render(sc,out/f'{i:03}.png')
 else:
  clip=part[2:];animate(sc,clip)
  for i in range(CLIPS[clip][0]):
   if clip=='death' and i==9:shutil.copy2(out/'008.png',out/'009.png');continue
   sc.frame_set(i+1);render(sc,out/f'{i:03}.png')
 manifest.write_text(json.dumps({'stage':part,'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':samples,'resolution':res,'master_sha256':hashlib.sha256((M/('plain.blend' if part=='b' else 'drone-swarm.blend')).read_bytes()).hexdigest(),'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))}},indent=2));print('STAGE_COMPLETE',part,flush=True)

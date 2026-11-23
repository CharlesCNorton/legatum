"""Sequential CPU preview or strict Metal GPU rendering, plus editable clip masters."""
import bpy, os, sys, json, math, hashlib, ast, shutil
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0,str(Path(__file__).parent))
from motion import Retarget
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/byzantine-heir'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
if mode not in {'b','check-gpu'}:assert not (M/'bake-required').exists(),'Rebuild requires successful surface bake before animation/render'
def configure():
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'No Metal device: refusing CPU fallback'
  for d in prefs.devices:d.use=d.type=='METAL'
 sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True;sc.render.use_persistent_data=True
 return sc

for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry IK>','exec'))
def make_clips(selected=None):
 global rig
 for clip,(count,fps,loop) in CLIPS.items():
  if selected and clip!=selected:continue
  bpy.ops.wm.open_mainfile(filepath=str(M/'byzantine-heir.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Heir MPFB game_engine'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy();staff=bpy.data.objects['Banner staff control'];staffrest=staff.matrix_basis.copy();staff_world=staff.matrix_world.copy();rootrest=rig.matrix_basis.copy();cloth=[o for o in sc.objects if o.type=='MESH' and o.data.shape_keys and 'Cloth follow through' in o.data.shape_keys.key_blocks]
  motion=Retarget(R,rig,clip,limb) if clip!='attack' else None
  def turn(name,axis,a):
   p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion(axis,a)
  for i in range(count+(1 if loop else 0)):
   t=i/count if loop else i/(count-1);f=i+1;sc.frame_set(f);rig.matrix_basis=rootrest;staff.matrix_basis=staffrest
   for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name]);p.rotation_mode='QUATERNION'
   wave=math.sin(2*math.pi*t)
   for o in cloth:o.data.shape_keys.key_blocks['Cloth follow through'].value=.35*wave
   if clip in {'idle','move','hit'}:
    motion.apply(t,i)
   elif clip=='attack':
    a=[0,-.15,-.25,.3,.9,1,.65,.3,.08,0][i];turn('spine_03',(1,0,0),.15*a);rig.location.y-=.05*a
    if a:
     bpy.context.view_layer.update();hand=rig.pose.bones['hand_r'];grip=hand.head.copy()
     elbow=rig.pose.bones['upperarm_r'].tail.copy();pole=elbow.lerp(Vector((-.65,-.12,1.12)),abs(a))
     limb('upperarm_r','lowerarm_r',grip+Vector((-.05*a,-.20*a,-.06*a)),pole)
     hand=rig.pose.bones['hand_r'];mat=hand.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(-.70*a,4,'Y')@mat;mat.translation=pos;hand.matrix=mat
   elif clip=='death':
    motion.apply(t,i)
    a=min(1,t/.78);a=a*a*(3-2*a)
    for o in cloth:o.data.shape_keys.key_blocks['Cloth follow through'].value=.8*a
    bpy.context.view_layer.update()
    # Banner is explicitly released and settles horizontally; never hidden or zero-scaled.
    release=min(1,max(0,(t-.1)/.58));release=release*release*(3-2*release)
    pivot=Vector((-.46,-.24,1.1));q=Quaternion((0,1,0),-math.pi/2*release);target=Vector((.03,-.38,.16));w=Matrix.Translation(pivot.lerp(target,release))@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)
    staff.matrix_world=w@staff_world
   for p in rig.pose.bones:
    for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
   for prop in ['location','rotation_euler','rotation_quaternion']:rig.keyframe_insert(prop,frame=f)
   for prop in ['location','rotation_euler','scale']:staff.keyframe_insert(prop,frame=f)
   for o in cloth:o.data.shape_keys.key_blocks['Cloth follow through'].keyframe_insert('value',frame=f)
  if clip=='death':
   # A separate authored drape lets distal cloth settle instead of following
   # the rigid torso horizontally. It is deformation, not a physics claim.
   sc.frame_set(count);bpy.context.view_layer.update()
   for ob in cloth:
    if ob.name=='Embroidered purple standard':continue
    key=ob.shape_key_add(name='Settled death drape')
    inv=ob.matrix_world.inverted();rows=40;columns=29
    for index,vertex in enumerate(key.data):
     fraction=(index//columns)/rows;weight=min(1,max(0,(fraction-.20)/.70))
     world=ob.matrix_world@vertex.co
     world.z-=max(0,world.z-.18)*weight
     vertex.co=inv@world
    for i in range(count):
     t=i/(count-1);a=min(1,t/.78);a=a*a*(3-2*a)
     key.value=a*a;key.keyframe_insert('value',frame=i+1)
  if clip=='death':
   # The captured backward fall is longer in depth than the original side
   # collapse. Seat its finished cloak within the token with ground-plane
   # translation only; keep released equipment in its keyed world position.
   for frame in range(1,count+1):
    sc.frame_set(frame);bpy.context.view_layer.update();held=staff.matrix_world.copy()
    deps=bpy.context.evaluated_depsgraph_get();bottom=0
    for ob in sc.objects:
     if ob.type!='MESH' or ob.name=='Stationary cream stone':continue
     if ob in staff.children_recursive:continue
     ev=ob.evaluated_get(deps);me=ev.to_mesh()
     bottom=max(bottom,max((1-world_to_camera_view(sc,sc.camera,ev.matrix_world@v.co).y)*256 for v in me.vertices));ev.to_mesh_clear()
    if bottom>238:
     rig.location.y+=(bottom-238)*sc.camera.data.ortho_scale/256/math.sin(.20)
     rig.keyframe_insert('location',frame=frame);bpy.context.view_layer.update();staff.matrix_world=held
     for prop in ['location','rotation_euler','scale']:staff.keyframe_insert(prop,frame=frame)
  sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc.frame_set(1);sc['clip']=clip;sc['count']=count;sc['source_sha256']=hashlib.sha256((M/'byzantine-heir.blend').read_bytes()).hexdigest();out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'clip.blend'))
  (out/'clip.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sc['source_sha256'],'motion':motion.provenance() if motion else {'method':'Authored weapon-specific attack'}},indent=2))
 print('CLIPS_READY')

if mode=='check-gpu':
 configure();print('GPU_READY')
elif mode=='animate' or mode.startswith('animate-'):
 make_clips(mode.removeprefix('animate-') if mode.startswith('animate-') else None)
else:
 clip='move' if mode=='g-feet' else mode[2:] if mode.startswith('e-') else None
 path=M/'clips'/clip/'clip.blend' if clip else M/('plain.blend' if mode=='b' else 'byzantine-heir.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=configure();out=M/'renders'/mode;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
 frames=list(range(1,CLIPS[clip][0]+1)) if clip else [1]
 if mode=='g-feet':
  frames=frames*2
  for ob in sc.objects:
   if ob.type=='MESH':ob.hide_render=not ob.name.startswith(('Leather toe','Tall leather boot','Stationary cream stone'))
 if mode=='b':
  grey=bpy.data.materials.new('Plain sculpt review');grey.diffuse_color=(.45,.40,.32,1);grey.use_nodes=True;grey.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.45,.40,.32,1);sc.view_layers[0].material_override=grey
 def geometry_signature():
  bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();h=hashlib.sha256()
  for ob in sorted(sc.objects,key=lambda o:o.name):
   if ob.type!='MESH':continue
   ev=ob.evaluated_get(deps);me=ev.to_mesh()
   for v in me.vertices:h.update(str(tuple(round(x,6) for x in ev.matrix_world@v.co)).encode())
   ev.to_mesh_clear()
  return h.hexdigest()
 for i,f in enumerate(frames):
  if mode=='g-feet':
   top=i<8;sc.camera.location=(0,0,4) if top else (0,-4,.50)
   target=Vector((0,0,.15 if top else .30));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=1.5 if top else 1.25
  sc.frame_set(f)
  if clip=='death' and i==len(frames)-1:
   assert geometry_signature()==held_signature,'Terminal death geometry changed'
   shutil.copy2(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
  if clip=='death' and i==len(frames)-2:held_signature=geometry_signature()
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 if mode=='b':
  for label,pos in [('side',(8,0,2.72)),('three-quarter',(4,-7,2.72))]:
   sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.10))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'frames':len(frames),'source_sha256':hashlib.sha256((M/'byzantine-heir.blend').read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frame_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('[0-9][0-9].png'))}},indent=2))
 print('RENDER_READY',mode)

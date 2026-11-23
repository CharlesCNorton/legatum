"""Sequential CPU preview or strict Metal GPU rendering, plus editable clip masters."""
import bpy, os, sys, json, math, hashlib, ast
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/byzantine-heir'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
if mode!='b':assert not (M/'bake-required').exists(),'Rebuild requires successful surface bake before animation/render'
def configure():
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'No Metal device: refusing CPU fallback'
  for d in prefs.devices:d.use=d.type=='METAL'
 sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True;sc.render.use_persistent_data=True
 return sc

for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry IK>','exec'))
def make_clips():
 global rig
 for clip,(count,fps,loop) in CLIPS.items():
  bpy.ops.wm.open_mainfile(filepath=str(M/'byzantine-heir.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Heir MPFB game_engine'];neutral=json.loads(rig['neutral_pose']);base=rig.location.copy();staff=bpy.data.objects['Banner staff control'];staffrest=staff.matrix_basis.copy();staff_world=staff.matrix_world.copy();rootrest=rig.matrix_basis.copy();cloth=[o for o in sc.objects if o.type=='MESH' and o.data.shape_keys and 'Cloth follow through' in o.data.shape_keys.key_blocks]
  def turn(name,axis,a):
   p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion(axis,a)
  for i in range(count+(1 if loop else 0)):
   t=i/count if loop else i/(count-1);f=i+1;sc.frame_set(f);rig.matrix_basis=rootrest;staff.matrix_basis=staffrest
   for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name]);p.rotation_mode='QUATERNION'
   wave=math.sin(2*math.pi*t)
   for o in cloth:o.data.shape_keys.key_blocks['Cloth follow through'].value=.35*wave
   if clip=='idle':
    turn('spine_03',(0,0,1),.012*wave);turn('neck_01',(0,1,0),.012*wave);turn('lowerarm_l',(1,0,0),.018*wave)
   elif clip=='move':
    for side,sgn in [('r',1),('l',-1)]:
     turn('thigh_'+side,(1,0,0),.27*wave*sgn);turn('calf_'+side,(1,0,0),-.33*max(0,wave*sgn));turn('foot_'+side,(1,0,0),-.10*wave*sgn)
    rig.location.z+=.018*(1-cos(4*math.pi*t));turn('spine_03',(0,0,1),.045*wave)
   elif clip=='attack':
    a=[0,-.15,-.25,.3,.9,1,.65,.3,.08,0][i];turn('spine_03',(1,0,0),.15*a);rig.location.y-=.05*a
    bpy.context.view_layer.update();hand=rig.pose.bones['hand_r'];grip=hand.head.copy();limb('upperarm_r','lowerarm_r',grip+Vector((-.05*a,-.20*a,-.06*a)),(-.65,-.12,1.12))
    hand=rig.pose.bones['hand_r'];mat=hand.matrix.copy();pos=mat.translation.copy();mat=Matrix.Rotation(-.70*a,4,'Y')@mat;mat.translation=pos;hand.matrix=mat
   elif clip=='hit':
    a=[0,1,.45,0][i];turn('spine_03',(1,0,0),-.20*a);turn('head',(1,0,0),-.13*a);turn('upperarm_l',(0,0,1),-.1*a);rig.location.y+=.06*a
   elif clip=='death':
    a=min(1,t/.78);a=a*a*(3-2*a);rig.rotation_mode='XYZ';rig.rotation_euler.y=-1.48*a;rig.location.x+=1.02*a;rig.location.z+=.16*a
    turn('thigh_l',(1,0,0),.55*a);turn('calf_l',(1,0,0),-.8*a);turn('thigh_r',(1,0,0),.3*a);turn('calf_r',(1,0,0),-.65*a);turn('spine_03',(1,0,0),.25*a)
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
  sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc.frame_set(1);sc['clip']=clip;sc['count']=count;sc['source_sha256']=hashlib.sha256((M/'byzantine-heir.blend').read_bytes()).hexdigest();out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'clip.blend'))
  (out/'clip.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':sc['source_sha256']},indent=2))
 print('CLIPS_READY')

if mode=='animate':
 from math import cos
 make_clips()
else:
 clip=mode[2:] if mode.startswith('e-') else None
 path=M/'clips'/clip/'clip.blend' if clip else M/('plain.blend' if mode=='b' else 'byzantine-heir.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=configure();out=M/'renders'/mode;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
 frames=list(range(1,CLIPS[clip][0]+1)) if clip else [1]
 if mode=='b':
  grey=bpy.data.materials.new('Plain sculpt review');grey.diffuse_color=(.45,.40,.32,1);grey.use_nodes=True;grey.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.45,.40,.32,1);sc.view_layers[0].material_override=grey
 for i,f in enumerate(frames):
  sc.frame_set(f);sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 if mode=='b':
  for label,pos in [('side',(8,0,2.72)),('three-quarter',(4,-7,2.72))]:
   sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.10))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'frames':len(frames),'source_sha256':hashlib.sha256((M/'byzantine-heir.blend').read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frame_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('[0-9][0-9].png'))}},indent=2))
 print('RENDER_READY',mode)

"""CC0 Quaternius skeletal clips, original spear thrust, independent releases."""
import bpy,os,json,math,hashlib,sys,ast
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
sys.path.insert(0,str(Path(__file__).parent))
from retarget import prepare,apply_matrices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';source=M/'barbarian-spearman.blend'
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry IK>','exec'))
clips={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def rotate(name,axis,angle):
 p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.rotation_quaternion=p.rotation_quaternion@Quaternion(axis,angle)
def smooth(t):return t*t*(3-2*t)
def surface_low(names):
 dg=bpy.context.evaluated_depsgraph_get();low=10
 for name in names:
  ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh()
  low=min(low,min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
 return low
for clip,(count,fps,loop) in clips.items():
 if os.environ.get('CLIP') and clip not in os.environ['CLIP'].split(','):continue
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Barbarian skeleton'];base=bpy.data.objects['Stationary cream base'];base_matrix=base.matrix_world.copy()
 neutral={p.name:p.matrix_basis.copy() for p in rig.pose.bones};root=rig.location.copy()
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 weapon=bpy.data.objects['Spear grip control'];wrest=weapon.matrix_world.copy()
 hand_pose_rest=rig.pose.bones['hand_r'].matrix.copy();hand_rest=rig.matrix_world@hand_pose_rest
 shield=bpy.data.objects['Shield grip control'];shield_rest=shield.matrix_world.copy();arm_rest=rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix
 if clip=='death':
  weapon.parent=None;weapon.matrix_world=wrest;shield.parent=None;shield.matrix_world=shield_rest
  weapon_release=wrest.copy();shield_release=shield_rest.copy()
 sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 samples=list(range(1,count+1))
 if clip=='death':samples[-1]=samples[-2]
 phases=[i/count if loop else min(i/7,1) if clip=='death' else i/(count-1) for i in range(count+int(loop))]
 motion,provenance=prepare(rig,R,clip,phases) if clip!='attack' else (None,{'provider':'Original spear-specific attack'})
 (M/'clips').mkdir(exist_ok=True);(M/'clips'/f'{clip}-motion.json').write_text(json.dumps(provenance,indent=2))
 contact=[]
 cloth=[o for o in sc.objects if o.type=='MESH' and o.name.startswith(('Folded fur cloak','Cloak fur lock'))] if clip=='death' else []
 for ob in cloth:ob.shape_key_add(name='Rest folds')
 for i,t in enumerate(phases):
  sc.frame_set(i+1);rig.location=root;rig.rotation_euler=(0,0,0)
  for p in rig.pose.bones:p.matrix_basis=neutral[p.name]
  bpy.context.view_layer.update()
  if motion:
   apply_matrices(rig,motion[i]['matrices']);rig.location=root+motion[i]['root'];bpy.context.view_layer.update()
   if clip=='move':
    # Fit the library gait to the miniature's bent-knee guard and fixed canvas.
    # Lower hips 65mm, solve knees to the same captured ankles, retain captured
    # foot WORLD rotations exactly (no yaw/flat-foot correction).
    ankle={side:rig.pose.bones['foot_'+side].matrix.copy() for side in ['r','l']}
    knees={side:rig.pose.bones['calf_'+side].head.copy() for side in ['r','l']}
    rig.location.z-=.065;bpy.context.view_layer.update()
    for side in ['r','l']:
     target=ankle[side].translation+Vector((0,0,.065))
     limb('thigh_'+side,'calf_'+side,target,knees[side])
     foot=rig.pose.bones['foot_'+side];mat=ankle[side].copy();mat.translation=foot.head.copy();foot.matrix=mat;bpy.context.view_layer.update()
   if clip in {'idle','move','hit'}:
    low=surface_low(['Lasted leather shoe r','Lasted leather shoe l'])
    rig.location.z+=.092-low;bpy.context.view_layer.update()
   else:
    # A real source fall; root-only translation places anatomy onto the stone.
    low=surface_low(['MPFB barbarian anatomy','Lasted leather shoe r','Lasted leather shoe l'])
    rig.location.z+=.095-low;bpy.context.view_layer.update()
    fall=smooth(min(1,t/.85))
    if t<.14:
     weapon.matrix_world=(rig.matrix_world@rig.pose.bones['hand_r'].matrix)@hand_rest.inverted()@wrest
     shield.matrix_world=(rig.matrix_world@rig.pose.bones['lowerarm_l'].matrix)@arm_rest.inverted()@shield_rest
     weapon_release=weapon.matrix_world.copy();shield_release=shield.matrix_world.copy()
    else:
     drop=smooth(min(1,(t-.14)/.65))
     weapon.matrix_world=weapon_release.lerp(Matrix.Translation((-.45,-.52,.13))@Matrix.Rotation(-.28,4,'Y'),drop)
     shield.matrix_world=shield_release.lerp(Matrix.Translation((.28,.10,.28))@Matrix.Rotation(1.45,4,'X'),drop)
     bpy.context.view_layer.update()
     for control in [weapon,shield]:
      parts=[o.name for o in control.children if o.type=='MESH']
      control.location.z+=max(0,.095-surface_low(parts))
      bpy.context.view_layer.update()
    for ob in [weapon,shield]:
     ob.rotation_mode='QUATERNION';ob.keyframe_insert('location',frame=i+1);ob.keyframe_insert('rotation_quaternion',frame=i+1)
    for digit in ['index','middle','ring','pinky']:
     for k in range(1,4):rotate(f'{digit}_{k:02d}_r',(1,0,0),-.65*fall)
  else:
   pulse=[0,-.15,-.30,.35,1.,.82,.48,.18,.04,0][i]
   rotate('spine_03',(0,1,0),-.08*pulse);bpy.context.view_layer.update()
   target=hand_pose_rest.translation+Vector((.065,-.18,.090))*pulse
   limb('upperarm_r','lowerarm_r',target,(-.55,-.10,1.17))
   hand=rig.pose.bones['hand_r'];hm=hand_pose_rest.copy();hm.translation=hand.head.copy();pivot=hm.translation.copy()
   hand.matrix=Matrix.Translation(pivot)@Matrix.Rotation(-.12*pulse,4,'Y')@Matrix.Translation(-pivot)@hm
   rotate('upperarm_l',(0,1,0),.04*pulse)
   rotate('thigh_r',(1,0,0),.06*pulse);rotate('calf_r',(1,0,0),-.05*pulse)
  bpy.context.view_layer.update()
  if clip=='death':
   fold=smooth(max(0,min(1,(t-.28)/.60)))
   for ob in cloth:
    # Drape the loose cloth/pelt toward the support plane after the captured fall.
    key=ob.shape_key_add(name=f'Contact folds {i+1}');inv=ob.matrix_world.inverted()
    for v,k in zip(ob.data.vertices,key.data):
     world=ob.matrix_world@v.co
     world.z=.10+max(0,world.z-.10)*(1-.62*fold)
     k.co=inv@world
    key.value=0;key.keyframe_insert('value',frame=max(0,i));key.value=1;key.keyframe_insert('value',frame=i+1);key.value=0;key.keyframe_insert('value',frame=i+2)
  if clip=='move':
   contact.append({'frame':i+1,'soles':{s:surface_low(['Lasted leather shoe '+s]) for s in ['r','l']},'toes':{s:list(rig.matrix_world@rig.pose.bones['ball_'+s].head) for s in ['r','l']},'foot_rotations':{s:list(rig.pose.bones['foot_'+s].matrix.to_quaternion()) for s in ['r','l']}})
  for p in rig.pose.bones:
   for prop in ['rotation_quaternion','location','scale']:p.keyframe_insert(prop,frame=i+1)
  rig.keyframe_insert('location',frame=i+1);rig.keyframe_insert('rotation_euler',frame=i+1)
  assert base.matrix_world==base_matrix,'Base moved'
 if clip=='move':(M/'clips'/'move-contact.json').write_text(json.dumps(contact,indent=2))
 if rig.animation_data:rig.animation_data.action.name='Barbarian '+clip+' '+provenance['provider']
 for ob in [rig,weapon,shield]:
  if not ob.animation_data or not ob.animation_data.action:continue
  for layer in ob.animation_data.action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type=kp.handle_right_type='AUTO_CLAMPED'
 sc['sample_frames']=json.dumps(samples);sc['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();sc['clip']=clip;sc['loop']=loop;sc['motion_provider']=provenance['provider']
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));print('CLIP_READY',clip,flush=True)

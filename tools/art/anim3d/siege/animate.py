"""Authored MPFB performance, physical rolling ratio, bounded 3D firing effects."""
import bpy,os,json,math,hashlib,sys
from pathlib import Path
from math import sin,cos,pi
from mathutils import Matrix,Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def descendants(o):
 return [x for x in bpy.context.scene.objects if x==o or x in o.children_recursive]
def lowest(objects):
 dg=bpy.context.evaluated_depsgraph_get();zs=[]
 for o in objects:
  if o.type not in ['MESH','CURVE'] or o.hide_render:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh()
  zs.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
 return min(zs)
def aim(rig,name,d):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();rot=((q @ Vector((0,1,0))).rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy()
 if name.startswith(('upperarm_','lowerarm_')):rot=rot @ Matrix.Diagonal((1,rig.get('arm_length_factor',1),1,1))
 p.matrix=rot;bpy.context.view_layer.update()
def limb(rig,up,low,t,pole):
 a=rig.pose.bones[up].head.copy();delta=Vector(t)-a;factor=rig.get('arm_length_factor',1) if up.startswith('upperarm_') else 1;l1=rig.data.bones[up].length*factor;l2=rig.data.bones[low].length*factor;d=min(delta.length,l1+l2-.0001);delta.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5
 side=Vector(pole)-a;side=(side-delta*side.dot(delta)).normalized();el=a+delta*along+side*h;aim(rig,up,el-a);aim(rig,low,Vector(t)-el)
def rotate(rig,bone,axis,a):
 p=rig.pose.bones[bone];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(a,4,axis);bpy.context.view_layer.update()
def effectmat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.95;return m
def smoke_material():
 # Full-depth volume with density tapering to zero at the surface; no opaque pellets.
 m=bpy.data.materials.new('Soft powder smoke volume');m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');volume=n.new('ShaderNodeVolumePrincipled')
 volume.inputs['Color'].default_value=(.62,.60,.54,1);volume.inputs['Anisotropy'].default_value=.1
 tc=n.new('ShaderNodeTexCoord');distance=n.new('ShaderNodeVectorMath');distance.operation='DISTANCE';distance.inputs[1].default_value=(.5,.5,.5);l.new(tc.outputs['Generated'],distance.inputs[0])
 radial=n.new('ShaderNodeMapRange');radial.inputs['From Min'].default_value=.12;radial.inputs['From Max'].default_value=.50;radial.inputs['To Min'].default_value=14;radial.inputs['To Max'].default_value=0;radial.clamp=True;l.new(distance.outputs['Value'],radial.inputs[0])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=2;l.new(tc.outputs['Generated'],noise.inputs['Vector'])
 density=n.new('ShaderNodeMath');density.operation='MULTIPLY';l.new(radial.outputs[0],density.inputs[0]);l.new(noise.outputs['Fac'],density.inputs[1]);l.new(density.outputs[0],volume.inputs['Density']);l.new(volume.outputs['Volume'],out.inputs['Volume'])
 return m
requested=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else None
if requested:assert requested in CLIPS,requested
for clip,(count,fps,loop) in CLIPS.items():
 if requested and clip!=requested:continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Gunner MPFB game_engine'];gun=bpy.data.objects['Gun travel and recoil'];wheels=[bpy.data.objects['Wheel '+str(s)] for s in [-1,1]];rammer=bpy.data.objects['Rammer hand control'];barrel=bpy.data.objects['Barrel elevation']
 neutral=json.loads(rig['neutral_pose']);start=rig.location.copy();neutralgun=gun.location.copy();gunangle=gun.rotation_euler.copy();crew=descendants(rig);gunparts=descendants(gun);rammerparts=descendants(rammer)
 # One hand-held tool becomes securely stowed alongside the trail during transport.
 if clip=='move':
  bpy.context.view_layer.update();w=rammer.matrix_world.copy();rammer.parent=gun;rammer.parent_type='OBJECT';rammer.matrix_world=w
  rammer.rotation_euler=(0,pi/2,0);rammer.location=(.40,.29,.34)
 # Release the rammer in death so it cannot lever the fallen person off the base.
 if clip=='death':
  bpy.context.view_layer.update();rammer_start=rammer.matrix_world.copy();rammer.parent=None;rammer.matrix_world=rammer_start
  rammer_start_pos=rammer.location.copy();rammer_start_rot=rammer.rotation_euler.to_quaternion();rammer.rotation_mode='QUATERNION'
  crew=descendants(rig)
 smoke=[];flash=None
 if clip=='attack':
  sm=smoke_material();fm=effectmat('Muzzle fire ochre',(.95,.48,.08));p=fm.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.32,.035,1);p.inputs['Emission Strength'].default_value=2
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);flash=bpy.context.object;flash.name='Bounded three dimensional muzzle flash';flash.data.materials.append(fm)
  for i in range(7):
   bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);o=bpy.context.object;o.name=f'Bounded smoke lobe {i}';o.data.materials.append(sm)
   for p in o.data.polygons:p.use_smooth=True
   smoke.append(o)
 frames=list(range(1,count+1));sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps
 for i,frame in enumerate(frames):
  # Identical last two death samples are a real held pose, not two different settles.
  t=i/count if loop else min(i,count-2)/(count-2) if clip=='death' else i/(count-1);phase=2*pi*t
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.matrix_basis=Matrix(neutral[p.name])
  rig.location=start;rig.rotation_euler=(0,0,0);gun.location=neutralgun;gun.rotation_euler=gunangle
  for w in wheels:w.rotation_euler=(0,0,0)
  if clip=='idle':
   rotate(rig,'spine_02','X',.016*sin(phase));rotate(rig,'head','Z',.035*sin(phase))
   target=rig.matrix_world.inverted() @ (barrel.matrix_world @ Vector(rig['barrel_contact_local']))-Vector((.11,-.015,-.03)).normalized()*rig.data.bones['hand_l'].length
   limb(rig,'upperarm_l','lowerarm_l',target,(.56,-.24,1.14));aim(rig,'hand_l',(.11,-.015,-.03))
  elif clip=='move':
   # Ground travel is removed from sprite root by the map; 12-fold wheel symmetry
   # gives an exact cyclic seam after one spoke pitch. theta = distance / radius.
   distance=.48*(2*pi/12)*t;localtravel=.018*sin(phase);theta=(distance+localtravel)/.48
   for w in wheels:w.rotation_euler.y=theta
   gun.location=neutralgun+Vector((localtravel*cos(gunangle.z),localtravel*sin(gunangle.z),0))
   rig.location.x+=.018*sin(phase);rotate(rig,'spine_01','X',.13);rotate(rig,'spine_02','Y',.12)
   for side,offset in [('l',0),('r',pi)]:
    stride=sin(phase+offset);lift=max(0,cos(phase+offset))*.045
    limb(rig,'thigh_'+side,'calf_'+side,((.17 if side=='l' else -.19)+.055*stride,-.035+.075*stride,.07+lift),(.2 if side=='l' else -.2,-.35,.5))
   limb(rig,'upperarm_r','lowerarm_r',(.28,.10,.94),(-.30,-.35,1.1))
   bpy.context.view_layer.update()
   target=rig.matrix_world.inverted() @ (barrel.matrix_world @ Vector(rig['barrel_contact_local']))-Vector((.11,-.015,-.03)).normalized()*rig.data.bones['hand_l'].length
   limb(rig,'upperarm_l','lowerarm_l',target,(.56,-.24,1.14));aim(rig,'hand_l',(.11,-.015,-.03))
  elif clip=='attack':
   recoil=[0,0,-.105,-.13,-.085,-.04,-.014,0,0,0][i];gun.location=neutralgun+Vector((recoil*cos(gunangle.z),recoil*sin(gunangle.z),0));bpy.context.view_layer.update()
   for w in wheels:w.rotation_euler.y=recoil/.48
   react=[0,-.025,.16,.23,.16,.09,.03,0,0,0][i];rotate(rig,'spine_01','Y',-react);rotate(rig,'head','X',react*.6);rotate(rig,'upperarm_l','Z',react)
   visible=1 if i==2 else 0;muzzle=barrel.matrix_world @ Vector((.76,0,.02));forward=(barrel.matrix_world.to_3x3() @ Vector((1,0,0))).normalized();flash.location=muzzle+forward*.10;flash.rotation_euler=barrel.matrix_world.to_euler();flash.scale=(.20,.065,.055);flash.hide_render=not visible;flash.keyframe_insert(data_path='hide_render',frame=frame)
   flash.keyframe_insert(data_path='scale',frame=frame);flash.keyframe_insert(data_path='location',frame=frame)
   for j,o in enumerate(smoke):
    age=max(0,(i-2)/6);size=(.055+.045*age)*(sin(pi*min(age,1)) if i>=2 else 0)
    o.location=muzzle+forward*(.06+.07*age)+Vector((.025*cos(j*2.4),.035*sin(j*2.4),.03+.21*age+.045*sin(j*1.3)));o.hide_render=size<.01;o.keyframe_insert(data_path='hide_render',frame=frame);size=max(.02,size);o.scale=(size*1.2,size,size*.9);o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='scale',frame=frame)
  elif clip=='hit':
   a=[0,.17,-.065,0][i];localtravel=-a*.23;gun.rotation_euler.z=gunangle.z+a*.1
   for w in wheels:w.rotation_euler.y=localtravel/.48
   gun.location=neutralgun+Vector((localtravel*cos(gunangle.z),localtravel*sin(gunangle.z),0))
   rotate(rig,'spine_02','Y',-a);rotate(rig,'head','X',-a*.7);rotate(rig,'upperarm_r','Z',a)
  else:
   fall=max(0,min(1,(t-.12)/.70));ease=fall*fall*(3-2*fall)
   rig.location.x=start.x+1.55*ease**.65;rig.location.y=start.y-.36*ease
   endrot=(Matrix.Rotation(pi/2,4,'Z') @ Matrix.Rotation(-pi/2,4,'X')).to_quaternion();rig.rotation_euler=Matrix.Identity(4).to_quaternion().slerp(endrot,ease).to_euler()
   rotate(rig,'thigh_l','X',.20*sin(pi*fall));rotate(rig,'thigh_r','X',-.14*sin(pi*fall))
   for side,sg in [('l',1),('r',-1)]:
    target=rig.pose.bones['hand_'+side].head.lerp(Vector((sg*.25,-.08,1.0)),ease);limb(rig,'upperarm_'+side,'lowerarm_'+side,target,(sg*.40,-.1,1.15))
   gun.rotation_euler.x=-.08*ease;gun.location.y=neutralgun.y+.18*ease;gun.location.x=neutralgun.x-.17*ease
   wheels[0].rotation_euler.x=.10*ease # damaged near-wheel cant, visible broken axle attitude
   bpy.context.view_layer.update()
   # Settle actual evaluated geometry on top of the disc, including carried tool.
   rig.location.z+=.098-lowest(crew);gun.location.z+=.098-lowest(gunparts)
   prop_ease=min(1,fall*2.2);rammer.location=rammer_start_pos.lerp(Vector((.60,-.65,.16)),prop_ease);rammer.rotation_quaternion=rammer_start_rot.slerp(Matrix.Rotation(pi/2,4,'Y').to_quaternion(),prop_ease)
   bpy.context.view_layer.update();rammer.location.z+=.098-lowest(descendants(rammer))
   rammer.keyframe_insert(data_path='location',frame=frame);rammer.keyframe_insert(data_path='rotation_quaternion',frame=frame)
  bpy.context.view_layer.update()
  for o in [rig,gun,*wheels]:
   o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='rotation_euler',frame=frame)
  for p in rig.pose.bones:
   p.rotation_mode='QUATERNION';p.keyframe_insert(data_path='location',frame=frame);p.keyframe_insert(data_path='rotation_quaternion',frame=frame);p.keyframe_insert(data_path='scale',frame=frame)
 sc['clip']=clip;sc['sample_frames']=json.dumps(frames);sc['loop']=loop;sc['wheel_motion']='theta = (virtual ground travel + local recoil/travel) / 0.48; 12-spoke cyclic symmetry';sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'source_master_sha256':hashlib.sha256((M/'field-cannon.blend').read_bytes()).hexdigest(),'frames':count,'fps':fps,'loop':loop},indent=2))
 print('CLIP_READY',clip,count)

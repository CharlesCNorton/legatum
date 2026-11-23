"""Retarget CC0 full-body actions, layer weapon attack/release, bake real cloth."""
import bpy,os,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path('tools/art/anim3d').resolve()))
sys.path.insert(0,str(Path('tools/art/anim3d/units/spartan-hoplite').resolve()))
from retarget import prepare, apply_matrices
root=Path(os.environ['ANIM_ROOT']);M=Path(os.environ.get('ANIM_MASTER', str(root/'masters/spearman-3d-v2')));A=root/'assets'
CLIPS={'idle':(8,4),'move':(8,6),'attack':(10,14),'hit':(4,8),'death':(10,5)}

clip=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'idle'
out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True)
(out/'clip.json').unlink(missing_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=3;rig=bpy.data.objects['Spearman • MPFB game_engine'];neutral=json.loads(rig['neutral_pose'])
base_loc=rig.location.copy()
spear_objects=[o for o in sc.objects if any(o.name.startswith(n) for n in ['Ash dory shaft','Spear bronze ferrule','Leaf spearhead','Iron spear butt'])]
spear_neutral={o.name:o.matrix_basis.copy() for o in spear_objects}
spear_rest_world={o.name:o.matrix_world.copy() for o in spear_objects}
for o in spear_objects:o.rotation_mode='QUATERNION'

shield=bpy.data.objects.get('Aspis control');shield_neutral=shield.matrix_basis.copy() if shield else None
if shield:shield.rotation_mode='QUATERNION'
cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip']
cloth.show_viewport=False
for p in rig.pose.bones:p.rotation_mode='QUATERNION'
def reset():
 rig.location=base_loc
 if shield:shield.matrix_basis=shield_neutral
 for o in spear_objects:o.matrix_basis=spear_neutral[o.name]
 for p in rig.pose.bones:p.matrix_basis=Matrix(neutral[p.name])
 bpy.context.view_layer.update()
def aim(name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q @ Vector((0,1,0))).rotation_difference(Vector(direction).normalized())
 mat=(delta @ q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
def limb(u,l,target,pole):
 a=rig.pose.bones[u].head.copy();v=Vector(target)-a;d=min(v.length,rig.data.bones[u].length+rig.data.bones[l].length-.0001);v.normalize()
 l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;along=(l1*l1-l2*l2+d*d)/(2*d)
 side=Vector(pole)-a;side=(side-v*side.dot(v)).normalized();elbow=a+along*v+max(0,l1*l1-along*along)**.5*side
 aim(u,elbow-a);aim(l,Vector(target)-elbow)
def turn(name,axis,angle):
 p=rig.pose.bones[name];mat=p.matrix.copy();rot=Matrix.Rotation(angle,4,axis);pos=mat.translation.copy();mat=rot @ mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
def hand_spear(direction):
 # Weapon was attached in neutral pose: rotate hand from neutral, not from rest.
 p=rig.pose.bones['hand_r'];reset_mat=p.matrix.copy();q=Vector((0,0,1)).rotation_difference(Vector(direction))
 rot=q.to_matrix().to_4x4();pos=reset_mat.translation.copy();mat=rot @ reset_mat;mat.translation=pos;p.matrix=mat;bpy.context.view_layer.update()
def pose(t):
 reset()
 if clip!='attack':
  phase=(3*t if t<1/3 else 1-(t-1/3)*1.5) if clip=='hit' else t
  sample=min(72,24+round(phase*48))
  motion=motion_frames[sample];rig.location=base_loc+motion['root'];apply_matrices(rig,motion['matrices'])
  if clip=='death' and t<.28:
   # Crossfade out of the equipment guard into the source's anatomical pose;
   # preserve the donor limb rotations through the fall and terminal contact.
   blend=t/.28;blend=blend*blend*(3-2*blend)
   for p in rig.pose.bones:
    l0,q0,s0=Matrix(neutral[p.name]).decompose();l1,q1,s1=p.matrix_basis.decompose()
    p.matrix_basis=Matrix.LocRotScale(l0.lerp(l1,blend),q0.slerp(q1,blend),s0.lerp(s1,blend))
   bpy.context.view_layer.update()
  if clip=='move':
   flags=motion_source['contact']['planted'].get(str(sample+1),{})
   support=next((side for side in ('l','r') if flags.get(side)),None)
   lows=[]
   for side in ([support] if support else ['l','r']):
    sole=bpy.data.objects['Leather sandal sole '+side];ev=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    lows.append(min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
   rig.location.z+=.10-min(lows);bpy.context.view_layer.update()
 elif clip=='attack':
  # Raise outside the right shoulder, then drive forward above the shield rim.
  # Right hand stays on the shaft; the rear shaft stays outside the torso.
  strength=[0,.05,.22,.72,1,1,.68,.25,.05,0][min(9,round(t*9))]
  raised=[0,.35,.90,1,1,1,1,.85,.30,0][min(9,round(t*9))]
  rig.location=base_loc+Vector((.12*strength,-.16*strength,-.12*strength))
  turn('spine_03','X',.20*strength);turn('spine_03','Y',.15*strength)
  # Counter root travel in the ankle targets: soles remain on the disc.
  limb('thigh_l','calf_l',(.32+.08*strength,.035-.18*strength,.082+.12*strength),(.42,-.50,.48))
  limb('thigh_r','calf_r',(-.25-.12*strength,-.075+.16*strength,.082+.12*strength),(-.40,-.20,.48))
  limb('upperarm_r','lowerarm_r',(-.37+.10*strength,-.31-.10*raised-.05*strength,1.43+.28*raised),tuple(Vector((-.55,-.04,.95)).lerp(Vector((-.65,.05,1.48)),raised)))
  limb('upperarm_l','lowerarm_l',(.29,-.34-.10*strength,1.12+.10*strength),(.55,-.12,1.20))
  aim('hand_r',(0,-.03,.09));hand_spear(Vector((.98,.17,.12))*raised+Vector((0,0,1))*(1-raised))
 bpy.context.view_layer.update()
 if clip=='attack':
  for side in ['l','r']:
   aim('foot_'+side,(0,-.12,-.045));aim('ball_'+side,(0,-1,0))
 if clip=='attack':
  lows=[]
  for side in ['l','r']:
   sole=bpy.data.objects['Leather sandal sole '+side];ev=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   lows.append(min((ev.matrix_world @ v.co).z for v in mesh.vertices));ev.to_mesh_clear()
  rig.location.z+=.10-min(lows);bpy.context.view_layer.update()
 if clip=='attack':
  # Slide the grip down the shaft during extension; preserve a continuous grip
  # while keeping both ends of the long spear inside the fixed atlas cell.
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  direction=(shaft.matrix_world @ Vector(pts[-1].co[:3])-shaft.matrix_world @ Vector(pts[0].co[:3])).normalized()
  for o in spear_objects:
   mat=o.matrix_world.copy();mat.translation+=direction*(float(os.environ.get('ANIM_ATTACK_SLIDE','.25'))*raised+.29*max(0,min(1,(raised-.4)/.4)));o.matrix_world=mat
  bpy.context.view_layer.update()
 if clip in ['idle','move','hit']:
  butt=bpy.data.objects['Iron spear butt'];ev=butt.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  lowest=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
  if lowest<.10:
   shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
   axis=(shaft.matrix_world @ Vector(pts[-1].co[:3])-shaft.matrix_world @ Vector(pts[0].co[:3])).normalized()
   assert axis.z>.5
   for ob in spear_objects:
    mat=ob.matrix_world.copy();mat.translation+=axis*((.10-lowest)/axis.z);ob.matrix_world=mat
   bpy.context.view_layer.update()
 if clip=='death' and t>0:
  dg=bpy.context.evaluated_depsgraph_get();lowest=10
  # Ground the worn kit as well as anatomy; exclude the separately released
  # equipment and simulated cloth, which have their own contact constraints.
  for ob in sc.objects:
   if ob.type!='MESH' or ob.hide_render or ob in spear_objects or ob.parent==shield or ob.name in ['Stationary cream stone','Cloak • simulated wool']:continue
   ev=ob.evaluated_get(dg);me=ev.to_mesh()
   lowest=min(lowest,min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
  rig.location.z+=.10-lowest;bpy.context.view_layer.update()
 if clip=='death':
  # Let go before the body rolls across the shaft. The rigid weapon lands across
  # the front edge of the stone; it is never hidden or teleported out of frame.
  release=max(0,min(1,(t-.04)/.44))
  if release>0:
   # Once released, the falling weapon no longer inherits the source hand's
   # changing orientation. Its independent rigid trajectory starts at rest.
   for ob in spear_objects:ob.matrix_world=spear_rest_world[ob.name]
   bpy.context.view_layer.update()
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  start=shaft.matrix_world @ Vector(pts[0].co[:3]);end=shaft.matrix_world @ Vector(pts[-1].co[:3])
  center=(start+end)*.5;direction=(end-start).normalized()
  # Clear the shield in depth while upright, tip forward, then settle inward
  # only after the shaft is horizontal and below the shield's lower edge.
  depth=min(1,release/.20);depth=depth*depth*(3-2*depth)
  tilt=max(0,min(1,(release-.20)/.55));tilt=tilt*tilt*(3-2*tilt)
  rotation=Quaternion().slerp(direction.rotation_difference(Vector((.99,.08,.015)).normalized()),tilt)
  target=center.lerp(Vector((-.05,-.57,.13)),release)
  target.x+=.13*math.sin(math.pi*release)
  target.y=center.y+(-.78-center.y)*depth
  if release>.80:target.y=-.78+.21*(release-.80)/.20
  drop=min(1,release/.75)
  target.z=center.z*(1-drop)+.13*drop
  if release>0:target.z=max(target.z,.11+(end-start).length*.5*abs((rotation @ direction).z))
  transform=Matrix.Translation(target) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-center)
  for o in spear_objects:o.matrix_world=transform @ o.matrix_world
  for digit in ['index','middle','ring','pinky']:
   for k in range(1,4):
    p=rig.pose.bones[f'{digit}_{k:02d}_r'];p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),min(1,release*4))
  bpy.context.view_layer.update()
  if release>0:
   # Free equipment stays inside the fixed token frame; camera never zooms.
   dg=bpy.context.evaluated_depsgraph_get();points=[]
   for ob in spear_objects:
    ev=ob.evaluated_get(dg);me=ev.to_mesh()
    points.extend(world_to_camera_view(sc,sc.camera,ev.matrix_world @ v.co) for v in me.vertices);ev.to_mesh_clear()
   dx=max(0,.025-min(p.x for p in points))-max(0,max(p.x for p in points)-.975)
   dy=max(0,.025-min(p.y for p in points))-max(0,max(p.y for p in points)-.975)
   q=sc.camera.matrix_world.to_quaternion();shift=(q @ Vector((dx,dy,0)))*sc.camera.data.ortho_scale
   for ob in spear_objects:
    mat=ob.matrix_world.copy();mat.translation+=shift;ob.matrix_world=mat
   bpy.context.view_layer.update()
 if clip=='death' and shield:
  release=max(0,min(1,(t-.30)/.42));mat=shield.matrix_world.copy();q=mat.to_quaternion().slerp(Matrix.Rotation(-math.pi/2,4,'X').to_quaternion(),release)
  pos=mat.translation.lerp(Vector((.14,.02,.28)),release)
  mat=q.to_matrix().to_4x4();mat.translation=pos;shield.matrix_world=mat
  bpy.context.view_layer.update()
  # Contact correction for the released shield, using evaluated mesh geometry.
  dg=bpy.context.evaluated_depsgraph_get();lowest=10
  for ob in shield.children:
   ev=ob.evaluated_get(dg);me=ev.to_mesh()
   lowest=min(lowest,min((ob.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
  if lowest<.10 or (os.environ.get('ANIM_SHIELD_SETTLE')=='1' and release>.8):
   parent_matrix=shield.matrix_world @ shield.matrix_basis.inverted()
   shield.location+=parent_matrix.to_3x3().inverted() @ Vector((0,0,.10-lowest))
   bpy.context.view_layer.update()
motion_frames=None;motion_source={'provider':'Original weapon-specific attack'}
if clip!='attack':
 motion_frames,motion_source=prepare(rig,root,clip,[0.0]*24+[i/48 for i in range(49)])
 reset()
if clip=='death':
 # A real collision floor catches the cloak beyond the disc edge. It is not
 # rendered; it has finite thickness and is never hidden with zero scale.
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.02))
 ground=bpy.context.object;ground.name='Death cloth ground collider';ground.scale=(4,4,.2)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ground.hide_render=True;ground.modifiers.new('Cloth ground contact','COLLISION')
 ground.collision.thickness_outer=.006
count,fps=CLIPS[clip];samples=[25+round(i*24/fps) for i in range(count)]
# Give cloth one second to settle before any output sample.
end=samples[-1];sc.frame_start=1;sc.frame_end=end;sc.render.fps=24
for f in range(1,end+1):
 sc.frame_set(f)
 t=max(0,min(1,(f-25)/max(1,end-25)))
 # Loop clips sample before the duplicate final phase.
 if clip in ['idle','move']:t=max(0,(f-25))/(count*24/fps)
 pose(t)
 rig.keyframe_insert(data_path='location',frame=f)
 for o in spear_objects:
  o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='rotation_quaternion',frame=f)
 if shield:
  shield.keyframe_insert(data_path='location',frame=f);shield.keyframe_insert(data_path='rotation_quaternion',frame=f)
 for p in rig.pose.bones:
  p.rotation_mode='QUATERNION';p.keyframe_insert(data_path='location',frame=f);p.keyframe_insert(data_path='rotation_quaternion',frame=f);p.keyframe_insert(data_path='scale',frame=f)
# Fail on rigid equipment crossings before spending time baking cloth.
for frame in samples:
 sc.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
 shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
 start=shaft.matrix_world @ Vector(pts[0].co[:3]);shaft_end=shaft.matrix_world @ Vector(pts[-1].co[:3])
 direction=shaft_end-start;length=direction.length;direction.normalize()
 for name in ['Forged bronze muscle cuirass','Convex bronze aspis','Corinthian helmet crown']:
  ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh()
  tree=BVHTree.FromPolygons([ob.matrix_world @ v.co for v in me.vertices],[list(poly.vertices) for poly in me.polygons])
  crossing=tree.ray_cast(start,direction,length)[0];ev.to_mesh_clear()
  assert crossing is None,f'{clip}/{frame}: spear intersects {name}; fix pose before cloth bake'
cloth.show_viewport=True
sc.frame_set(1)
cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip'];pc=cloth.point_cache;pc.frame_start=1;pc.frame_end=end
# Blender cache stored alongside each master, outside git.
bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
with bpy.context.temp_override(point_cache=pc):bpy.ops.ptcache.bake(bake=True)
assert pc.is_baked, 'Cloth bake did not complete'
if clip=='death':samples[-2]=samples[-1]
sc['source_master_sha256']=hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest()
sc['spear_release_start']=.04 if clip=='death' else -1
sc['attack_guard_extra_slide']=.29
sc['attack_slide']=float(os.environ.get('ANIM_ATTACK_SLIDE','.25'))
sc['clip']=clip;sc['sample_frames']=json.dumps(samples);sc['cloth_baked']=True
sc.frame_set(samples[0]);bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
(out/'clip.json').write_text(json.dumps({'source_master_sha256':sc['source_master_sha256'],'clip':clip,'frames':samples,'fps':fps,'cloth_baked':pc.is_baked,'motion':motion_source},indent=2))
print('CLIP_READY',clip, samples)

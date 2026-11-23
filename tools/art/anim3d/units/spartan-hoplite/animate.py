"""Retarget CMU standing/walk, layer weapon poses, bake real cloth per clip."""
import bpy,os,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path('tools/art/anim3d').resolve()))
from mocap import BVH
root=Path(os.environ['ANIM_ROOT']);M=Path(os.environ.get('ANIM_MASTER', str(root/'masters/spearman-3d-v2')));A=root/'assets'
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
walk=BVH(A/'cmu-02_01.bvh');stand=BVH(A/'cmu-77_02.bvh')
clip=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'idle'
out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True)
(out/'clip.json').unlink(missing_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=3;rig=bpy.data.objects['Spearman • MPFB game_engine'];neutral=json.loads(rig['neutral_pose'])
base_loc=rig.location.copy()
spear_objects=[o for o in sc.objects if any(o.name.startswith(n) for n in ['Ash dory shaft','Spear bronze ferrule','Leaf spearhead','Iron spear butt'])]
spear_neutral={o.name:o.matrix_basis.copy() for o in spear_objects}
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
def guard(t=0):
 limb('upperarm_r','lowerarm_r',(-.37,-.31,1.43+t),(-.55,-.04,.95))
 limb('upperarm_l','lowerarm_l',(.29,-.34,1.12+t),(.53,-.10,1.13))
 aim('hand_r',(0,-.03,.09));aim('hand_l',(0,-.03,.09))
def pose(t):
 reset()
 if clip=='idle':
  p=stand.positions(80+round(t*240));p0=stand.positions(80)
  v=(p['Neck']-p['Hips']).normalized();v0=(p0['Neck']-p0['Hips']).normalized()
  delta=(v-v0)*.65
  # Keep the end near the start for a gentle loop; only CMU deltas drive sway.
  envelope=math.sin(math.pi*t)**2
  turn('spine_03','X',delta.y*envelope);turn('spine_03','Y',delta.x*envelope)
  guard(.007*math.sin(2*math.pi*t))
 elif clip=='move':
  p=walk.positions(40+round(t*120))
  for side,prefix in [('l','Left'),('r','Right')]:
   upper=p[prefix+'Leg']-p[prefix+'UpLeg'];lower=p[prefix+'Foot']-p[prefix+'Leg']
   # Captured sagittal gait, spread for the shield-bearing stance.
   upper.x=.14 if side=='l' else -.14
   aim('thigh_'+side,upper);aim('calf_'+side,lower)
   aim('foot_'+side,(0,-.12,-.04));aim('ball_'+side,(0,-1,0))
  floor=min(rig.pose.bones['foot_'+s].head.z for s in ['l','r'])
  rig.location.z=base_loc.z+.09-floor
  guard(.08+.013*math.cos(4*math.pi*t));turn('spine_03','Z',.045*math.sin(2*math.pi*t))
 elif clip=='attack':
  # Raise outside the right shoulder, then drive forward above the shield rim.
  # Right hand stays on the shaft; the rear shaft stays outside the torso.
  strength=[0,.05,.22,.72,1,1,.68,.25,.05,0][min(9,round(t*9))]
  raised=[0,.35,.90,1,1,1,1,.85,.30,0][min(9,round(t*9))]
  rig.location=base_loc+Vector((.12*strength,-.16*strength,-.12*strength))
  turn('spine_03','X',.20*strength);turn('spine_03','Y',.15*strength)
  # Counter root travel in the ankle targets: soles remain on the disc.
  limb('thigh_l','calf_l',(.32+.08*strength,.035-.18*strength,.082+.12*strength),(.42,-.50,.48))
  limb('thigh_r','calf_r',(-.32-.12*strength,-.075+.16*strength,.082+.12*strength),(-.40,-.20,.48))
  limb('upperarm_r','lowerarm_r',(-.37+.10*strength,-.31-.10*raised-.05*strength,1.43+.28*raised),tuple(Vector((-.55,-.04,.95)).lerp(Vector((-.65,.05,1.48)),raised)))
  limb('upperarm_l','lowerarm_l',(.29,-.34-.10*strength,1.12+.10*strength),(.55,-.12,1.20))
  aim('hand_r',(0,-.03,.09));hand_spear(Vector((.98,.17,.12))*raised+Vector((0,0,1))*(1-raised))
 elif clip=='hit':
  a=[0,1,.5,0][min(3,round(t*3))]
  turn('spine_03','X',-.30*a);turn('neck_01','X',-.18*a);turn('head','Z',.09*a)
  guard(.06*a);turn('lowerarm_l','Z',.25*a);rig.location.y=.045*a
 elif clip=='death':
  # Side collapse onto the disc, folded legs; held terminal key pose.
  a=min(1,t/.72);smooth=a*a*(3-2*a)
  rig.location=base_loc+Vector((-.27*smooth,.02*smooth,-.585*smooth))
  turn('pelvis','Y',1.25*smooth);turn('spine_03','Y',.22*smooth);turn('head','X',.28*smooth)
  for side,sgn in [('l',1),('r',-1)]:
   # Begin in the same wide guard, then fold the ankles into the fall.
   x=sgn*.32*(1-smooth)+(-.22+sgn*.12)*smooth
   y=(.035 if side=='l' else -.075)*(1-smooth)+(.02+sgn*.12)*smooth
   limb('thigh_'+side,'calf_'+side,(x,y,.75*smooth+.082*(1-smooth)),(-.45,-.30,.55))
  limb('upperarm_r','lowerarm_r',(-.37+.48*smooth,-.31+.10*smooth,1.43-.58*smooth),tuple(Vector((-.55,-.04,.95)).lerp(Vector((-.35,-.32,.85)),smooth)))
  limb('upperarm_l','lowerarm_l',(.29+.14*smooth,-.34+.08*smooth,1.12-.30*smooth),(.4,-.15,.9))
  aim('hand_r',(0,-.03,.09));hand_spear(Vector((0,0,1)))
 bpy.context.view_layer.update()
 if clip in ['attack','death']:
  for side in ['l','r']:
   aim('foot_'+side,(0,-.12,-.045));aim('ball_'+side,(0,-1,0))
 if clip=='attack':
  # Slide the grip down the shaft during extension; preserve a continuous grip
  # while keeping both ends of the long spear inside the fixed atlas cell.
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  direction=(shaft.matrix_world @ Vector(pts[-1].co[:3])-shaft.matrix_world @ Vector(pts[0].co[:3])).normalized()
  for o in spear_objects:
   mat=o.matrix_world.copy();mat.translation+=direction*(float(os.environ.get('ANIM_ATTACK_SLIDE','.25'))*raised+.29*max(0,min(1,(raised-.4)/.4)));o.matrix_world=mat
  bpy.context.view_layer.update()
 if clip=='death':
  # Let go before the body rolls across the shaft. The rigid weapon lands across
  # the front edge of the stone; it is never hidden or teleported out of frame.
  release=max(0,min(1,(t-.04)/.44))
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
(out/'clip.json').write_text(json.dumps({'source_master_sha256':sc['source_master_sha256'],'clip':clip,'frames':samples,'fps':fps,'cloth_baked':pc.is_baked,'mocap':{'idle':'CMU 77_02 standing, frames 80-320, torso deltas','move':'CMU 02_01 walk, frames 40-160, sagittal legs'}.get(clip,'hand keyed')},indent=2))
print('CLIP_READY',clip, samples)

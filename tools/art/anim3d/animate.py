"""Bake Blender-retargeted CC0 motion and the weapon-specific attack."""
import bpy,os,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).parent/'infantry'))
sys.path.insert(0,str(Path(__file__).parent/'units/spearman'))
from retarget import prepare, apply_matrices, contact_ik
from contact import sole_points
from motion import attack_channels, source_phase, EquipmentResponse
import collapse
root=Path(os.environ['ANIM_ROOT']);M=root/'masters/spearman-3d-v2';A=root/'assets'
CLIPS={'idle':(8,4),'move':(8,6),'attack':(10,14),'hit':(4,12),'death':(10,4)}

clip=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'idle'
out=M/'clips'/clip;out.mkdir(parents=True,exist_ok=True)
if os.environ.get('MOTION_DIAGNOSTIC')!='1':(out/'clip.json').unlink(missing_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=3;rig=bpy.data.objects['Spearman • MPFB game_engine'];neutral=json.loads(rig['neutral_pose'])
base_loc=rig.location.copy()
neutral_world={p.name:p.matrix.copy() for p in rig.pose.bones}
guard_hand=Vector(rig.get('guard_hand_target',(-.37,-.31,1.34)))
spear_objects=[o for o in sc.objects if any(o.name.startswith(n) for n in ['Ash dory shaft','Spear bronze ferrule','Leaf spearhead','Iron spear butt'])]
spear_neutral={o.name:o.matrix_basis.copy() for o in spear_objects}
spear_world={o.name:o.matrix_world.copy() for o in spear_objects}
for o in spear_objects:o.rotation_mode='QUATERNION'

shield=bpy.data.objects.get('Aspis control');shield_neutral=shield.matrix_basis.copy() if shield else None
if shield:shield.rotation_mode='QUATERNION'
cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip']
cloth.show_viewport=False
if clip=='attack':
 # Retain the shoulder attachment; free more of the lower wool to lag the
 # torso's acceleration, then damp it like a heavy cloak instead of a flag.
 # Hit keeps the original pins/settings: loosening them raised a cloak corner
 # behind the shoulder at its four-frame recovery in the merged candidate.
 cloak=bpy.data.objects['Cloak • simulated wool'];pins=cloak.vertex_groups['Shoulder pins']
 for v in cloak.data.vertices:
  for g in v.groups:
   if g.group==pins.index and g.weight<.99:pins.add([v.index],g.weight*.65,'REPLACE')
 cloth.settings.bending_stiffness=.8
 cloth.settings.air_damping=2
if clip=='death':
 # Release the lower cape's silhouette pins so it drapes during the collapse.
 # Keep the shoulder attachment; no visibility or scale trick hides the cloth.
 cloak=bpy.data.objects['Cloak • simulated wool'];pins=cloak.vertex_groups['Shoulder pins']
 for v in cloak.data.vertices:
  for g in v.groups:
   if g.group==pins.index and g.weight<.99:pins.add([v.index],g.weight*.15,'REPLACE')
 cloth.settings.bending_stiffness=.4
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.02))
 ground=bpy.context.object;ground.name='Death ground cloth collider';ground.scale=(6,6,.04)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 ground.hide_render=True;ground.modifiers.new('Ground cloth collision','COLLISION')
 cloth.settings.quality=8
 cloth.collision_settings.collision_quality=6
for p in rig.pose.bones:p.rotation_mode='QUATERNION'
def reset():
 rig.location=base_loc
 if clip=='death':rig.rotation_mode='QUATERNION';rig.rotation_quaternion=(1,0,0,0)
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
 if clip=='death':
  if t>0:collapse.apply(t,rig,neutral_world,limb,turn)
 elif clip in ['idle','move','hit']:
  motion=retarget_frames[active_frame-1]
  rig.location=base_loc+motion['root']
  apply_matrices(rig,motion['matrices'])
  if clip=='move':
   # Constant stance registration, separate from the measured slip correction.
   # Native IK retains the donor's world foot rotations.
   from motion import walk_offsets
   contact_ik(rig,walk_offsets(motion['foot_corrections']))
  bpy.context.view_layer.update()
 elif clip=='attack':
  # Raise outside the right shoulder, then drive forward above the shield rim.
  # Right hand stays on the shaft; the rear shaft stays outside the torso.
  strength,raised=attack_channels(t)
  rig.location=base_loc+Vector((.12*strength,-.16*strength,-.12*strength))
  turn('spine_03','X',.20*strength);turn('spine_03','Y',.15*strength)
  # Counter root travel in the ankle targets: soles remain on the disc.
  limb('thigh_l','calf_l',(.21+.10*strength,.15-.18*strength,.082+.12*strength),(.42,-.50,.48))
  limb('thigh_r','calf_r',(-.39-.05*strength,-.075+.16*strength,.082+.12*strength),(-.40,-.20,.48))
  pole=Vector((-.48,-.12,1.08)).lerp(Vector((-.65,.05,1.48)),raised)
  # Arm keys are authored about the round-12 pelvis; guard_shift is where the planted guard moved it (zero otherwise).
  gs=Vector(rig.get('guard_shift',(0,0,0)))
  limb('upperarm_r','lowerarm_r',Vector((guard_hand.x+(-.13-guard_hand.x)*strength,guard_hand.y+(-.41-guard_hand.y)*raised-.05*strength,guard_hand.z+(1.71-guard_hand.z)*raised))+gs,pole+gs)
  limb('upperarm_l','lowerarm_l',Vector((.29,-.34-.10*strength,1.12+.10*strength))+gs,Vector((.53,-.10,1.13)).lerp(Vector((.55,-.12,1.20)),strength)+gs)
  aim('hand_r',(0,-.03,.09));hand_spear(Vector((.98,.17,.12))*raised+Vector((0,0,1))*(1-raised))
 bpy.context.view_layer.update()
 if clip=='attack':
  # The authored attack has planted foot controls, rebased on the new idle.
  # These are attack keys, not a correction to any retargeted clip.
  for side in ['l','r']:
   for name in ['foot_'+side,'ball_'+side]:
    bone=rig.pose.bones[name];matrix=neutral_world[name].copy();matrix.translation=bone.head
    bone.matrix=matrix;bpy.context.view_layer.update()
 if clip=='attack':
  # Slide the grip down the shaft during extension; preserve a continuous grip
  # while keeping both ends of the long spear inside the fixed atlas cell.
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  direction=(shaft.matrix_world @ Vector(pts[-1].co[:3])-shaft.matrix_world @ Vector(pts[0].co[:3])).normalized()
  for o in spear_objects:
   mat=o.matrix_world.copy();mat.translation+=direction*.25*raised;o.matrix_world=mat
  bpy.context.view_layer.update()
 if clip=='death':
  # Let go before the body rolls across the shaft. The rigid weapon lands across
  # the front edge of the stone; it is never hidden or teleported out of frame.
  release=max(0,min(1,t/.56))
  if release>0:
   for o in spear_objects:o.matrix_world=spear_world[o.name]
   bpy.context.view_layer.update()
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  start=shaft.matrix_world @ Vector(pts[0].co[:3]);end=shaft.matrix_world @ Vector(pts[-1].co[:3])
  center=(start+end)*.5;direction=(end-start).normalized()
  # Clear the shield in depth while upright, tip forward, then settle inward
  # only after the shaft is horizontal and below the shield's lower edge.
  depth=min(1,release/.20);depth=depth*depth*(3-2*depth)
  tilt=max(0,min(1,(release-.02)/.73));tilt=tilt*tilt*(3-2*tilt)
  rotation=Quaternion().slerp(direction.rotation_difference(Vector((.995,-.10,.0)).normalized()),tilt)
  target=center.lerp(Vector((-.30,-.60,.075)),release)
  # Keep a real pixel margin while the retimed fall crosses the horizontal
  # weapon pose; the endpoint and held landing stay exactly where authored.
  target.x+=.02*math.sin(math.pi*release)
  target.x+=.12*tilt
  target.y=center.y+(-.82-center.y)*depth
  if release>.80:target.y=-.82+.22*(release-.80)/.20
  drop=min(1,release/.75)
  target.z=center.z*(1-drop)+.075*drop
  # Over the stone the low end rides its top; past the front edge it drops to the ground.
  off=max(0,min(1,(-.40-target.y)/.20));rest_z=.13-.055*off*off*(3-2*off)
  if release>0:target.z=max(target.z,rest_z+(end-start).length*.5*abs((rotation @ direction).z))
  transform=Matrix.Translation(target) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-center)
  for o in spear_objects:o.matrix_world=transform @ o.matrix_world
  for digit in ['index','middle','ring','pinky']:
   for k in range(1,4):
    p=rig.pose.bones[f'{digit}_{k:02d}_r'];p.rotation_quaternion=p.rotation_quaternion.slerp(Quaternion(),min(1,release*4))
  bpy.context.view_layer.update()
count,fps=CLIPS[clip];samples=[25+round(i*24/fps) for i in range(count)]
# Give cloth one second to settle before any output sample.
end=25+round(count*24/fps) if clip in ['idle','move'] else samples[-1]
sc.frame_start=1;sc.frame_end=end;sc.render.fps=24
phases=[max(0,(f-25))/(count*24/fps) if clip in ['idle','move']
        else max(0,min(1,(f-25)/max(1,end-25))) for f in range(1,end+1)]
if clip=='death':retarget_frames,motion_source=None,{'provider':'Authored weighted collapse (Fable B, accepted 2026-11-24)','keys':len(collapse.KEYS)}
elif clip=='attack':retarget_frames,motion_source=None,{'provider':'Original weapon-specific hand keys, rebased on Quaternius idle reference'}
else:retarget_frames,motion_source=prepare(rig,root,clip,phases)
response=EquipmentResponse(rig,shield,clip)
# A single complete source cycle, sampled before its duplicate endpoint.

for f in range(1,end+1):
 if f==1 or f%8==0:print('POSE',clip,f,'/',end,flush=True)
 sc.frame_set(f)
 t=max(0,min(1,(f-25)/max(1,end-25)))
 # Loop clips sample before the duplicate final phase.
 if clip in ['idle','move']:t=max(0,(f-25))/(count*24/fps)
 active_frame=f
 equipment_phase=t
 pose(equipment_phase)
 # Resolve the actual finished sandal underside against the real stone top.
 # Small foot-bone translations preserve the keyed action and live skinning;
 # airborne feet are unchanged. The previous root heuristic allowed buried soles.
 if sc.get('infantry_refinement',0)>=6:
  base=bpy.data.objects['Stationary cream stone']
  floor=max((base.matrix_world @ v.co).z for v in base.data.vertices)
  if clip=='move':
   flags=motion_source['contact']['planted'].get(str(f),{})
   # Each planted sole meets the stone. The root follows the planted foot that
   # needs the lowest pelvis; any other foot (second support, or a swing toe
   # that would dip into the stone) is raised by leg IK with its source roll.
   # No rigid ankle translation and no error left on the second support.
   need={side:floor+.001-min(v.z for v in sole_points(side)) for side in ['l','r']}
   planted=[side for side in ['l','r'] if flags.get(side)]
   if planted:
    correction=min(need[side] for side in planted)
    assert abs(correction)<.04, f'Large contact height correction: {correction}'
    rig.location.z+=correction
    bpy.context.view_layer.update()
    raise_by={side:Vector((0,0,need[side]-correction if side in planted else max(0,need[side]-correction))) for side in ['l','r']}
    raise_by={side:v for side,v in raise_by.items() if v.z>1e-5}
    if raise_by:
     motion_source['max_ik_sole_raise_m']=max(motion_source.get('max_ik_sole_raise_m',0),max(v.z for v in raise_by.values()))
     contact_ik(rig,raise_by)
  base_inverse=base.matrix_world.inverted()
  base_radius=max((v.co.x*v.co.x+v.co.y*v.co.y)**.5 for v in base.data.vertices)-.015
  if clip=='death':
   # The open clip falls onto a flat floor. Fit its root to the actual raised
   # stone and thick armour, preserving every retargeted joint rotation.
   released={o:o.matrix_world.copy() for o in spear_objects}
   dg=bpy.context.evaluated_depsgraph_get();lift=0;culprit=''
   feet_zones=[(rig.matrix_world @ rig.pose.bones[n+side].head,r) for side in 'lr' for n,r in [('ball_',.17),('foot_',.12)]]
   for ob in (sc.objects if t>0 else []):
    if ob.type!='MESH' or ob.hide_render or ob==base or ob.name.startswith(('Cloak •','Aspis','Sunburst','Convex bronze aspis','Shield','Leather shield','Leather sandal','Sandal strap')):continue
    if ob in spear_objects:continue
    # Only rig-carried body/clothes/armour; released equipment has its own solve.
    parent=ob.parent
    if parent!=rig:continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh()
    for v in me.vertices:
     w=ob.matrix_world @ v.co;local=base_inverse @ w
     # Feet are solved separately below (sole, straps and their own pitch).
     if any((w-c).length<r for c,r in feet_zones):continue
     plane=floor+.005 if local.x*local.x+local.y*local.y<base_radius**2 else .012
     if plane-w.z>lift:lift=plane-w.z;culprit=ob.name+' at '+str([round(c,2) for c in w])+' groups '+str([ob.vertex_groups[g.group].name for g in ob.data.vertices[v.index].groups if g.weight>.3] if len(ob.data.vertices)==len(me.vertices) else '')
    ev.to_mesh_clear()
   if f in samples:print('DEATH_LIFT',f,round(lift,3),culprit if lift>0 else '',flush=True)
   if lift>0:
    rig.location.z+=lift;bpy.context.view_layer.update()
    for ob,matrix in released.items():ob.matrix_world=matrix
    bpy.context.view_layer.update()
   motion_source['max_armoured_fall_root_lift_m']=max(motion_source.get('max_armoured_fall_root_lift_m',0),lift)
  for side in ['l','r']:
   sole=bpy.data.objects['Leather sandal sole '+side]
   planted=clip=='move' and flags.get(side,False)
   if planted:continue
   lift=0
   foot_points=sole_points(side)
   if clip=='death':
    dg=bpy.context.evaluated_depsgraph_get()
    for ob in sc.objects:
     if ob.name.startswith('Sandal strap '+side):
      ev=ob.evaluated_get(dg);me=ev.to_mesh();foot_points+=[ob.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
   for point in foot_points:
    local=base_inverse @ point
    reach=base_radius+(.15 if clip=='death' else 0)
    plane=floor+.001 if local.x*local.x+local.y*local.y<reach**2 else .006
    lift=max(lift,plane-point.z)
   if abs(lift)>1e-8:
    if clip=='move':assert abs(lift)<.04,('Large sole contact translation',side,lift)
    motion_source['max_sole_translation_m']=max(motion_source.get('max_sole_translation_m',0),abs(lift))
    motion_source['max_sole_lift_m']=max(motion_source.get('max_sole_lift_m',0),lift)
    if clip=='move':
     contact_ik(rig,{side:Vector((0,0,lift))})
    else:
     foot=rig.pose.bones['foot_'+side];mat=foot.matrix.copy()
     mat.translation+=rig.matrix_world.to_3x3().inverted() @ Vector((0,0,lift))
     foot.matrix=mat;bpy.context.view_layer.update()
 if clip!='death':
  butt=next(o for o in spear_objects if o.name.startswith('Iron spear butt'))
  ev=butt.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  lowest=min((butt.matrix_world @ v.co).z for v in mesh.vertices);ev.to_mesh_clear()
  if lowest<.107:
   shaft=bpy.data.objects['Ash dory shaft'];points=shaft.data.splines[0].points
   direction=(shaft.matrix_world @ Vector(points[-1].co[:3])-shaft.matrix_world @ Vector(points[0].co[:3])).normalized()
   if direction.z>.25:
    shift=direction*((.107-lowest)/direction.z)
    for ob in spear_objects:
     matrix=ob.matrix_world.copy();matrix.translation+=shift;ob.matrix_world=matrix
    bpy.context.view_layer.update()
 response.key(f,equipment_phase)
 rig.keyframe_insert(data_path='location',frame=f)
 if clip=='death':rig.keyframe_insert(data_path='rotation_quaternion',frame=f)
 for o in spear_objects:
  o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='rotation_quaternion',frame=f)
 if shield:
  shield.keyframe_insert(data_path='location',frame=f);shield.keyframe_insert(data_path='rotation_quaternion',frame=f)
 for p in rig.pose.bones:
  p.rotation_mode='QUATERNION';p.keyframe_insert(data_path='location',frame=f);p.keyframe_insert(data_path='rotation_quaternion',frame=f);p.keyframe_insert(data_path='scale',frame=f)
motion_source['equipment_response']=response.report()
sc['motion_source']=json.dumps(motion_source)
sc['sample_frames']=json.dumps(samples)
if os.environ.get('MOTION_DIAGNOSTIC') == '1':
 sc['source_master_sha256']=hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest()
 sc['clip']=clip;sc['cloth_baked']=False
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'-diagnostic.blend')))
 print('MOTION_DIAGNOSTIC_READY',clip,flush=True)
 raise SystemExit(0)
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
sc['spear_release_start']=0 if clip=='death' else -1
sc['clip']=clip;sc['sample_frames']=json.dumps(samples);sc['cloth_baked']=True
sc.frame_set(samples[0]);bpy.ops.wm.save_as_mainfile(filepath=str(out/(clip+'.blend')))
(out/'clip.json').write_text(json.dumps({'source_master_sha256':sc['source_master_sha256'],'clip':clip,'frames':samples,'fps':fps,'cloth_baked':pc.is_baked,'motion_source':motion_source},indent=2))
print('CLIP_READY',clip, samples)

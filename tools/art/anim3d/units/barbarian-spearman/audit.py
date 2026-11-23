"""Saved-scene audit. This does not claim a full collision solver or art approval."""
import bpy,os,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';source=M/'barbarian-spearman.blend';expected=hashlib.sha256(source.read_bytes()).hexdigest();rows=[]
(M/'audit.json').unlink(missing_ok=True)
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));s=bpy.context.scene;r=bpy.data.objects['Barbarian skeleton'];b=bpy.data.objects['Stationary cream base'];base=b.matrix_world.copy()
 assert s['source_sha256']==expected,'Clip from stale source'
 assert len(r.data.bones)==53 and len(bpy.data.objects['MPFB barbarian anatomy'].data.vertices)==19158
 assert bpy.data.objects['MPFB barbarian anatomy'].data.shape_keys is None,'Macro shape keys override fitting'
 shaft=bpy.data.objects['Ash spear shaft'];points=np.array([list(v.co) for v in shaft.data.vertices]);center=points.mean(axis=0);_,axes=np.linalg.eigh(np.cov((points-center).T));axis=axes[:,-1];along=(points-center)@axis;ends=[Vector(center+axis*t) for t in [along.min(),along.max()]]
 max_grip=0;max_contact_error=0
 for frame in json.loads(s['sample_frames']):
  s.frame_set(frame);assert b.matrix_world==base
  for ob in s.objects:
   assert all(abs(v)>.0001 for v in ob.scale),f'Unsafe zero scale: {ob.name}'
  if clip=='move':
   soles=[]
   for side in ['r','l']:
    motion=json.loads((M/'clips/move-motion.json').read_text())
    expected_rotation=Quaternion(motion['target_foot_rotations'][frame-1][side])
    assert abs(expected_rotation.dot(r.pose.bones['foot_'+side].matrix.to_quaternion()))> .99999,'Foot rotation changed after retarget'
    shoe=bpy.data.objects['Lasted leather shoe '+side]
    sole=min((shoe.matrix_world@v.co).z for v in shoe.data.vertices);soles.append(sole)
    assert sole>=.086,f'{clip}/{frame}: foot below stone {sole}'
   error=abs(min(soles)-.092);max_contact_error=max(max_contact_error,error)
   assert error<.006,f'{clip}/{frame}: neither sole planted {error}'
  if clip!='death':
   assert bpy.data.objects['Spear grip control'].parent==r,'Detached weapon'
   a,bp=[shaft.matrix_world@v for v in ends];p=r.matrix_world@r.pose.bones['hand_r'].head;axis=bp-a;t=max(0,min(1,(p-a).dot(axis)/axis.length_squared));distance=(p-(a+t*axis)).length;max_grip=max(max_grip,distance);assert distance<.065,f'{clip}/{frame}: lost grip {distance}'
  else:
   dg=bpy.context.evaluated_depsgraph_get()
   for name in ['MPFB barbarian anatomy','Lasted leather shoe r','Lasted leather shoe l']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh();lowest=min((ob.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();assert lowest>=.09,f'{clip}/{frame}: below base {name}: {lowest}'
 if clip!='attack':
  assert s.get('motion_provider')=='Quaternius Universal Animation Library Standard'
 if clip=='move':
  provenance=json.loads((M/'clips/move-motion.json').read_text());speed=provenance['contact']['virtual_ground_m_per_sample']
  max_slide=0
  for side,start,end in [('l',2,5),('r',6,9)]:
   points=[]
   for frame in range(start,end+1):
    s.frame_set(frame);points.append(r.matrix_world@r.pose.bones['ball_'+side].head)
   for a,z in zip(points,points[1:]):max_slide=max(max_slide,abs((z-a).y-speed),abs((z-a).x))
  assert max_slide<.006,f'Virtual-ground stance sliding {max_slide}'
  rows.append(f'move: source-derived toe stance speed {speed:.6f}m/sample, maximum horizontal slide {max_slide:.6f}m; foot rotations retained')
 rows.append(clip+f': source hash, MPFB topology/rig, stationary base, safe scales, grip/ground passed; max grip distance {max_grip:.4f}m; max move sole error {max_contact_error:.5f}m')
result={'passed':True,'source_sha256':expected,'clip_sha256':{p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in (M/'clips').glob('*.blend')},'checks':rows,'limits':'No full cloth/skin/equipment collision solver. All five clips require visual review.'}
(M/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

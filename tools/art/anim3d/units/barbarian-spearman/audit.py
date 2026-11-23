"""Saved-scene audit. This does not claim a full collision solver or art approval."""
import bpy,os,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';source=M/'barbarian-spearman.blend';expected=hashlib.sha256(source.read_bytes()).hexdigest();rows=[]
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));s=bpy.context.scene;r=bpy.data.objects['Barbarian skeleton'];b=bpy.data.objects['Stationary cream base'];base=b.matrix_world.copy()
 assert s['source_sha256']==expected,'Clip from stale source'
 assert len(r.data.bones)>=50 and len(bpy.data.objects['MPFB barbarian anatomy'].data.vertices)>10000
 shaft=bpy.data.objects['Ash spear shaft'];points=np.array([list(v.co) for v in shaft.data.vertices]);center=points.mean(axis=0);_,axes=np.linalg.eigh(np.cov((points-center).T));axis=axes[:,-1];along=(points-center)@axis;ends=[Vector(center+axis*t) for t in [along.min(),along.max()]]
 max_grip=0
 for frame in json.loads(s['sample_frames']):
  s.frame_set(frame);assert b.matrix_world==base
  for ob in s.objects:
   assert all(abs(v)>.0001 for v in ob.scale),f'Unsafe zero scale: {ob.name}'
  if clip!='death':
   assert bpy.data.objects['Spear grip control'].parent==r,'Detached weapon'
   a,bp=[shaft.matrix_world@v for v in ends];p=r.matrix_world@r.pose.bones['hand_r'].head;axis=bp-a;t=max(0,min(1,(p-a).dot(axis)/axis.length_squared));distance=(p-(a+t*axis)).length;max_grip=max(max_grip,distance);assert distance<.065,f'{clip}/{frame}: lost grip {distance}'
  else:
   dg=bpy.context.evaluated_depsgraph_get()
   for name in ['MPFB barbarian anatomy','Lasted leather shoe r','Lasted leather shoe l']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh();lowest=min((ob.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();assert lowest>=.09,f'{clip}/{frame}: below base {name}: {lowest}'
 rows.append(clip+f': source hash, MPFB topology/rig, stationary base, safe scales, grip/ground passed; max grip distance {max_grip:.4f}m')
result={'passed':True,'checks':rows,'limits':'No full cloth/skin/equipment collision solver. All five clips require visual review.'}
(M/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

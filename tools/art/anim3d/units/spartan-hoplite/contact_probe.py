"""Report the surface under a suspicious shield detail without changing the scene."""
import bpy,os,json
from pathlib import Path
from mathutils import Vector
M=Path(os.environ['ANIM_MASTER']);bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'));sc=bpy.context.scene;cam=sc.camera;rot=cam.matrix_world.to_quaternion();dg=bpy.context.evaluated_depsgraph_get();records=[]
for x in range(139,148,2):
 for y in range(113,128,2):
  start=cam.location+rot@Vector(((x/256-.5)*cam.data.ortho_scale,(.5-y/256)*cam.data.ortho_scale,0))
  hit,loc,normal,index,obj,matrix=sc.ray_cast(dg,start,rot@Vector((0,0,-1)))
  if hit:records.append({'pixel':[x,y],'surface':obj.name})
(M/'shield-contact-probe.json').write_text(json.dumps(records,indent=2));print('SHIELD_CONTACT_SURFACES',sorted(set(r['surface'] for r in records)))

expected={(139,121),(141,121),(141,123),(143,123),(143,125)}
blocked=[r for r in records if tuple(r['pixel']) in expected and r['surface']!='Convex bronze aspis']
assert not blocked, 'Fingertip still visible through shield: '+str(blocked)

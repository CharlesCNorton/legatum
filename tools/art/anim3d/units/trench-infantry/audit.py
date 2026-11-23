"""Structural/rig audit; report contact metrics without claiming visual approval."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/trench-infantry';records={}
master_hash=hashlib.sha256((M/'trench-infantry.blend').read_bytes()).hexdigest()
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 meta=json.loads((M/'clips'/f'{clip}.json').read_text());assert meta['source_sha256']==master_hash
 if clip!='attack':assert meta['motion']['license']=='CC0-1.0'
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
 rig=bpy.data.objects['RIG-Trench infantry MPFB'];assert len(rig.data.bones)==53
 assert len(bpy.data.objects['GEO-MPFB trench-infantry anatomy'].data.vertices)>10000
 base=bpy.data.objects['GEO-stationary cream base'];initial=base.matrix_world.copy();poses=[]
 for f in range(1,n+1):
  sc.frame_set(f);assert base.matrix_world==initial
  assert all(min(abs(v) for v in o.scale)>.001 for o in sc.objects),'Zero scale object'
  feet={}
  for side in ('l','r'):
   o=bpy.data.objects['GEO-boot sole '+side];direction=o.matrix_world.to_3x3() @ Vector((0,-1,0));direction.z=0;direction.normalize()
   angle=math.degrees(math.acos(max(-1,min(1,direction.dot(Vector((0,-1,0)))))))
   feet[side]={'forward_degrees':round(angle,2),'center':list(o.matrix_world.translation),'ankle':list(rig.matrix_world @ rig.pose.bones['foot_'+side].head)}
  poses.append(feet)
 contact_errors=[]
 if clip=='move':
  assert max(p[s]['forward_degrees'] for p in poses for s in ('l','r'))<15,'Feet are not pointing along travel'
  contact=meta['motion']['contact'];speed=contact['virtual_forward_speed_m_s']
  for i in range(n-1):
   a=24+round(i/n*48);b=24+round((i+1)/n*48)
   for side in ('l','r'):
    flags=contact['planted']
    if all(flags.get(str(k+1),{}).get(side,False) for k in range(a,b+1)):
     delta=Vector(poses[i+1][side]['ankle'])-Vector(poses[i][side]['ankle']);delta.y-=speed*(b-a)/24;delta.z=0
     contact_errors.append({'from':i+1,'to':i+2,'side':side,'slip_m':delta.length})
  assert contact_errors,'No planted intervals inspected'
  assert max(x['slip_m'] for x in contact_errors)<.015,contact_errors
 if clip=='hit':
  sc.frame_set(1);start={p.name:p.matrix.copy() for p in rig.pose.bones};start_root=rig.location.copy();sc.frame_set(n)
  assert (rig.location-start_root).length<.00001
  assert max(abs(p.matrix[i][j]-start[p.name][i][j]) for p in rig.pose.bones for i in range(4) for j in range(4))<.0001,'Hit did not recover'
 records[clip]={'frames':n,'feet':poses,'motion':meta['motion'],'planted_interval_errors':contact_errors}
(M/'audit.json').write_text(json.dumps({'structural_checks':'pass','visual_approval':False,'clips':records},indent=2))
print('Structural audit passed; full contact/contour judgment requires feet and clip images.')

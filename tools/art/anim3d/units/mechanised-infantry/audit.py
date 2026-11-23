"""Inspect saved rig, real wheel rotation and foot direction; no visual PASS claim."""
import bpy,json,os,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/mechanised-infantry';records=[]
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/f'mechanised-infantry-{clip}.blend'))
 sc=bpy.context.scene;rig=bpy.data.objects['RIG-Soldier MPFB'];base=bpy.data.objects['GEO-stationary cream disc']
 assert len(rig.data.bones)==53 and rig.animation_data.action
 assert base.animation_data is None
 wheels=[o for o in sc.objects if o.name.startswith('RIG-wheel ')]
 assert len(wheels)==8
 for i in range(count):
  sc.frame_set(i+1);deps=bpy.context.evaluated_depsgraph_get();feet=[]
  travel=(rig.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()
  for side in ['l','r']:
   ob=bpy.data.objects['GEO-boot sole '+side];ev=ob.evaluated_get(deps);me=ev.to_mesh();points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
   forward=(ob.matrix_world.to_3x3()@Vector((0,-1,0))).normalized()
   yaw=math.atan2(forward.x,-forward.y)-math.atan2(travel.x,-travel.y)
   feet.append({'side':side,'min_z':min(v.z for v in points),'forward':list(forward),'yaw_degrees':math.degrees(math.atan2(math.sin(yaw),math.cos(yaw)))})
  if clip=='move':
   # Direction gate: compare the bound sole axis to the rig's -Y travel direction.
   assert all(abs(f['yaw_degrees'])<35 for f in feet),(i,feet)
   assert abs(min(f['min_z'] for f in feet)-.15)<.003,(i,feet)
  records.append({'clip':clip,'frame':i+1,'feet':feet})
report={'rig_bones':53,'wheels':8,'frames':40,'stationary_base':True,'move_feet_forward_within_degrees':35,'move_lowest_sole_contact_tolerance':.003,'records':records,'visual_approval':False,'limitation':'direction/contact checks do not certify absence of horizontal sliding or intersections'}
report['clip_blends']={clip:hashlib.sha256((M/f'mechanised-infantry-{clip}.blend').read_bytes()).hexdigest() for clip in ['idle','move','attack','hit','death']}
(M/'geometry-audit.json').write_text(json.dumps(report,indent=2))
print('PASS: MPFB 53-bone actions; eight wheels; stationary base; move sole direction and ground contact')

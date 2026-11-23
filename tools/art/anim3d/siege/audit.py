"""Audit saved 3D geometry, stationary base, rolling ratios and settled death."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon';records={}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Gunner MPFB game_engine'];gun=bpy.data.objects['Gun travel and recoil'];base=bpy.data.objects['Stationary cream base'];body=bpy.data.objects['MPFB artillery gunner anatomy']
 assert len(body.data.vertices)>10000 and len(rig.data.bones)==53,'MPFB topology/rig missing'
 assert json.loads(sc['sample_frames'])==list(range(1,count+1));base_matrix=base.matrix_world.copy();samples=[];held_values=None
 for i in range(count):
  sc.frame_set(i+1);assert base.matrix_world==base_matrix,'Base moved'
  for o in sc.objects:
   if o.type=='MESH' and not o.hide_render:assert min(abs(s) for s in o.scale)>.001,('Degenerate renderable mesh',o.name)
  if clip in ['move','attack','hit']:
   travel=.48*(2*math.pi/12)*(i/count) if clip=='move' else 0
   rest=gun['rest_location'];yaw=gun['rest_yaw'];localtravel=(gun.location.x-rest[0])*math.cos(yaw)+(gun.location.y-rest[1])*math.sin(yaw)
   expected=(travel+localtravel)/.48
   for name in ['Wheel -1','Wheel 1']:assert abs(bpy.data.objects[name].rotation_euler.y-expected)<1e-5,'Wheel slip'
  if clip=='death' and i>=count-2:
   values=[v for o in sc.objects for row in o.matrix_world for v in row]
   values.extend(v for o in sc.objects if o.type=='ARMATURE' for p in o.pose.bones for row in p.matrix for v in row)
   if held_values is not None:
    delta=max(abs(a-b) for a,b in zip(values,held_values));assert delta<1e-6,('Held geometry differs',delta);records['held_matrix_max_delta']=delta
   held_values=values
  samples.append({'rig':list(rig.location),'gun':list(gun.location),'wheel':list(bpy.data.objects['Wheel -1'].rotation_euler)})
 if clip=='death':
  assert samples[-1]==samples[-2],'Death is not held'
  # Check actual evaluated mesh surfaces of the fallen crew and tipped gun.
  dg=bpy.context.evaluated_depsgraph_get();grounds={}
  for root in [rig,gun,bpy.data.objects['Rammer hand control']]:
   lows=[]
   for o in sc.objects:
    if o.type!='MESH' or o.hide_render or not(root==o or o in root.children_recursive):continue
    ev=o.evaluated_get(dg);me=ev.to_mesh();lows.extend((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   grounds[root.name]=min(lows);assert .09<=min(lows)<=.15,('Terminal object not grounded',root.name,min(lows))
  records['terminal_ground']=grounds
 records[clip]=samples
(R/'review/3d-v2/field-cannon-audit.json').write_text(json.dumps(records,indent=2))
print('PASS: MPFB topology, 53-bone rig, 40 samples, stationary base, rolling ratio, nondegenerate effects, held grounded death')

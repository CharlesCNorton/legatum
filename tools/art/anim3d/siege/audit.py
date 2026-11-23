"""Audit saved 3D geometry, stationary base, rolling ratios and settled death."""
import bpy,os,json,math,runpy
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon';records={}
# Reopening the saved unprojected surface must not add another sampling level.
# This matters when iterating pigment from this checkpoint instead of rebuilding.
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon-surface.blend'))
before={o.name:len(o.data.vertices) for o in bpy.context.scene.objects if o.type=='MESH'}
runpy.run_path(str(Path(__file__).with_name('surface.py')))['finish_surfaces']()
after={o.name:len(o.data.vertices) for o in bpy.context.scene.objects if o.type=='MESH'}
assert before==after,'Finished-surface replay changed topology'
records['surface_replay_topology_unchanged']=True
# Guard the original projection defect: the UVs must land on the finished,
# posed surfaces, not an unsmoothed cage that changes again during rendering.
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon.blend'))
scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
projection=json.loads((M/'projection.json').read_text())
sx0,sy0,sx1,sy1=projection['registration']['source_bbox']
rx0,ry0,rx1,ry1=projection['registration']['reference_bbox']
errors={}
for name in ['MPFB artillery gunner anatomy','Tailored blue coat body','White wool breeches','Black felt shako','Hollow bronze barrel','Stationary cream base']:
 obj=bpy.data.objects[name]
 assert all(mod.type=='ARMATURE' or not mod.show_render for mod in obj.modifiers),('Unfinished projection surface',name)
 ev=obj.evaluated_get(deps);mesh=ev.to_mesh();uv=mesh.uv_layers['Painting projection']
 worst=0
 for loop in mesh.loops:
  point=world_to_camera_view(scene,scene.camera,ev.matrix_world @ mesh.vertices[loop.vertex_index].co)
  tex=uv.data[loop.index].uv
  reference=Vector((rx0+(tex.x*1254-sx0)*(rx1-rx0)/(sx1-sx0),ry0+((1-tex.y)*1254-sy0)*(ry1-ry0)/(sy1-sy0)))
  worst=max(worst,(Vector((point.x*256,(1-point.y)*256))-reference).length)
 ev.to_mesh_clear();errors[name]=worst
 assert worst<.01,('Finished surface UV registration drift',name,worst)
records['finished_projection_error_px']=errors
fit=json.loads((M/'registration.json').read_text())['wheel_surfaces']
records['wheel_reference_bounds']={}
for name,reference in fit.items():
 wheel=bpy.data.objects[name]
 assert wheel.parent.name.startswith('Wheel mounting '),'Fitted wheel mount missing'
 tyre=next(o for o in wheel.children if o.name.startswith('Flat wrought iron tyre'))
 points=[world_to_camera_view(scene,scene.camera,tyre.matrix_world @ v.co) for v in tyre.data.vertices]
 actual=[min(p.x for p in points)*256,(1-max(p.y for p in points))*256,max(p.x for p in points)*256,(1-min(p.y for p in points))*256]
 error=max(abs(a-b) for a,b in zip(actual,reference['target_bounds_px']))
 assert error<1,('Rendered tyre differs from fitted reference bounds',name,actual,error)
 records['wheel_reference_bounds'][name]={'actual':actual,'max_error_px':error}

for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Gunner MPFB game_engine'];gun=bpy.data.objects['Gun travel and recoil'];base=bpy.data.objects['Stationary cream base'];body=bpy.data.objects['MPFB artillery gunner anatomy']
 assert abs(sc['wheel_radius']-.525)<1e-6 and abs(gun['wheel_radius']-.525)<1e-6,'Wheel radius metadata drifted from geometry'
 for wheel_name in ['Wheel -1','Wheel 1']:
  wheel=bpy.data.objects[wheel_name]
  tyre=next(o for o in wheel.children if o.name.startswith('Flat wrought iron tyre'))
  local=wheel.matrix_world.inverted() @ tyre.matrix_world
  radius=max(((local @ v.co).x**2+(local @ v.co).z**2)**.5 for v in tyre.data.vertices)
  assert abs(radius-sc['wheel_radius'])<1e-5,('Rolling radius differs from real tyre geometry',wheel_name,radius)
 for belt in [o for o in sc.objects if o.name.startswith('Ivory cross belt')]:
  assert belt.parent.name=='Tailored blue coat body','Crossbelt detached from coat'
  assert belt.get('finished_thickness',0)>=.005 or any(m.type=='SOLIDIFY' and m.thickness>=.005 for m in belt.modifiers),'Crossbelt lacks physical thickness'
  if belt.get('finished_thickness',0):
   edges={}
   for face in belt.data.polygons:
    for edge in face.edge_keys:edges[edge]=edges.get(edge,0)+1
   assert edges and all(n==2 for n in edges.values()),'Finished crossbelt is not a closed solid'
 assert len(body.data.vertices)>10000 and len(rig.data.bones)==53,'MPFB topology/rig missing'
 assert json.loads(sc['sample_frames'])==list(range(1,count+1));base_matrix=base.matrix_world.copy();samples=[];held_values=None
 for i in range(count):
  sc.frame_set(i+1);assert base.matrix_world==base_matrix,'Base moved'
  for o in sc.objects:
   if o.type=='MESH' and not o.hide_render:assert min(abs(s) for s in o.scale)>.001,('Degenerate renderable mesh',o.name)
  if clip in ['idle','move']:
   actual=rig.matrix_world @ rig.pose.bones['hand_l'].tail
   target=bpy.data.objects['Barrel elevation'].matrix_world @ Vector(rig['barrel_contact_local'])
   assert (actual-target).length<.002,('Resting palm lost barrel contact',(actual-target).length)
  if clip=='move':
   target=bpy.data.objects['Barrel elevation'].matrix_world @ Vector(rig['push_contact_local'])
   actual=rig.matrix_world @ rig.pose.bones['hand_r'].tail
   assert (actual-target).length<.002,('Pushing right palm lost barrel contact',(actual-target).length)
   for side,offset in [('l',0),('r',.5)]:
    cycle=(i/count+offset)%1
    lift=0 if cycle<.5 else .045*math.sin(2*math.pi*(cycle-.5))
    sole=bpy.data.objects['Boot sole '+side]
    bottom=min((sole.matrix_world @ v.co).z for v in sole.data.vertices)
    assert abs(bottom-(.098+lift))<.002,('Pushing boot lost authored ground contact',side,i,bottom,lift)
  if clip in ['move','attack','hit']:
   travel=.525*(2*math.pi/12)*(i/count) if clip=='move' else 0
   rest=gun['rest_location'];yaw=gun['rest_yaw'];localtravel=(gun.location.x-rest[0])*math.cos(yaw)+(gun.location.y-rest[1])*math.sin(yaw)
   expected=(travel+localtravel)/.525
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
    ev=o.evaluated_get(dg);me=ev.to_mesh();lows.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
   grounds[root.name]=min(lows);assert .09<=min(lows)<=.15,('Terminal object not grounded',root.name,min(lows))
  records['terminal_ground']=grounds
 records[clip]=samples
(R/'review/3d-v2/field-cannon-audit.json').write_text(json.dumps(records,indent=2))
print('PASS: MPFB topology, 53-bone rig, 40 samples, idle/move palm contact, two-handed push and planted boots, closed thick belts, stationary base, rolling ratio, nondegenerate effects, held grounded death')

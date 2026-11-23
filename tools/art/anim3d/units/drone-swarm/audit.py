"""Geometry and mechanical motion evidence, independent of image acceptance."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/drone-swarm'
bpy.ops.wm.open_mainfile(filepath=str(M/'drone-swarm.blend'))
assert bpy.context.scene.camera is not None
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)>=150
assert all(min(o.dimensions)>.002 for o in meshes),'near-zero-thickness geometry'
assert all('PaintingProjection' in o.data.uv_layers for o in meshes)
assert len([o for o in bpy.data.objects if o.name.startswith('RIG-') and ' rotor' in o.name])==6
assert len(list((M/'textures/baked').glob('*-AO.png')))==3
assert len(list((M/'textures/baked').glob('*-curvature.png')))==3
reports=[]
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene;base=bpy.data.objects['GEO-stationary cream base'];sc.frame_set(1);base_matrix=base.matrix_world.copy();roots=[bpy.data.objects['RIG-drone'+str(i)] for i in (1,2,3)];matrices=[]
 for f in range(1,n+1):
  sc.frame_set(f);assert base.matrix_world==base_matrix,'moving base';assert all(min(o.scale)>.001 for o in sc.objects if o.type=='MESH');matrices.append([tuple(v for row in o.matrix_world for v in row) for o in roots])
 assert len(set(tuple(m[0]) for m in matrices))>1,clip+' static'
 if clip in ('idle','move'):
  sc.frame_set(1);first=[o.matrix_world.copy() for o in roots];sc.frame_set(n+1)
  assert all(max(abs(a-b) for row1,row2 in zip(mat,o.matrix_world) for a,b in zip(row1,row2))<1e-5 for mat,o in zip(first,roots)),'loop root seam'
 if clip=='death':
  assert matrices[-1]==matrices[-2],'unsettled wreck';top=max((base.matrix_world@Vector(v)).z for v in base.bound_box);contacts=[]
  for root in roots:
   points=[];deps=bpy.context.evaluated_depsgraph_get()
   for ob in root.children_recursive:
    if ob.type!='MESH':continue
    ev=ob.evaluated_get(deps);me=ev.to_mesh();points.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
   lowest=min(points,key=lambda p:p.z);gap=lowest.z-top;assert -.005<=gap<=.025,(root.name,gap);contacts.append({'root':root.name,'minimum_z_gap':gap,'lowest_point_in_disc':(lowest.xy-base.location.xy).length<1.78})
  assert all(c['lowest_point_in_disc'] for c in contacts),'wreck contact outside pedestal'
  reports.append({'death_contacts':contacts})
 reports.append({'clip':clip,'frames':n,'stationary_base':True,'rig_moves':True})
report={'status':'pass','mesh_count':len(meshes),'solid_geometry':True,'projection_on_meshes':True,'baked_maps':6,'clips':reports,'art_approval':False};(M/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

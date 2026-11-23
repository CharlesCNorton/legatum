"""Geometry, clip continuity, physical wreck contact and source provenance."""
import bpy,bmesh,os,json,hashlib
from mathutils import Vector
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-fighter';records={}
bakes=json.loads((M/'textures/baked/manifest.json').read_text());assert len(bakes)==3
for record in bakes:assert all(Path(record[key]).exists() for key in ('AO','curvature'))
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene
 assert sc['master_sha256']==hashlib.sha256((M/'stealth-fighter.blend').read_bytes()).hexdigest()
 meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)>=20
 assert all(min(abs(v) for v in o.scale)>.001 for o in meshes)
 for name in ('GEO-fuselage','GEO-near wing','GEO-far wing'):
  o=bpy.data.objects[name];assert min(o.dimensions)>.04 and len(o.data.vertices)>100
  assert 'RestPainting' in o.data.uv_layers and o.get('surface_finished') and not o.modifiers
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),name+' not closed';assert abs(bm.calc_volume())>.001;bm.free()
 for side in ('near','far'):
  hinge=bpy.data.objects['RIG-'+side+' elevon'];surface=bpy.data.objects['GEO-'+side+' stabilizer']
  assert surface.parent==hinge
  center=surface.matrix_world @ (sum((v.co for v in surface.data.vertices),Vector())/len(surface.data.vertices))
  assert (center-hinge.matrix_world.translation).length<.12,'control pivot misses surface'
 base=bpy.data.objects['GEO-stationary cream base'];root=bpy.data.objects['RIG-airframe'];poses=[];bases=[];stands=[]
 support=bpy.data.objects['GEO-curved stationary stone support']
 assert 'RestPainting' not in base.data.uv_layers
 assert 'StonePigment' in base.data.uv_layers
 for f in range(1,n+1):
  sc.frame_set(f);poses.append(tuple(v for row in root.matrix_world for v in row));bases.append(tuple(v for row in base.matrix_world for v in row))
  assert not support.hide_render,'stone support disappears'
  stands.append(tuple(v for row in support.matrix_world for v in row))
 assert len(set(bases))==1 and len(set(poses))>1
 if clip in ('idle','move'):
  sc.frame_set(n+1);end=tuple(v for row in root.matrix_world for v in row);assert max(abs(a-b) for a,b in zip(poses[0],end))<1e-6
 if clip=='death':
  assert poses[-1]==poses[-2]
  assert len(set(stands))>1 and stands[-1]==stands[-2], 'support must topple then hold'
  top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box);deps=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['GEO-fuselage'].evaluated_get(deps);me=o.to_mesh();points=[]
  for v in me.vertices:
   pt=o.matrix_world@v.co
   if (pt.xy-base.location.xy).length<1.02:points.append(pt.z)
  o.to_mesh_clear();assert points and abs(min(points)-top)<.001
 records[clip]={'frames':n,'meshes':len(meshes),'closed_airframe':True,'stationary_base':True,'real_motion':True,'solid_support_visible':True}
(M/'audit.json').write_text(json.dumps(records,indent=2));print('AUDIT PASS',json.dumps(records))

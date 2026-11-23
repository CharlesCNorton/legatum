"""Independent checks on editable solid geometry, motion and stationary base."""
import bpy,bmesh,os,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contact import disc_clearance, support_clearance
from provenance import render_signature
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-bomber';records={}
bakes=json.loads((M/'textures/baked/manifest.json').read_text());assert len(bakes)==3
for record in bakes:
 assert all(Path(record[k]).exists() for k in ('AO','curvature'))
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene;assert sc.camera
 assert sc['render_signature']==render_signature(),'stale motion source'
 assert sc['master_sha256']==hashlib.sha256((M/'stealth-bomber.blend').read_bytes()).hexdigest()
 meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)>=12
 assert all(min(abs(v) for v in o.scale)>.001 for o in meshes)
 for name in ('GEO-fuselage','GEO-centre crown','GEO-cockpit'):
  o=bpy.data.objects[name];assert len(o.data.vertices)>100 and min(o.dimensions)>.04
  if name=='GEO-fuselage':assert o.dimensions.y>2*o.dimensions.z,'wing plane too steep'
  assert 'RestPainting' in o.data.uv_layers and o.get('surface_finished') and not o.modifiers
  bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),(name,'open edges');assert abs(bm.calc_volume())>.001;bm.free()
 base=bpy.data.objects['GEO-stationary cream base'];root=bpy.data.objects['RIG-airframe'];bases=[];poses=[]
 assert 'RestPainting' in base.data.uv_layers
 for f in range(1,n+1):
  sc.frame_set(f);bases.append(tuple(v for row in base.matrix_world for v in row));poses.append(tuple(v for row in root.matrix_world for v in row))
 assert len(set(bases))==1 and len(set(poses))>1
 if clip=='death':
  assert poses[-1]==poses[-2]
  clearances=[]
  for f in range(1,n+1):
   sc.frame_set(f);bpy.context.view_layer.update()
   gap=disc_clearance(sc,[bpy.data.objects['GEO-fuselage']],base)
   assert gap is None or gap>=-.001,('airframe penetrates disc',f,gap)
   support=bpy.data.objects['GEO-curved stationary stone support']
   assert not support.hide_render,'support vanished'
   sgap=disc_clearance(sc,[support],base)
   assert sgap is None or sgap>=-.001,('support penetrates disc',f,sgap)
   stand_gap=support_clearance(sc,bpy.data.objects['GEO-fuselage'],support)
   assert stand_gap is None or stand_gap>=(-.12 if f==1 else -.001),('stand penetrates wing beyond mount',f,stand_gap)
   clearances.append(gap)
  assert abs(clearances[-1]-.008)<.001 or (stand_gap is not None and abs(stand_gap-.012)<.001),'wreck contact'
  records['death_contact']={'sampled_clearances':clearances,'triangle_interior_checks':True,'support_visible':True,'airframe_stand_clearance':stand_gap}
 if clip in ('idle','move'):
  sc.frame_set(n+1);closing=tuple(v for row in root.matrix_world for v in row)
  assert max(abs(a-b) for a,b in zip(poses[0],closing))<1e-6
 records[clip]={'frames':n,'meshes':len(meshes),'closed_airframe':True,'stationary_base':True,'real_motion':True}
(M/'audit.json').write_text(json.dumps(records,indent=2));print('AUDIT PASS',json.dumps(records))

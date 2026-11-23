"""Geometry/rig checks, with honest limits rather than a collision-free claim."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/scout';V=R/'review/3d-v2';source=hashlib.sha256((M/'scout.blend').read_bytes()).hexdigest();results={}
projection=json.loads((M/'projection.json').read_text())
assert any(p['object']=='GEO-Scout MPFB anatomy' for p in projection),'Skin projection was skipped'
assert all(p['source_box_256'] is None for p in projection),'Per-region texture stretching returned'
bpy.ops.wm.open_mainfile(filepath=str(M/'scout.blend'))
for record in projection:
 o=bpy.data.objects[record['object']]
 assert o.data.uv_layers.get('PaintingUV') and o.data.attributes.get('PaintingFacing')
 assert o.data.materials[0].node_tree.nodes.get('Camera-only pigment')
assert bpy.data.objects['GEO-Scout MPFB anatomy'].data.shape_keys is None,'Macro mix not frozen'
def matrices(sc):
 return {o.name:[v for row in o.matrix_world for v in row] for o in sc.objects} | {p.name:[v for row in p.matrix for v in row] for p in bpy.data.objects['Scout MPFB game_engine'].pose.bones}
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/(clip+'.blend')));sc=bpy.context.scene;r=bpy.data.objects['Scout MPFB game_engine'];assert sc['source_sha256']==source;assert len(r.data.bones)==53
 body=bpy.data.objects['GEO-Scout MPFB anatomy'];assert len(body.data.vertices)>10000,'Expected MPFB topology'
 assert any(m.type=='ARMATURE' for m in body.modifiers);assert sc.camera and sc.camera.data.type=='ORTHO'
 base=bpy.data.objects['GEO-Stationary cream stone'];start=None;sampledata=[]
 for frame in json.loads(sc['samples']):
  sc.frame_set(frame);bpy.context.view_layer.update();current=[v for row in base.matrix_world for v in row]
  if start is None:start=current
  assert current==start,'Moving base'
  for o in sc.objects:assert min(abs(v) for v in o.scale)>.001,'Degenerate object '+o.name
  hand=r.matrix_world@r.pose.bones['hand_r'].head;staff=bpy.data.objects['GEO-Forked walking staff'];ev=staff.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();dist=min((staff.matrix_world@v.co-hand).length for v in me.vertices);ev.to_mesh_clear();assert dist<.12,f'Detached staff {clip}/{frame}: {dist}'
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();minz=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();assert .095<=minz<=.105,f'Body clearance {clip}/{frame}: {minz}';sampledata.append({'frame':frame,'hand_to_staff_surface':round(dist,4),'body_min_z':round(minz,4)})
 if clip in ['idle','move']:
  sc.frame_set(1);a=matrices(sc);sc.frame_set(sc.frame_end);b=matrices(sc);assert max(abs(x-y) for k in a for x,y in zip(a[k],b[k]))<1e-5,'Loop endpoint mismatch'
 if clip=='death':
  sc.frame_set(9);a=matrices(sc);sc.frame_set(10);b=matrices(sc);assert max(abs(x-y) for k in a for x,y in zip(a[k],b[k]))<1e-5,'Death geometry does not hold'
 results[clip]=sampledata
report={'status':'PASS','bones':53,'stationary_base':True,'body_floor_clearance':True,'nondegenerate_objects':True,'grip_threshold':.12,'samples':results,'limits':'Body minimum Z clears the base; this is not a full cloth/equipment collision solver. Art and detailed sandal contact require visual review.'};(V/'scout-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

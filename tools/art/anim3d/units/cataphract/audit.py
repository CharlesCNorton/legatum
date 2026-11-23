"""Validate true anatomical geometry, rig ownership and invariant base/camera."""
import bpy,os,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reins import endpoints, RINGS, SIDES
from contacts import foot_indices, evaluated
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cataphract';Q=R/'review/3d-v2'
def upstream_images(socket,seen=None):
 seen=set() if seen is None else seen
 images=[]
 for link in socket.links:
  node=link.from_node
  if node in seen:continue
  seen.add(node)
  if node.type=='TEX_IMAGE' and node.image:images.append(node.image.name)
  for input_socket in node.inputs:images.extend(upstream_images(input_socket,seen))
 return images
sha=hashlib.sha256((M/'cataphract.blend').read_bytes()).hexdigest();report={}
for clip,count in {'idle':8,'move':8,'attack':10,'hit':4,'death':10}.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
 assert sc['source_master_sha256']==sha,clip+': stale master'
 horse=bpy.data.objects['Horse'];rider=bpy.data.objects['Rider MPFB CC0 anatomy'];base=bpy.data.objects['Stationary cream stone']
 assert len(rider.data.vertices)>10000 and len(horse.data.vertices)>1000
 assert rider.data.shape_keys is None,'Active macro shapes can override fitting'
 for ob in sc.objects:
  if ob.type!='MESH':continue
  assert ob.get('finished_before_projection'),ob.name
  assert all(m.type=='ARMATURE' for m in ob.modifiers),ob.name
  if ob==base:continue
  assert ob.data.uv_layers.get('Painting projection'),ob.name
  for mat in ob.data.materials:
   if not mat or not mat.use_nodes:continue
   assert mat.node_tree.nodes.get('Painted illumination'),(ob.name,mat.name)
   assert not any(name.startswith('projection.png') for name in upstream_images(mat.node_tree.nodes['Principled BSDF'].inputs['Alpha'])),(ob.name,'Painting must not cut geometry; native eye alpha is allowed')
 assert any(m.type=='ARMATURE' for m in rider.modifiers) and any(m.type=='ARMATURE' for m in horse.modifiers)
 assert len(bpy.data.objects['Rider MPFB game_engine'].data.bones)==53
 bm=base.matrix_world.copy();cam=sc.camera.matrix_world.copy()
 max_rein_gap=0
 foot_vertices=foot_indices(horse);minimum_sole=1e9
 assert sc['rider_source_action']=={'hit':'Hit_Chest','death':'Death01'}.get(clip,'Sitting_Idle_Loop')
 for frame in range(1,count+1):
  sc.frame_set(frame);bpy.context.view_layer.update()
  assert base.matrix_world==bm and sc.camera.matrix_world==cam
  for ob in sc.objects:assert min(abs(x) for x in ob.scale)>1e-6,ob.name
  points=evaluated(horse)
  minimum_sole=min(minimum_sole,min(points[i].z for ids in foot_vertices.values() for i in ids))
  for ob in sc.objects:
   if 'rein_anchors' not in ob:continue
   expected=endpoints(ob);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   for offset,target in [(0,expected[0]),((RINGS-1)*SIDES,expected[1])]:
    actual=sum((ev.matrix_world@me.vertices[offset+k].co for k in range(SIDES)),Vector())/SIDES
    max_rein_gap=max(max_rein_gap,(actual-target).length)
   ev.to_mesh_clear()
 assert max_rein_gap<.0001,(clip,'detached rein',max_rein_gap)
 assert minimum_sole>=.105,(clip,'hoof below support plane',minimum_sole)
 loop_error=0
 if clip in ['idle','move']:
  arm=bpy.data.objects['AnimalArmature'];sc.frame_set(1);bpy.context.view_layer.update();first={p.name:p.matrix.copy() for p in arm.pose.bones}
  sc.frame_set(count+1);bpy.context.view_layer.update()
  loop_error=max(abs(p.matrix[i][j]-first[p.name][i][j]) for p in arm.pose.bones for i in range(4) for j in range(4))
  assert loop_error<.003,(clip,'loop endpoint',loop_error)
 report[clip]={'loop_matrix_error':loop_error,'minimum_sole_z':minimum_sole,'max_rein_endpoint_gap_m':max_rein_gap,'rider_source_action':sc['rider_source_action'],'frames':count,'rider_vertices':len(rider.data.vertices),'horse_vertices':len(horse.data.vertices),'rider_bones':53,'stationary_base_camera':True}
(Q/'cataphract-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('CATAPHRACT_AUDIT_PASS',report)

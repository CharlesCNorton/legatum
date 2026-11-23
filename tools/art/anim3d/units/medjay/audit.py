"""Structural audit on the saved geometry and every sampled animation frame."""
import sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(M/'medjay.blend'));rig=bpy.data.objects['Medjay MPFB game_engine'];body=bpy.data.objects['Medjay MPFB anatomical body'];assert len(body.data.vertices)>10000 and len(rig.data.bones)==53;assert any(m.type=='ARMATURE' for m in body.modifiers);assert body.data.uv_layers.get('Rest painting projection');assert len(json.loads((M/'surface-manifest.json').read_text()))==8
assert body.data.shape_keys is None,'Morphs must be frozen before UV calibration'
assert bpy.context.scene['finished_surface_projection']
rest_matrices={p.name:p.matrix.copy() for p in rig.pose.bones}
uv_error=0.0
for obj in bpy.context.scene.objects:
 if obj.type!='MESH' or not obj.data.uv_layers.get('Rest painting projection'):continue
 assert obj.active_material.node_tree.nodes.get('Camera painted pigment'),obj.name
 mask_states=[(m,m.show_viewport) for m in obj.modifiers if m.type=='MASK']
 for m,_ in mask_states:m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),obj.name
 uv=obj.data.uv_layers['Rest painting projection']
 for loop in obj.data.loops:
  q=world_to_camera_view(bpy.context.scene,bpy.context.scene.camera,ev.matrix_world@me.vertices[loop.vertex_index].co)
  uv_error=max(uv_error,(Vector((q.x,q.y))-uv.data[loop.index].uv).length*256)
 ev.to_mesh_clear()
 for m,show in mask_states:m.show_viewport=show
assert uv_error<.05,('Finished surface projection drift',uv_error)
vertex_count=len(body.data.vertices);records={};base_matrix=None
for clip,(count,_,_) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/f'medjay-{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Medjay MPFB game_engine'];base=bpy.data.objects['Stationary warm cream stone'];assert base.parent is None
 if clip in {'attack','hit','death'}:
  sc.frame_set(1);bpy.context.view_layer.update()
  error=max(abs(p.matrix[i][j]-rest_matrices[p.name][i][j]) for p in rig.pose.bones for i in range(4) for j in range(4))
  assert error<.0001,(clip,'Clip entry pose pop',error)
 matrices=[];bounds=[]
 for i in range(count):
  sc.frame_set(i+1);bpy.context.view_layer.update();matrix=[list(row) for row in base.matrix_world]
  if base_matrix is None:base_matrix=matrix
  assert matrix==base_matrix,'Stone moves'
  for o in sc.objects:
   assert all(abs(v)>.001 for v in o.scale),(clip,i,o.name,'near-zero scale')
   if o.type in ['MESH','CURVE'] and o.name!='Stationary warm cream stone':
    assert o.parent is not None or o.name=='Medjay anatomical eyes',(clip,o.name,'unattached equipment')
  matrices.append([list(row) for row in rig.matrix_world]);coords=[]
  for o in sc.objects:
   if o.type not in ['MESH','CURVE']:continue
   for v in o.bound_box:
    q=world_to_camera_view(sc,sc.camera,o.matrix_world@Vector(v));coords.append((q.x,q.y))
  bounds.append([min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords),max(y for x,y in coords)])
 records[clip]={'samples':count,'stationary_base':True,'sane_scales':True,'equipment_attached':True,'bounds_conservative':bounds}
(M/'audit.json').write_text(json.dumps({'status':'pass','body_vertices':vertex_count,'bones':53,'finished_projection_max_error_px':uv_error,'combat_entry_matches_rest':True,'clips':records,'limitations':'Structural audit does not prove absence of all skin/cloth/weapon intersections. Review silhouettes and held death.'},indent=2));log('Structural audit passed: genuine weighted anatomy, 53 bones, fixed projection UVs, stationary base and sane scales across every clip sample.')

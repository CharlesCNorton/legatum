"""Audit actual saved geometry and skeletal masters, separately from the art verdict."""
import bpy,os,json,math,hashlib
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';V=R/'review/3d-v2';result={};base_matrix=None
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
 assert sc['source_master_sha256']==hashlib.sha256((M/'cuirassier.blend').read_bytes()).hexdigest()
 human=bpy.data.objects['Rider MPFB CC0 anatomy'];horse=bpy.data.objects['Horse'];assert len(human.data.vertices)>10000;assert len(horse.data.vertices)>300
 assert len(bpy.data.objects['Rider MPFB game_engine'].data.bones)==53
 assert human.data.shape_keys is None,'Unfrozen MPFB macro keys override fitting'
 assert bpy.data.objects['GEO-pistol steel barrel'].type=='MESH','Unfinished curve kit'
 assert all(bpy.data.objects[n].data.uv_layers.get('Painting projection') for n in ['Horse','GEO-ridged steel cuirass','GEO-perforated visor','GEO-pistol steel barrel'])
 assert any(m.type=='ARMATURE' for m in human.modifiers);assert any(m.type=='ARMATURE' for m in horse.modifiers)
 assert bpy.data.objects['GEO-pistol steel barrel'].parent_bone=='hand_r'
 minima=[];body_clearance=[]
 torso_groups={g.index for g in horse.vertex_groups if g.name in ('Torso','Torso2')}
 torso_indices=[v.index for v in horse.data.vertices if sum(g.weight for g in v.groups if g.group in torso_groups)>.5]
 for frame in json.loads(sc['sample_frames']):
  sc.frame_set(frame);bpy.context.view_layer.update();base=bpy.data.objects['Stationary cream stone'];matrix=[v for row in base.matrix_world for v in row]
  if base_matrix is None:base_matrix=matrix
  assert max(abs(a-b) for a,b in zip(matrix,base_matrix))<1e-6,'Moving base'
  for obj in sc.objects:
   assert all(math.isfinite(v) for v in obj.location)
   assert min(abs(v) for v in obj.scale)>.00001,f'Degenerate scale: {obj.name}'
  assert sc.camera.animation_data is None,'Projection camera must remain fixed'
  ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=[(ev.matrix_world @ v.co).z for v in me.vertices];minima.append(min(z));body_clearance.append(min(z[i] for i in torso_indices)-min(z));ev.to_mesh_clear()
 assert min(minima)>=.102,f'{clip}: horse penetrates stone top'
 if clip=='death':assert body_clearance[-1]<.20,'Terminal torso remains propped above support'
 result[clip]={'torso_to_lowest_surface':body_clearance,'rider_source_action':sc['rider_source_action'],'sample_frames':len(json.loads(sc['sample_frames'])),'horse_min_z':minima,'human_vertices':len(human.data.vertices),'horse_vertices':len(horse.data.vertices),'stationary_base':True,'weapon_bone_parent':'hand_r'}
(V/'cuirassier-audit.json').write_text(json.dumps({'passed':True,'clips':result,'limits':'No complete tack/skin collision solver; contact heights are measurements, not art approval.'},indent=2));print('AUDIT PASS',json.dumps(result))

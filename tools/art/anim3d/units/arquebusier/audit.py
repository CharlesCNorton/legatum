"""Audit editable geometry and sampled clip matrices, independently of raster packing."""
import bpy,json,os,math,hashlib
from pathlib import Path
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/arquebusier';V=R/'review/3d-v2'
(V/'arquebusier-geometry-audit.json').unlink(missing_ok=True)
counts={'idle':8,'move':8,'attack':10,'hit':4,'death':10};results={}
for clip,n in counts.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Arquebusier MPFB'];body=bpy.data.objects['GEO-MPFB arquebusier anatomy'];base=bpy.data.objects['GEO-stationary cream base'];assert len(rig.data.bones)==53;assert len(body.data.vertices)==19158;assert not body.data.shape_keys;assert sc.camera
 assert json.loads((M/'clips'/f'{clip}.json').read_text())['source_sha256']==hashlib.sha256((M/'arquebusier.blend').read_bytes()).hexdigest(),'Stale clip'
 assert any(n.name.startswith('Camera painted illumination') for ma in bpy.data.materials if ma.use_nodes for n in ma.node_tree.nodes),'Missing painted pigment'
 for image in bpy.data.images:
  if image.source=='FILE':assert image.packed_file or Path(bpy.path.abspath(image.filepath)).exists(),image.name
 snapshots=[];bm=None;minscale=1.;max_ankle_gap=0.
 for frame in range(1,n+1):
  sc.frame_set(frame);bpy.context.view_layer.update();snap=[]
  now=[x for row in base.matrix_world for x in row]
  if bm is None:bm=now
  assert max(abs(a-b) for a,b in zip(now,bm))<1e-7,'Base moved'
  for o in sc.objects:
   assert all(math.isfinite(x) for row in o.matrix_world for x in row),(clip,frame,o.name)
   if o.type=='MESH':
    assert min(abs(v) for v in o.scale)>.001,(clip,frame,o.name,'degenerate scale');minscale=min(minscale,min(abs(v) for v in o.scale))
   if o.type in ('MESH','ARMATURE','EMPTY'):snap.extend(x for row in o.matrix_world for x in row)
  for b in rig.pose.bones:snap.extend(x for row in b.matrix for x in row)
  # Bone-only contact metrics missed detached shoes in the first mocap trial.
  # Measure the actual closed footwear against its anatomical ankle every frame.
  for side in ('l','r'):
   ankle=rig.matrix_world @ rig.pose.bones['foot_'+side].head
   shoe=bpy.data.objects['GEO-latchet shoe '+side]
   gap=min((shoe.matrix_world @ v.co-ankle).length for v in shoe.data.vertices)
   max_ankle_gap=max(max_ankle_gap,gap)
   assert gap<.08,(clip,frame,side,'footwear separated from ankle',gap)
  snapshots.append(snap)
 assert any(max(abs(a-b) for a,b in zip(snapshots[0],s))>1e-5 for s in snapshots[1:]),clip+' static'
 if clip=='death':assert max(abs(a-b) for a,b in zip(snapshots[-2],snapshots[-1]))<1e-5,'Death geometry not held'
 if clip in ('idle','move'):
  sc.frame_set(n+1);bpy.context.view_layer.update()
  # Exact underlying action endpoint equals first pose; the repeated endpoint is not shipped.
  for b in rig.pose.bones:
   end=b.matrix.copy();sc.frame_set(1);bpy.context.view_layer.update();assert max(abs(end[i][j]-b.matrix[i][j]) for i in range(4) for j in range(4))<1e-5,(clip,b.name,'loop seam');sc.frame_set(n+1);bpy.context.view_layer.update()
 results[clip]={'frames':n,'bones':len(rig.data.bones),'body_vertices':len(body.data.vertices),'minimum_mesh_scale':minscale,'stationary_base':True,'motion':True,'max_ankle_to_shoe_surface_m':max_ankle_gap}
report={'status':'pass','clips':results,'limits':'Does not establish hand/weapon or garment collision clearance; visual review remains required.'};(V/'arquebusier-geometry-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

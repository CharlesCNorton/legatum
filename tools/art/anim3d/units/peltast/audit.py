"""Audit full 3D sources, frozen base, finite transforms, loops and terminal hold."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
records={};sourcehash=hashlib.sha256((M/'peltast.blend').read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(M/'peltast.blend'))
sc=bpy.context.scene;bpy.context.view_layer.update()
rest={p.name:p.matrix.copy() for p in bpy.data.objects['RIG-Peltast'].pose.bones}
uv_error=0.;finished_count=0
for obj in sc.objects:
 if obj.type!='MESH' or not obj.get('finished_projection_surface'):continue
 uv=obj.data.uv_layers.get('Painting rest UV')
 if uv is None:continue
 finished_count+=1
 assert not obj.modifiers,'Rigid geometry changed after UV calibration'
 for loop in obj.data.loops:
  q=world_to_camera_view(sc,sc.camera,obj.matrix_world@obj.data.vertices[loop.vertex_index].co)
  uv_error=max(uv_error,256*(Vector((q.x,q.y))-uv.data[loop.index].uv).length)
assert finished_count>100 and uv_error<.01,(finished_count,uv_error)
for clip,(n,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast'];base=bpy.data.objects['GEO-Stationary cream base'];refbase=base.matrix_world.copy();assert sc['source_sha256']==sourcehash
 assert len(rig.data.bones)==53;assert len(bpy.data.objects['GEO-MPFB peltast anatomy'].data.vertices)>10000
 assert bpy.data.objects['GEO-Dished wicker crescent pelta'].get('finished_projection_surface'), 'Project the finished thick shield'
 assert any('Painting rest UV' in o.data.uv_layers for o in sc.objects if o.type=='MESH')
 matrices=[]
 if clip=='attack':
  for frame in (1,n):
   sc.frame_set(frame);bpy.context.view_layer.update()
   error=max(abs(p.matrix[r][c]-rest[p.name][r][c]) for p in rig.pose.bones for r in range(4) for c in range(4))
   assert error<1e-5,('Attack guard endpoint pop',frame,error)
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==refbase,'Moving base'
  for o in sc.objects:
   assert all(math.isfinite(v) for row in o.matrix_world for v in row),'Nonfinite transform'
   if o.type in ('MESH','CURVE'):assert min(abs(v) for v in o.matrix_world.to_scale())>.0001,'Near-zero geometry scale'
  matrices.append([list(row) for row in rig.matrix_world]+[[v for row in p.matrix for v in row] for p in rig.pose.bones])
 if loop:
  sc.frame_set(n+1);bpy.context.view_layer.update();wrap=[list(row) for row in rig.matrix_world]+[[v for row in p.matrix for v in row] for p in rig.pose.bones];error=max(abs(a-b) for aa,bb in zip(matrices[0],wrap) for a,b in zip(aa,bb));assert error<1e-5,(clip,'loop mismatch',error)
 else:error=None
 if clip=='death':assert max(abs(a-b) for aa,bb in zip(matrices[-1],matrices[-2]) for a,b in zip(aa,bb))<1e-5,'Death not settled'
 records[clip]={'frames':n,'base':'stationary','loop_max_matrix_error':error,'true_3d':True}
(R/'peltast-audit.json').write_text(json.dumps({'passed':True,'finished_projected_meshes':finished_count,'rigid_uv_max_error_px':uv_error,'clips':records,'scope':'Finished rigid projection, attack endpoint continuity, topology, transform sanity, stationary base, loop and terminal skeletal pose. Visual intersections remain review work.'},indent=2));print('AUDIT PASS',json.dumps(records),'UV error',uv_error)

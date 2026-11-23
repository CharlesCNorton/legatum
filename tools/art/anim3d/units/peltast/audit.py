"""Audit full 3D sources, frozen base, finite transforms, loops and terminal hold."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
records={};sourcehash=hashlib.sha256((M/'peltast.blend').read_bytes()).hexdigest()
for clip,(n,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast'];base=bpy.data.objects['GEO-Stationary cream base'];refbase=base.matrix_world.copy();assert sc['source_sha256']==sourcehash
 assert len(rig.data.bones)==53;assert len(bpy.data.objects['GEO-MPFB peltast anatomy'].data.vertices)>10000
 assert bpy.data.objects['GEO-Dished wicker crescent pelta'].modifiers.get('Real thickness')
 assert any('Painting rest UV' in o.data.uv_layers for o in sc.objects if o.type=='MESH')
 matrices=[]
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
(R/'peltast-audit.json').write_text(json.dumps({'passed':True,'clips':records,'scope':'Topology, full volumetric meshes, transform sanity, stationary base, loop and terminal skeletal pose. Visual intersections remain review work.'},indent=2));print('AUDIT PASS',json.dumps(records))

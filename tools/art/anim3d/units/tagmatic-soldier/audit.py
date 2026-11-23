"""Evaluate sampled meshes, record clip bounds and stationary-base evidence."""
import bpy, json, os, math, sys
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier';records={}
for clip in ([os.environ['AUDIT_CLIP']] if os.environ.get('AUDIT_CLIP') else ['idle','move','attack','hit','death']):
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;frames=json.loads(sc['sample_frames']);base=bpy.data.objects['GEO-stationary cream stone'];base_mat=base.matrix_world.copy();bounds=[]
 for fr in frames:
  sc.frame_set(fr);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();cam_inv=sc.camera.matrix_world.inverted();span=sc.camera.data.ortho_scale;xs=[];ys=[];zmin=99;culprits=[]
  assert all(abs(base.matrix_world[i][j]-base_mat[i][j])<1e-7 for i in range(4) for j in range(4))
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();xmin=1;ymin=1;xmax=0;ymax=0;low=99
   for v in me.vertices:
    p=ev.matrix_world@v.co;cq=cam_inv@p;q=Vector((.5+cq.x/span,.5+cq.y/span,0));xmin=min(xmin,q.x);ymin=min(ymin,q.y);xmax=max(xmax,q.x);ymax=max(ymax,q.y);low=min(low,p.z)
   ev.to_mesh_clear();xs.extend([xmin,xmax]);ys.extend([ymin,ymax]);zmin=min(zmin,low)
   if xmin<.005 or ymin<.005 or xmax>.995 or ymax>.995 or low<.08:culprits.append({'object':o.name,'bbox':[round(x*256,1) for x in [xmin,1-ymax,xmax,1-ymin]],'min_z':round(low,3)})
  bounds.append({'frame':fr,'bbox256':[round(x*256,1) for x in [min(xs),1-max(ys),max(xs),1-min(ys)]],'min_z':round(zmin,3),'suspects':culprits})
 records[clip]={'stationary_base':True,'samples':bounds};print(clip,[(b['bbox256'],b['min_z']) for b in bounds],flush=True)
(M/('geometry-audit-'+os.environ['AUDIT_CLIP']+'.json' if os.environ.get('AUDIT_CLIP') else 'geometry-audit.json')).write_text(json.dumps(records,indent=2))
failures=[]
for clip,record in records.items():
 for sample in record['samples']:
  x0,y0,x1,y1=sample['bbox256']
  if min(x0,y0,256-x1,256-y1)<2 or sample['min_z']<.08:failures.append((clip,sample['frame'],sample['bbox256'],sample['min_z']))
if failures:raise RuntimeError('Geometry left frame or penetrated below base: '+str(failures))
print('GEOMETRY_AUDIT_PASS',len(records),'clips')


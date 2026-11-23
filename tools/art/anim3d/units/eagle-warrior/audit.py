"""Audit saved unit and all samples; separate technical checks from art approval."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/eagle-warrior';master=M/'eagle-warrior.blend';digest=hashlib.sha256(master.read_bytes()).hexdigest();report={'art_approved':False,'clips':{},'warnings':[]}
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 path=M/'clips'/f'{clip}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;assert sc['source_master_sha256']==digest,'Stale clip';rig=bpy.data.objects['RIG-eagle-warrior'];body=bpy.data.objects['GEO-MPFB-anatomy'];assert len(rig.data.bones)==53;assert len(body.data.vertices)>10000;assert any(m.type=='ARMATURE' and m.object==rig for m in body.modifiers);assert sc['no_billboards']
 base=bpy.data.objects['GEO-cream-stone-base'];fixed=base.matrix_world.copy();samples=[]
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==fixed;assert all(min(abs(x) for x in o.scale)>.0001 for o in sc.objects),'Unsafe scale';dg=bpy.context.evaluated_depsgraph_get();coords=[];zlo=100
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh()
   for v in me.vertices:
    world=o.matrix_world@v.co;zlo=min(zlo,world.z);p=world_to_camera_view(sc,sc.camera,world);coords.append((p.x,p.y))
   ev.to_mesh_clear()
  bounds=[min(p[0] for p in coords),min(p[1] for p in coords),max(p[0] for p in coords),max(p[1] for p in coords)];samples.append({'frame':f,'bounds':bounds,'min_z':zlo})
  if min(bounds[:2])<0 or max(bounds[2:])>1:report['warnings'].append(f'{clip} frame {f}: geometry outside camera {bounds}')
  if zlo<.07:report['warnings'].append(f'{clip} frame {f}: geometry below stone top; min z {zlo:.3f}')
 report['clips'][clip]={'samples':samples,'bones':len(rig.data.bones),'body_vertices':len(body.data.vertices),'base_stationary':True,'source_sha256':digest}
report['ok']=not report['warnings'];(R/'review/3d-v2/eagle-warrior-audit.json').write_text(json.dumps(report,indent=2));print('AUDIT',json.dumps({'ok':report['ok'],'warnings':report['warnings']}),flush=True)
assert not any('outside camera' in w for w in report['warnings']),'Framing must be fixed before GPU delivery'

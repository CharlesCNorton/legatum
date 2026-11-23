"""Saved surface/rig/contact audit. Technical success is never art approval."""
import bpy, os, json, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/eagle-warrior'
master=M/'eagle-warrior.blend';digest=hashlib.sha256(master.read_bytes()).hexdigest()
report={'art_approved':False,'clips':{},'warnings':[]}
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 if os.environ.get('AUDIT_CLIP') and os.environ['AUDIT_CLIP']!=clip:continue
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
 assert sc['source_master_sha256']==digest,'Stale clip'
 rig=bpy.data.objects['RIG-eagle-warrior'];body=bpy.data.objects['GEO-MPFB-anatomy']
 assert len(rig.data.bones)==53 and len(body.data.vertices)==19158
 assert body.data.shape_keys is None
 assert any(m.type=='ARMATURE' and m.object==rig for m in body.modifiers)
 assert sc['no_billboards'] and sc['refinement_round']==2
 assert all(not any(m.type in {'BEVEL','SOLIDIFY','SUBSURF'} for m in o.modifiers) for o in sc.objects if o.type=='MESH'),'unfinished projection surface'
 base=bpy.data.objects['GEO-cream-stone-base'];fixed=base.matrix_world.copy();samples=[]
 top=max((base.matrix_world@v.co).z for v in base.data.vertices)
 radius=max((Vector((v.co.x,v.co.y,0))).length for v in base.data.vertices)-.025
 for f in range(1,n+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==fixed
  assert all(min(abs(x) for x in o.scale)>.0001 for o in sc.objects),'Unsafe scale'
  dg=bpy.context.evaluated_depsgraph_get();coords=[];zlo=100;contact=100;lowest=[];camera_inverse=sc.camera.matrix_world.inverted();scale=sc.camera.data.ortho_scale
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();objlow=100
   for v in me.vertices:
    world=o.matrix_world@v.co;p=camera_inverse@world;coords.append((p.x/scale+.5,p.y/scale+.5))
    if o==base:continue
    zlo=min(zlo,world.z);objlow=min(objlow,world.z)
    if (Vector((world.x-base.location.x,world.y-base.location.y,0))).length<radius:contact=min(contact,world.z)
   ev.to_mesh_clear()
   if o!=base:lowest.append((round(objlow,5),o.name))
  bounds=[min(p[0] for p in coords),min(p[1] for p in coords),max(p[0] for p in coords),max(p[1] for p in coords)]
  head=rig.matrix_world@rig.pose.bones['head'].head
  samples.append({'frame':f,'bounds':bounds,'figure_min_z':zlo,'inside_disc_min_z':contact,'head_z':head.z,'lowest_surfaces':sorted(lowest)[:4]})
  if min(bounds[:2])<0 or max(bounds[2:])>1:report['warnings'].append(f'{clip} frame {f}: geometry outside camera {bounds}')
  if contact<top-.025:report['warnings'].append(f'{clip} frame {f}: stone penetration {top-contact:.4f}m')
  if zlo<-.005:report['warnings'].append(f'{clip} frame {f}: below world ground')
  if clip=='death' and f>=n-1 and head.z>.70:report['warnings'].append(f'{clip} frame {f}: terminal head remains suspended ({head.z:.3f}m)')
 report['clips'][clip]={'samples':samples,'bones':53,'body_vertices':len(body.data.vertices),'base_stationary':True,'source_sha256':digest,'disc_top':top}
report['ok']=not report['warnings']
(R/'review/3d-v2/eagle-warrior-audit.json').write_text(json.dumps(report,indent=2))
print('AUDIT',json.dumps({'ok':report['ok'],'warnings':report['warnings']}),flush=True)
assert report['ok'],'Fix geometry/contact before GPU delivery'

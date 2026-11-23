import bpy,os,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane';bpy.ops.wm.open_mainfile(filepath=str(M/'biplane.blend'));sc=bpy.context.scene;bpy.context.view_layer.update()
for name in ['GEO-engine-hub','RIG-propeller','GEO-propeller-boss','GEO-rubber-wheel','GEO-rubber-wheel.001','GEO-upper-cambered-wing','GEO-horizontal-tail','GEO-cream-stone-base']:
 o=bpy.data.objects[name];p=world_to_camera_view(sc,sc.camera,o.matrix_world.translation);print(name,round(256*p.x,1),round(256*(1-p.y),1))
base0=None;report={}
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene;mins=[];maxs=[];floor=[]
 for f in range(1,sc.frame_end+1):
  sc.frame_set(f);deps=bpy.context.evaluated_depsgraph_get();pts=[];zs=[]
  base=bpy.data.objects['GEO-cream-stone-base'];b=tuple(tuple(r) for r in base.matrix_world)
  if base0 is None:base0=b
  assert base0==b,'base moved'
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   assert min(abs(v) for v in o.scale)>.001,(o.name,'tiny scale')
   eo=o.evaluated_get(deps)
   for v in eo.data.vertices:
    world=eo.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world);pts.append((p.x,p.y));zs.append(world.z)
  mins.append([min(p[a] for p in pts) for a in [0,1]]);maxs.append([max(p[a] for p in pts) for a in [0,1]]);floor.append(min(zs))
 report[clip]={'min_xy':mins,'max_xy':maxs,'min_z':floor,'stationary_base':True}
(M/'geometry-audit.json').write_text(json.dumps(report,indent=2));print('AUDIT stationary base and no tiny scales; frame bounds recorded')

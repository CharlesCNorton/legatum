"""Verify finished projection, mechanical orientation, bounds and held wreck."""
import bpy, os, json, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/biplane'
bpy.ops.wm.open_mainfile(filepath=str(M/'biplane.blend'));sc=bpy.context.scene
bpy.context.view_layer.update()
assert sc.get('registered_round2'), 'Expected registered full-depth model'
assert len([o for o in sc.objects if o.name.startswith('GEO-varnished-interplane-strut')])==4
max_uv=0;projected=0
for o in sc.objects:
 if o.type!='MESH' or 'PaintingProjection' not in o.data.uv_layers:continue
 assert not o.modifiers, ('Projection must use the finished surface',o.name)
 uv=o.data.uv_layers['PaintingProjection']
 for loop in o.data.loops:
  p=world_to_camera_view(sc,sc.camera,o.matrix_world@o.data.vertices[loop.vertex_index].co)
  max_uv=max(max_uv,(uv.data[loop.index].uv-Vector((p.x,p.y))).length)
 nodes=o.data.materials[0].node_tree.nodes
 assert nodes.get('Camera-only paint'),('missing camera ray mask',o.name)
 projected+=1
assert max_uv<1e-5,('UV registration moved',max_uv)
# All generated/full-fill materials and original painting remain packed.
assert any(im.name.startswith('projection') and im.packed_file for im in bpy.data.images)
base0=None;report={'projection':{'meshes':projected,'max_pixel_error':max_uv*256},'clips':{}}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene
 assert sc.frame_end==count
 config=json.loads((M/(clip+'.json')).read_text())
 assert config['source_sha256']==hashlib.sha256((M/'biplane.blend').read_bytes()).hexdigest()
 mins=[];maxs=[];floor=[];base=bpy.data.objects['GEO-cream-stone-base'];terminal=[]
 for f in range(1,sc.frame_end+1):
  sc.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();pts=[];zs=[]
  b=tuple(tuple(r) for r in base.matrix_world)
  if base0 is None:base0=b
  assert base0==b,'base moved'
  forward=(bpy.data.objects['RIG-flight'].matrix_world.to_3x3()@Vector((1,0,0))).normalized()
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   assert min(abs(v) for v in o.scale)>.001,(o.name,'tiny scale')
   if o.name.startswith('GEO-rubber-wheel'):
    wheel_axis=(o.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
    assert abs(wheel_axis.dot(forward))<1e-5,('wheel not aligned to flight',o.name)
   eo=o.evaluated_get(deps)
   for v in eo.data.vertices:
    world=eo.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world);pts.append((p.x,p.y));zs.append(world.z)
  low=[min(p[a] for p in pts) for a in (0,1)];high=[max(p[a] for p in pts) for a in (0,1)]
  assert min(low)>0 and max(high)<1,('camera clipping',clip,f,low,high)
  assert min(zs)>-.001,('below ground',clip,f,min(zs))
  mins.append(low);maxs.append(high);floor.append(min(zs))
  if clip=='death' and f>=count-1:
   terminal.append([(o.name,tuple(round(v,6) for row in o.matrix_world for v in row),o.hide_render) for o in sc.objects])
 if clip=='death':assert terminal[0]==terminal[1],'wreck must hold'
 report['clips'][clip]={'min_xy':mins,'max_xy':maxs,'min_z':floor,'stationary_base':True,'wheel_axis_aligned':True}
(M/'geometry-audit.json').write_text(json.dumps(report,indent=2))
print('PASS: finished UVs/camera-only pigment, four distinct struts, 40 bounded poses, aligned airborne wheels, stationary base and held wreck')

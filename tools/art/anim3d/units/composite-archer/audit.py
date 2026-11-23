"""Saved-geometry checks; explicitly not an artistic or full collision approval."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';result={};firstposes={}
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/f'clips/{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-composite-archer'];meta=json.loads((M/f'clips/{clip}.json').read_text());base=bpy.data.objects['GEO-stationary cream base'];mat=base.matrix_world.copy()
 assert len(rig.data.bones)==53;assert len(bpy.data.objects['GEO-MPFB anatomical archer'].data.vertices)==19158
 assert meta['source_sha256']==hashlib.sha256((M/'composite-archer.blend').read_bytes()).hexdigest()
 if clip!='attack':assert meta['motion']['license']=='CC0-1.0'
 minima=[];terminal=[];contacts=[]
 for f in range(1,meta['frames']+1):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==mat
  if f==1:firstposes[clip]=[x for row in rig.matrix_world for x in row]+[x for p in rig.pose.bones for row in p.matrix for x in row]
  for o in sc.objects:
   assert all(math.isfinite(x) for row in o.matrix_world for x in row),o.name
   assert min(abs(v) for v in o.scale)>.0001,(o.name,'near-zero scale')
  body=bpy.data.objects['GEO-MPFB anatomical archer'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs=[(ev.matrix_world @ v.co).z for v in me.vertices];ev.to_mesh_clear();minima.append(min(zs))
  boots=bpy.data.objects['GEO-soft leather boots'];ev=boots.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
  inside=[p.z for p in points if (p.x-base.location.x)**2+(p.y-base.location.y)**2<.54**2]
  clearance=min(inside)-.085 if inside else None;contacts.append(clearance)
  assert clearance is None or clearance>=-.012,(clip,f,'boot penetrates stone',clearance)
  if clip=='move':assert clearance is not None and abs(clearance-.002)<.003,(clip,f,'missing planted boot support',clearance)
  if clip=='death' and f>=meta['frames']-1:terminal.append([[list(row) for row in p.matrix] for p in rig.pose.bones])
 if clip=='death':assert max(abs(x-y) for a,b in zip(terminal[0],terminal[1]) for aa,bb in zip(a,b) for x,y in zip(aa,bb))<1e-5
 result[clip]={'frames':meta['frames'],'body_min_z':minima,'boot_stone_clearance':contacts,'stationary_base':True,'finite_positive_scales':True,'bones':53}
delta=max(abs(a-b) for a,b in zip(firstposes['idle'],firstposes['death']));assert delta<1e-5,('death start differs from neutral',delta)
result['death_start_max_delta']=delta
result['limitations']=['Not a complete self-collision test','Knee contact, finger grip and projection seams require visual review','No GPU art approval']
(M/'audit.json').write_text(json.dumps(result,indent=2));print('PASS geometry:',json.dumps(result))

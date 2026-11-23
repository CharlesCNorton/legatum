"""Saved-scene audit; visual clearance and craft still require human review."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
records=[];source_hash=hashlib.sha256((MASTER/'archer.blend').read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'archer.blend'))
sc=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();uv_error=0
for obj in sc.objects:
 if obj.type!='MESH' or not obj.data.uv_layers.get('Painting projection'):continue
 assert obj.data.shape_keys is None,(obj.name,'unfrozen macro morph')
 assert all(m.type=='ARMATURE' or not m.show_render for m in obj.modifiers),(obj.name,'unfinished surface')
 ev=obj.evaluated_get(deps);me=ev.to_mesh();uv=obj.data.uv_layers['Painting projection']
 for loop in obj.data.loops:
  q=world_to_camera_view(sc,sc.camera,ev.matrix_world@me.vertices[loop.vertex_index].co)
  uv_error=max(uv_error,(Vector((q.x,q.y))-uv.data[loop.index].uv).length*256)
 ev.to_mesh_clear()
 assert all(m.node_tree.nodes.get('Camera-only painted pigment') for m in obj.data.materials),(obj.name,'missing pigment shader')
assert uv_error<.01,('finished-surface UV registration',uv_error)

for clip,(count,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(MASTER/'clips'/f'{clip}.blend'));sc=bpy.context.scene;assert sc['source_sha256']==source_hash;rig=bpy.data.objects['Archer MPFB rig'];assert len(rig.data.bones)==53;body=bpy.data.objects['GEO-MPFB archer anatomy'];assert len(body.data.vertices)>10000;assert any(m.type=='ARMATURE' and m.object==rig for m in body.modifiers)
 base=bpy.data.objects['GEO-Stationary cream base'];baseworld=base.matrix_world.copy();samples=[];foot_samples=[]
 neutral=json.loads(rig['rest_pose'])
 for f in range(count):
  sc.frame_set(f)
  if clip=='death' and f==0:
   assert max(abs(x-y) for p in rig.pose.bones for row1,row2 in zip(Matrix(neutral[p.name]),p.matrix_basis) for x,y in zip(row1,row2))<1e-4,'death entry pose pops'
  if clip=='move':
   deps=bpy.context.evaluated_depsgraph_get();heights=[];feet={}
   for side in ['l','r']:
    sole=bpy.data.objects['GEO-Sandal sole '+side];ev=sole.evaluated_get(deps);me=ev.to_mesh();heights.append(min((ev.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
    ankle=rig.matrix_world@rig.pose.bones['foot_'+side].head
    toe=rig.matrix_world@rig.pose.bones['ball_'+side].head
    direction=toe-ankle
    # Swing feet may pitch past vertical; planted foot yaw must face travel (-Y).
    feet[side]={'sole_z':heights[-1],'ankle':list(ankle),'toe':list(toe),'direction':list(direction)}
    if heights[-1]<.095:
     assert direction.y<-.025,(f,side,'planted foot points backward')
     assert abs(direction.x)<.025,(f,side,'planted foot yaw drift')
   foot_samples.append({'frame':f,'feet':feet})
   assert abs(min(heights)-.092)<.002,('move sole contact',f,heights)
  assert base.matrix_world==baseworld;assert not base.animation_data
  for o in sc.objects:assert min(abs(v) for v in o.scale)>1e-5,(clip,f,o.name,'zero scale')
  bow=bpy.data.objects['GEO-Yew bow'];string=bpy.data.objects['GEO-Bowstring'];points=bow.data.splines[0].points;sp=string.data.splines[0].points
  errs=[(bow.matrix_world@Vector(points[k].co[:3])-Vector(sp[j].co[:3])).length for k,j in [(0,0),(-1,2)]];assert max(errs)<.0001,(clip,f,'string tip detached',errs)
  if clip!='death' and not (clip=='attack' and 4<=f<=7):
   nock=rig.matrix_world@rig.pose.bones['hand_r'].tail;assert (nock-Vector(sp[1].co[:3])).length<.0001,(clip,f,'nock detached')
  if clip=='death' and f>=8:
   floor=min((bow.matrix_world@Vector(p.co[:3])).z for p in points);assert floor>=.10,(clip,f,'bow below base',floor)
  samples.append({'frame':f,'max_string_tip_error':max(errs)})
 if clip=='move':
  motion=json.loads((MASTER/'clips/move-motion.json').read_text())
  speed=motion['contact']['virtual_ground_m_per_sample']
  residuals=[]
  for side,start,end in [('l',0,4),('r',4,8)]:
   for i in range(start,end-1):
    a=Vector(foot_samples[i]['feet'][side]['toe']);b=Vector(foot_samples[i+1]['feet'][side]['toe'])
    residuals.append(Vector((b.x-a.x,b.y-a.y-speed,0)).length)
  assert max(residuals)<1e-4,('stance toe slides against virtual travel',residuals)
  motion['contact']['measured_max_stance_residual_m']=max(residuals)
  (REVIEW/'archer-foot-contact.json').write_text(json.dumps(motion['contact'],indent=2))
 if loop:
  sc.frame_set(0);a=[p.matrix.copy() for p in rig.pose.bones];loc=rig.location.copy();sc.frame_set(count);assert (rig.location-loc).length<1e-5
  assert max(abs(x-y) for aa,p in zip(a,rig.pose.bones) for row1,row2 in zip(aa,p.matrix) for x,y in zip(row1,row2))<1e-4,(clip,'loop seam')
 records.append({'clip':clip,'samples':samples,'loop_key_matches':loop,'feet':foot_samples})
report={'passed':True,'finished_surface_uv_max_error_px':uv_error,'checks':['MPFB anatomy and 53 bones','source hashes','base fixed','positive scales','bowstring endpoints','hand-to-nock before intentional release','loop closure','planted foot direction -Y'],'clips':records,'limits':'Not a complete mesh collision solver. Modeled cloth is skinned to pelvis/thighs, not simulated.'};(REVIEW/'archer-audit.json').write_text(json.dumps(report,indent=2));log('- Geometry audit passed: anatomy, fixed base, nonzero scales, bow/nock contact and loop closure.');print('ARCHER_AUDIT_PASS')

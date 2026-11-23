"""Saved-scene audit; visual clearance and craft still require human review."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
records=[];source_hash=hashlib.sha256((MASTER/'archer.blend').read_bytes()).hexdigest()
for clip,(count,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(MASTER/'clips'/f'{clip}.blend'));sc=bpy.context.scene;assert sc['source_sha256']==source_hash;rig=bpy.data.objects['Archer MPFB rig'];assert len(rig.data.bones)==53;body=bpy.data.objects['GEO-MPFB archer anatomy'];assert len(body.data.vertices)>10000;assert any(m.type=='ARMATURE' and m.object==rig for m in body.modifiers)
 base=bpy.data.objects['GEO-Stationary cream base'];baseworld=base.matrix_world.copy();samples=[]
 for f in range(count):
  sc.frame_set(f);assert base.matrix_world==baseworld;assert not base.animation_data
  for o in sc.objects:assert min(abs(v) for v in o.scale)>1e-5,(clip,f,o.name,'zero scale')
  bow=bpy.data.objects['GEO-Yew bow'];string=bpy.data.objects['GEO-Bowstring'];points=bow.data.splines[0].points;sp=string.data.splines[0].points
  errs=[(bow.matrix_world@Vector(points[k].co[:3])-Vector(sp[j].co[:3])).length for k,j in [(0,0),(-1,2)]];assert max(errs)<.0001,(clip,f,'string tip detached',errs)
  if clip!='death' and not (clip=='attack' and 4<=f<=7):
   nock=rig.matrix_world@rig.pose.bones['hand_r'].tail;assert (nock-Vector(sp[1].co[:3])).length<.0001,(clip,f,'nock detached')
  if clip=='death' and f>=8:
   floor=min((bow.matrix_world@Vector(p.co[:3])).z for p in points);assert floor>=.10,(clip,f,'bow below base',floor)
  samples.append({'frame':f,'max_string_tip_error':max(errs)})
 if loop:
  sc.frame_set(0);a=[p.matrix.copy() for p in rig.pose.bones];loc=rig.location.copy();sc.frame_set(count);assert (rig.location-loc).length<1e-5
  assert max(abs(x-y) for aa,p in zip(a,rig.pose.bones) for row1,row2 in zip(aa,p.matrix) for x,y in zip(row1,row2))<1e-4,(clip,'loop seam')
 records.append({'clip':clip,'samples':samples,'loop_key_matches':loop})
report={'passed':True,'checks':['MPFB anatomy and 53 bones','source hashes','base fixed','positive scales','bowstring endpoints','hand-to-nock before intentional release','loop closure'],'clips':records,'limits':'Not a complete mesh collision solver. Cloth folds are modeled and attached to pelvis, not simulated.'};(REVIEW/'archer-audit.json').write_text(json.dumps(report,indent=2));log('- Geometry audit passed: anatomy, fixed base, nonzero scales, bow/nock contact and loop closure.');print('ARCHER_AUDIT_PASS')

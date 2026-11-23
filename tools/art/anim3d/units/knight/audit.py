"""Audit actual scene geometry and source gait. Art/foot-slide approval stays manual."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
import sys
sys.path.insert(0,str(Path(__file__).parent))
from contacts import foot_indices
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight';report={'clips':{},'art_approved':False}
(M/'audit.json').unlink(missing_ok=True)
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 p=M/'clips'/f'{clip}.blend';bpy.ops.wm.open_mainfile(filepath=str(p));sc=bpy.context.scene;frames=json.loads(sc['sample_frames']);assert len(frames)==count
 horse=bpy.data.objects['Horse'];rig=bpy.data.objects['AnimalArmature'];base=bpy.data.objects['Stationary cream stone'];rest=base.matrix_world.copy();records=[]
 assert sc['horse_source_action'].startswith('AnimalArmature|')
 assert sc['source_master_sha256']==hashlib.sha256((M/'knight.blend').read_bytes()).hexdigest(),'Stale clip'
 for frame in frames:
  sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==rest
  for ob in sc.objects:
   assert min(abs(x) for x in ob.scale)>1e-5,f'Near-zero scale: {ob.name}'
  ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();points=[ev.matrix_world @ v.co for v in mesh.vertices];floor=min(v.z for v in points);ev.to_mesh_clear()
  hoof_floors={n:min(points[i].z for i in ids) for n,ids in foot_indices(horse).items()}
  if clip!='death':assert min(hoof_floors.values())>=.105,(clip,frame,hoof_floors)
  soles={n:min((points[i] for i in ids),key=lambda v:v.z) for n,ids in foot_indices(horse).items()}
  support={n:{'point':list(p),'radius':((p.x-base.location.x)**2+(p.y-base.location.y)**2)**.5,'on_disc':((p.x-base.location.x)**2+(p.y-base.location.y)**2)**.5<=1.02*base.scale.x} for n,p in soles.items()}
  if clip!='death':assert all(s['on_disc'] for s in support.values()),(clip,frame,support)
  feet={n:list(rig.matrix_world @ rig.pose.bones[n].head) for n in ['FF.L','FF.R','FFB.L','FFB.R']}
  records.append({'frame':frame,'horse_floor':floor,'hoof_floors':hoof_floors,'sole_footprint':support,'source_foot_targets':feet})
 report['clips'][clip]={'blend_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'horse_action':sc['horse_source_action'],'rider_action':sc['rider_source_action'],'frames':records}
report['limitations']=['In-place gait uses unaltered CC0 foot axes; front/top render is required for visual check.','Vertical skin correctives preserve native foot lift; disc-constrained translation and foot sliding still need visual review.','Caparison is bone-driven cloth; collision freedom and foot sliding are not automatically certified.']
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_PASS: five source actions, frame counts, stationary base, nonzero scales, hoof plane clearance and disc footprint, current master hashes; gait measurements recorded')

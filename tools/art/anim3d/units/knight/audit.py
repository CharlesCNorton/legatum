"""Audit actual scene geometry and source gait. Art/foot-slide approval stays manual."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight';report={'clips':{},'art_approved':False}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 p=M/'clips'/f'{clip}.blend';bpy.ops.wm.open_mainfile(filepath=str(p));sc=bpy.context.scene;frames=json.loads(sc['sample_frames']);assert len(frames)==count
 horse=bpy.data.objects['Horse'];rig=bpy.data.objects['AnimalArmature'];base=bpy.data.objects['Stationary cream stone'];rest=base.matrix_world.copy();records=[]
 assert sc['horse_source_action'].startswith('AnimalArmature|')
 for frame in frames:
  sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==rest
  for ob in sc.objects:
   assert min(abs(x) for x in ob.scale)>1e-5,f'Near-zero scale: {ob.name}'
  ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();floor=min((ev.matrix_world@v.co).z for v in mesh.vertices);ev.to_mesh_clear()
  feet={n:list(rig.matrix_world@rig.pose.bones[n].head) for n in ['FF.L','FF.R','FFB.L','FFB.R']}
  records.append({'frame':frame,'horse_floor':floor,'source_foot_targets':feet})
 report['clips'][clip]={'blend_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'horse_action':sc['horse_source_action'],'rider_action':sc['rider_source_action'],'frames':records}
report['limitations']=['In-place gait uses unaltered CC0 foot axes; front/top render is required for visual check.','Grounding uses whole-horse mesh minimum, not a full hoof-contact/stride solver.','Caparison is bone-driven cloth; collision freedom and foot sliding are not automatically certified.']
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_PASS: five source actions, frame counts, stationary base, nonzero scales; gait measurements recorded')

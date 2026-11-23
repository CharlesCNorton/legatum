"""Audit source topology, hierarchy, per-frame geometry and planted terminal death."""
import bpy,os,json,math
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/horseman-3d';report={};errors=[]
def bounds(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;horse=bpy.data.objects['Horse'];rider=bpy.data.objects['Rider MPFB CC0 anatomy'];rig=bpy.data.objects['Rider MPFB game_engine'];base=bpy.data.objects['Stationary cream stone']
 assert horse.type=='MESH' and rider.type=='MESH' and len(rider.data.vertices)>10000
 assert any(m.type=='ARMATURE' for m in horse.modifiers);assert any(m.type=='ARMATURE' for m in rider.modifiers)
 assert rig.parent.name=='AnimalArmature' and rig.parent_type=='BONE' and rig.parent_bone=='Torso'
 base_matrix=[list(row) for row in base.matrix_world];frames=[]
 for f in json.loads(sc['sample_frames']):
  sc.frame_set(f);bpy.context.view_layer.update();assert [list(row) for row in base.matrix_world]==base_matrix
  hb=bounds(horse);rb=bounds(rider);frames.append({'frame':f,'horse_bounds':hb,'rider_bounds':rb,'source_foot_controls':{n:list(bpy.data.objects['AnimalArmature'].matrix_world@bpy.data.objects['AnimalArmature'].pose.bones[n].head) for n in ['FF.L','FF.R','FFB.L','FFB.R']}})
  if hb[2][0]<.075:errors.append(f'{clip}/{f}: horse penetrates base: {hb[2][0]:.3f}')
  if rb[2][0]<.075:errors.append(f'{clip}/{f}: rider penetrates base: {rb[2][0]:.3f}')
 if clip=='move':
  flight=sum(all(p[2]>.25 for p in f['source_foot_controls'].values()) for f in frames)
  if flight>2:errors.append(f'Canter has {flight}/8 unsupported samples; stance timing needs correction')
 if clip=='death':
  if frames[-1]['horse_bounds'][2][0]>.17:errors.append('Death horse is not planted on base')
  if frames[-1]['horse_bounds'][2][1]>1.35:errors.append('Death horse remains too high')
  if frames[-1]['horse_bounds']!=frames[-2]['horse_bounds']:errors.append('Terminal death geometry is not held')
 report[clip]={'source_action':sc['horse_source_action'],'horse_vertices':len(horse.data.vertices),'rider_vertices':len(rider.data.vertices),'stationary_base':True,'saddle_parented':True,'frames':frames}
report['errors']=errors;(R/'review/3d-v2/horseman-rig-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'clips':5,'errors':errors},indent=2))
if errors:raise RuntimeError('Mounted geometry audit failed')

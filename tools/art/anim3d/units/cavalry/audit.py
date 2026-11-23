"""Structural audit; does not substitute for contact/intersection art review."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';records=[]
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;horse=bpy.data.objects['Horse'];body=bpy.data.objects['Rider MPFB CC0 anatomy'];rig=bpy.data.objects['Rider MPFB game_engine'];base=bpy.data.objects['Stationary cream stone']
 assert len(body.data.vertices)>10000 and len(rig.data.bones)==53
 assert any(m.type=='ARMATURE' for m in horse.modifiers) and any(m.type=='ARMATURE' for m in body.modifiers)
 assert rig.parent_type=='BONE' and rig.parent_bone=='Torso'
 tail=bpy.data.objects['GEO-swept-tail-locks']
 assert tail.parent==horse.parent and tail.parent_type==horse.parent_type,'Tail must share horse root hierarchy'
 initial=base.matrix_world.copy();heights=[];hoof_samples=[]
 for f in json.loads(sc['sample_frames']):
  sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==initial
  assert all(min(abs(v) for v in ob.scale)>.00001 for ob in sc.objects), 'Unsafe zero scale'
  for suffix in ['', '.001']:
   rein=bpy.data.objects['Slack leather rein'+suffix];bridle=bpy.data.objects['Cheek bridle'+suffix]
   bit=bridle.matrix_world @ bridle.data.splines[0].points[-1].co.xyz
   endpoint=rein.matrix_world @ rein.data.splines[0].points[0].co.xyz
   assert (endpoint-bit).length<.002,f'{clip}/{f}: detached rein at bit'

  for ob in [horse,body]:
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=[(ev.matrix_world @ v.co).z for v in me.vertices];ev.to_mesh_clear();heights.append({'frame':f,'object':ob.name,'min_z':min(z),'max_z':max(z)})
   if ob==horse:
    soles={}
    for name in ['FF.L','FF.R','FFB.L','FFB.R']:
     group=horse.vertex_groups[name].index
     ids=[v.index for v in horse.data.vertices if any(g.group==group and g.weight>.5 for g in v.groups)]
     soles[name]=min(z[i] for i in ids)
    hoof_samples.append({'frame':f,'lowest_z':soles,'below_stone_warning':any(h<.09 for h in soles.values())})
 records.append({'clip':clip,'stationary_base':True,'rigs':True,'height_samples':heights,'hoof_samples':hoof_samples,'rider_source_action':sc.get('rider_source_action'),'horse_source_action':sc.get('horse_source_action'),'contact_method':sc.get('contact_method','source collapse plus floor solver')})
(R/'review/3d-v2/cavalry-audit.json').write_text(json.dumps({'structural_pass':True,'clips':records,'limitations':'No exhaustive mesh collision or hoof slip solver. Inspect strips and video.'},indent=2)+'\n');print('AUDIT cavalry dual rigs, anatomy, safe scale and fixed base passed')

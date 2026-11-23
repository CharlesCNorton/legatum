"""Structural audit; does not substitute for contact/intersection art review."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';records=[]
for clip in ['idle','move','attack','hit','death']:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;horse=bpy.data.objects['Horse'];body=bpy.data.objects['Rider MPFB CC0 anatomy'];rig=bpy.data.objects['Rider MPFB game_engine'];base=bpy.data.objects['Stationary cream stone']
 assert len(body.data.vertices)>10000 and len(rig.data.bones)==53
 assert any(m.type=='ARMATURE' for m in horse.modifiers) and any(m.type=='ARMATURE' for m in body.modifiers)
 assert rig.parent_type=='BONE' and rig.parent_bone=='Torso'
 initial=base.matrix_world.copy();heights=[]
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
 records.append({'clip':clip,'stationary_base':True,'rigs':True,'height_samples':heights})
(R/'review/3d-v2/cavalry-audit.json').write_text(json.dumps({'structural_pass':True,'clips':records,'limitations':'No exhaustive mesh collision or hoof slip solver. Inspect strips and video.'},indent=2)+'\n');print('AUDIT cavalry dual rigs, anatomy, safe scale and fixed base passed')

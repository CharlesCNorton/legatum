"""Audit saved geometry and actual sampled contacts, independently of image packing."""
import bpy,bmesh,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, REVIEW, SLUG, CLIPS, log
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'finished.blend'))
sc=bpy.context.scene
meshes=[o for o in sc.objects if o.type=='MESH'];bad=[]
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data)
 if any(not e.is_manifold for e in bm.edges):bad.append(o.name)
 bm.free()
 assert min(abs(s) for s in o.scale)>.01,o.name
assert not bad,bad
assert len(meshes)>40
assert len(json.loads(sc['legs']))==4
materials=json.loads((MASTER/'materials.json').read_text());assert len(materials['bakes'])==3
for maps in materials['bakes'].values():
 for path in maps.values():assert Path(path).stat().st_size>100
maxplant=0;maxlength=0
for clip,(count,fps,loop) in CLIPS.items():
 bpy.ops.wm.open_mainfile(filepath=str(MASTER/'clips'/f'{clip}.blend'));sc=bpy.context.scene;legs=json.loads(sc['legs']);base=bpy.data.objects['GEO-Stationary cream disc'];base0=base.matrix_world.copy();samples=json.loads(sc['sample_frames']);assert len(samples)==count
 records=json.loads((MASTER/'clips'/f'{clip}-kinematics.json').read_text())
 for frame in samples:
  sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==base0
  for leg,c in zip(legs,records[frame-1]['contacts']):
   foot=bpy.data.objects['RIG-foot-'+leg['name']].matrix_world.translation
   if not c['airborne']:
    error=(foot-Vector(leg['foot'])).length;assert error<1e-5;maxplant=max(maxplant,error)
   hip0,knee0,foot0=[Vector(leg[k]) for k in ('hip','knee','foot')]
   upper=bpy.data.objects['RIG-upper-'+leg['name']];lower=bpy.data.objects['RIG-lower-'+leg['name']]
   assert ((upper.matrix_world @ (knee0-hip0))-lower.matrix_world.translation).length<1e-5,'Disconnected knee'
   assert ((lower.matrix_world @ (foot0-knee0))-foot).length<1e-5,'Disconnected foot'
   for k in ('upper_error','lower_error'):assert c[k]<1e-5;maxlength=max(maxlength,c[k])
  assert not any(min(abs(s) for s in o.scale)<.01 for o in sc.objects if o.type=='MESH')
 if loop:
  for leg in legs:
   foot=bpy.data.objects['RIG-foot-'+leg['name']];sc.frame_set(1);a=foot.matrix_world.copy();sc.frame_set(count+1);assert (foot.matrix_world.translation-a.translation).length<1e-5
 if clip=='death':assert samples[-1]==samples[-2]
result={'contract':'PASS','meshes':len(meshes),'closed_meshes':True,'legs':4,'baked_maps':6,'max_planted_foot_error':maxplant,'max_segment_length_error':maxlength,'stationary_base':True,'held_death':True,'master_sha256':hashlib.sha256((MASTER/'finished.blend').read_bytes()).hexdigest(),'art_approval':False}
(REVIEW/f'{SLUG}-audit.json').write_text(json.dumps(result,indent=2));log('Geometry/contact audit PASS: closed volumes, four IK legs, fixed planted feet, constant segments, stationary disc, six bakes, no zero scales.');print(json.dumps(result))

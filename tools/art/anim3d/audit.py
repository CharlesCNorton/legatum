"""Inspect saved animation geometry, immutable base and persistent cloth cache."""
import bpy,os,json,sys,hashlib
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/spearman-3d-v2';report={};failures=[];entry_arms={}
clips=[os.environ['AUDIT_CLIP']] if os.environ.get('AUDIT_CLIP') else ['idle','move','attack','hit','death']
for clip in clips:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/clip/(clip+'.blend')))
 sc=bpy.context.scene
 assert sc.get('source_master_sha256')==hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest(), f'{clip}: stale master; regenerate clip'
 base=bpy.data.objects['Stationary cream stone'];base_matrix=base.matrix_world.copy()
 floor=max((base.matrix_world @ v.co).z for v in base.data.vertices)
 base_inverse=base.matrix_world.inverted()
 base_radius=max((v.co.x*v.co.x+v.co.y*v.co.y)**.5 for v in base.data.vertices)-.015
 assert base.data.uv_layers.get('Painting camera rest') is None, 'Static base must not project painted feet/shadows'
 assert [m.get('sRGB_base') for m in base.data.materials]==['#E9CFA0','#B68A51'], 'Shared cream base palette changed'
 for mat in base.data.materials:
  output=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
  assert output.inputs['Surface'].links[0].from_node.type=='BSDF_PRINCIPLED', 'Base must retain physical contact shading'
 rig=bpy.data.objects['Spearman • MPFB game_engine'];body=bpy.data.objects['MPFB anatomical male • original topology']
 assert len(body.data.vertices)==19158 and len(rig.data.bones)==53
 cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip'];assert cloth.point_cache.is_baked
 rows=[]
 for frame in json.loads(sc['sample_frames']):
  sc.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();bounds=[1.,1.,0.,0.];minz=100;lowest=None;disc_minz=100;disc_lowest=None
  if not rows:
   entry_arms[clip]={name:rig.matrix_world @ rig.pose.bones[name].head
                    for name in ['upperarm_r','lowerarm_r','hand_r','upperarm_l','lowerarm_l','hand_l']}
  if clip in ['attack','hit'] and frame==json.loads(sc['sample_frames'])[-1]:
   entry_arms[clip+' exit']={name:rig.matrix_world @ rig.pose.bones[name].head
                            for name in entry_arms[clip]}
  assert base.matrix_world==base_matrix
  for o in sc.objects:
   if o.type not in ['MESH','CURVE'] or o==base or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh()
   for v in me.vertices:
    w=o.matrix_world @ v.co
    if w.z<minz:minz=w.z;lowest=o.name
    local=base_inverse @ w
    if local.x*local.x+local.y*local.y<=base_radius**2 and w.z<disc_minz:disc_minz=w.z;disc_lowest=o.name
    p=world_to_camera_view(sc,sc.camera,w);bounds=[min(bounds[0],p.x),min(bounds[1],p.y),max(bounds[2],p.x),max(bounds[3],p.y)]
   ev.to_mesh_clear()
  # Visible spear crossings must not be accepted by an in-frame-only audit.
  shaft=bpy.data.objects['Ash dory shaft'];points=shaft.data.splines[0].points
  start=shaft.matrix_world @ Vector(points[0].co[:3]);end=shaft.matrix_world @ Vector(points[-1].co[:3])
  axis=(end-start).normalized();length=(end-start).length
  hand=rig.matrix_world @ rig.pose.bones['hand_r'].head
  grip_distance=((hand-start)-axis*(hand-start).dot(axis)).length
  released=clip=='death' and (frame-25)/max(1,sc.frame_end-25)>sc.get('spear_release_start',1)
  if not released and grip_distance>.10:failures.append(f'{clip}/{frame}: hand is {grip_distance:.3f} m from spear')
  crossings=[]
  for name in ['Forged bronze muscle cuirass','Convex bronze aspis','Corinthian helmet crown']:
   ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh()
   tree=BVHTree.FromPolygons([ob.matrix_world @ v.co for v in me.vertices],[list(p.vertices) for p in me.polygons])
   if tree.ray_cast(start,axis,length)[0] is not None:crossings.append(name)
   ev.to_mesh_clear()
  if crossings:failures.append(f'{clip}/{frame}: spear intersects {", ".join(crossings)}')
  row={'shaft_start':list(start),'shaft_end':list(end),'shaft_length':length,'spear_released':released,'grip_distance':grip_distance,'spear_crossings':crossings,'frame':frame,'camera_bounds':bounds,'min_z':minz,'lowest_object':lowest,'disc_min_z':disc_minz,'disc_lowest_object':disc_lowest};rows.append(row)
  if min(bounds[:2])<0 or max(bounds[2:])>1:failures.append(f'{clip}/{frame}: geometry outside camera')
  if disc_minz<floor-.01:failures.append(f'{clip}/{frame}: {disc_lowest} intersects base, z={disc_minz:.4f}, top={floor:.4f}')
  if minz<0:failures.append(f'{clip}/{frame}: {lowest} below ground, z={minz:.4f}')
 report[clip]=rows
transition_errors={}
if 'idle' in entry_arms:
 for clip in ['attack','death','hit','attack exit','hit exit']:
  if clip not in entry_arms:continue
  transition_errors[clip]={}
  for name,point in entry_arms[clip].items():
   distance=(point-entry_arms['idle'][name]).length
   transition_errors[clip][name]=distance
   if distance>.002:failures.append(f'{clip}: {name} differs from idle by {distance:.4f}m')
report['arm_transition_errors']=transition_errors
report['failures']=failures;(R/'review/3d-v2'/('rig-audit-'+clips[0]+'.json' if len(clips)==1 else 'rig-audit.json')).write_text(json.dumps(report,indent=2))
print('AUDIT',len(failures),'findings')
for f in failures:print(f)
raise SystemExit(bool(failures))

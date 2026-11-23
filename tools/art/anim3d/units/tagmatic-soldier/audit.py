"""Evaluate sampled meshes, record clip bounds and stationary-base evidence."""
import bpy, json, os, math, sys
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier';records={}
for clip in ([os.environ['AUDIT_CLIP']] if os.environ.get('AUDIT_CLIP') else ['idle','move','attack','hit','death']):
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;frames=json.loads(sc['sample_frames']);base=bpy.data.objects['GEO-stationary cream stone'];base_mat=base.matrix_world.copy();bounds=[]
 rig=bpy.data.objects['RIG-Tagmatic MPFB'];body=bpy.data.objects['GEO-MPFB anatomical soldier']
 assert len(rig.data.bones)==53 and len(body.data.vertices)==19158,'MPFB anatomy changed'
 assert sc['finished_surface_projection'],'Unfinished projection surface'
 assert sc.view_settings.view_transform=='Standard','Painted illumination display mismatch'
 for o in sc.objects:
  assert all(abs(v)>.001 for v in o.scale),('Unsafe scale',o.name)
  if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):
   assert not any(m.type in {'BEVEL','SOLIDIFY','SUBSURF'} for m in o.modifiers),('Unfinished rigid surface',o.name)
  if o.type=='MESH' and o!=base:
   for ma in o.data.materials:
    assert ma.node_tree.nodes.get('Camera only painted pigment'),('Missing camera-only pigment',o.name)

 # Relative transforms certify released ornaments remain one rigid assembly.
 sc.frame_set(frames[0]);bpy.context.view_layer.update()
 assemblies=[]
 for prefixes in [('GEO-overhand ash','GEO-iron spear socket','GEO-forged iron spear'),('GEO-convex wooden kite','GEO-kite shield','GEO-shield brass','GEO-vertical cross','GEO-horizontal cross','GEO-shield boss','GEO-shield back')]:
  group=[o for o in sc.objects if o.name.startswith(prefixes)];reference=group[0]
  assemblies.append((reference,[(o,reference.matrix_world.inverted()@o.matrix_world) for o in group[1:]]))
 for fr in frames:
  sc.frame_set(fr);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();cam_inv=sc.camera.matrix_world.inverted();span=sc.camera.data.ortho_scale;xs=[];ys=[];zmin=99;culprits=[];feet={};directions={}
  shaft=bpy.data.objects['GEO-overhand ash spear']
  a,b=[shaft.matrix_world@Vector(p) for p in json.loads(shaft['shaft_axis_local'])]
  hand=rig.pose.bones['hand_r'];palm=rig.matrix_world@hand.head.lerp(hand.tail,.45)
  axis=(b-a).normalized();nearest=a+axis*max(0,min((b-a).length,(palm-a).dot(axis)))
  grip_distance=(palm-nearest).length
  if clip!='death' or fr<=3:assert grip_distance<.055,(clip,fr,'detached grip',grip_distance)
  assert all(abs(base.matrix_world[i][j]-base_mat[i][j])<1e-7 for i in range(4) for j in range(4))
  for reference,parts in assemblies:
   for ob,expected in parts:
    actual=reference.matrix_world.inverted()@ob.matrix_world
    assert max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4))<.0001,(clip,fr,'rigid assembly drift',ob.name)
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();xmin=1;ymin=1;xmax=0;ymax=0;low=99
   for v in me.vertices:
    p=ev.matrix_world@v.co;cq=cam_inv@p;q=Vector((.5+cq.x/span,.5+cq.y/span,0));xmin=min(xmin,q.x);ymin=min(ymin,q.y);xmax=max(xmax,q.x);ymax=max(ymax,q.y);low=min(low,p.z)
   if o.name.startswith('GEO-closed leather shoe'):
    feet[o.name]=round(low,5)
    forward=ev.matrix_world.to_3x3()@Vector((0,-1,0));directions[o.name]={'yaw_degrees':round(math.degrees(math.atan2(forward.x,-forward.y)),3),'sole_min_z':round(low,5)}
   ev.to_mesh_clear();xs.extend([xmin,xmax]);ys.extend([ymin,ymax]);zmin=min(zmin,low) if o!=base else zmin
   if xmin<.005 or ymin<.005 or xmax>.995 or ymax>.995 or (o!=base and low<.165):culprits.append({'object':o.name,'bbox':[round(x*256,1) for x in [xmin,1-ymax,xmax,1-ymin]],'min_z':round(low,3)})
  bounds.append({'frame':fr,'grip_distance':round(grip_distance,5),'bbox256':[round(x*256,1) for x in [min(xs),1-max(ys),max(xs),1-min(ys)]],'min_z':round(zmin,3),'suspects':culprits,'shoe_min_z':feet,'feet_direction':directions})
 records[clip]={'stationary_base':True,'samples':bounds};print(clip,[(b['bbox256'],b['min_z']) for b in bounds],flush=True)
(M/('geometry-audit-'+os.environ['AUDIT_CLIP']+'.json' if os.environ.get('AUDIT_CLIP') else 'geometry-audit.json')).write_text(json.dumps(records,indent=2))
failures=[]
for clip,record in records.items():
 for sample in record['samples']:
  x0,y0,x1,y1=sample['bbox256']
  if clip!='death' and min(sample['shoe_min_z'].values())<.165:failures.append((clip,sample['frame'],'shoe below stone',sample['shoe_min_z']))
  if min(x0,y0,256-x1,256-y1)<2 or sample['min_z']<.165:failures.append((clip,sample['frame'],sample['bbox256'],sample['min_z']))
if failures:raise RuntimeError('Geometry left frame or penetrated below base: '+str(failures))
print('GEOMETRY_AUDIT_PASS',len(records),'clips')


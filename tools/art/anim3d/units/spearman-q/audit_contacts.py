"""Sampled mesh-surface intersections, excluding the deliberate hand grip.

This checks body versus the shield shell and spear; it is not continuous
collision detection or a general garment self-intersection test.
"""
import bpy,json,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))/'lanes/spearman-q-r2'
def tree(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
 points=[o.matrix_world @ v.co for v in m.vertices];tris=[tuple(t.vertices) for t in m.loop_triangles]
 b=BVHTree.FromPolygons(points,tris,all_triangles=True);e.to_mesh_clear();return b,tris,points
report={}
for clip in ('attack','idle','walk','hit','death'):
 bpy.ops.wm.open_mainfile(filepath=str(root/'masters'/f'{clip}.blend'));s=bpy.context.scene
 ob=bpy.data.objects['SuperHero_Male'];groups={v.index:ob.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name for v in ob.data.vertices if v.groups}
 rows=[]
 for f in range(1,s.frame_end+1):
  s.frame_set(f);bt,tris,_=tree(ob);row={'frame':f,'torso_or_head':{},'released_body_contacts':{}}
  for name in ['KIT Convex bronze aspis','GEO-Rigid spear shaft','GEO-Rigid spear leaf']:
   pt,_,pp=tree(bpy.data.objects[name]);pairs=bt.overlap(pt)
   core=[(i,j) for i,j in pairs if any(groups.get(v,'') in ('Head','neck_01','spine_01','spine_02','spine_03','pelvis') for v in tris[i])]
   if core:row['torso_or_head'][name]=len(core)
   if clip=='death' and f>=5 and pairs:row['released_body_contacts'][name]=len(pairs)
  if row['torso_or_head'] or row['released_body_contacts']:rows.append(row)
 report[clip]=rows
(root/'collision-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('COLLISIONS',json.dumps(report))

assert not any(report.values()),report

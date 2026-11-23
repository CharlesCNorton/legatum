"""Audit actual saved mesh/rig/clip data, not visual approval."""
import bpy,os,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/byzantine-heir';report={}
bpy.ops.wm.open_mainfile(filepath=str(M/'byzantine-heir.blend'));rig=bpy.data.objects['Heir MPFB game_engine'];body=bpy.data.objects['Heir MPFB anatomy'];assert len(rig.data.bones)>=50;assert len(body.data.vertices)>10000
assert bpy.context.scene.get('finish_version')==3,'Finished-surface refinement missing'
assert body.data.shape_keys is None,'Active macro shapes override fitting'
assert all(m.type not in {'BEVEL','SOLIDIFY','SUBSURF'} for ob in bpy.context.scene.objects if ob.type=='MESH' and not ob.data.shape_keys and ob.name!='Stationary cream stone' for m in ob.modifiers),'Unfinished rigid surface'
sc=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();max_error=0
for ob in sc.objects:
 if ob.type!='MESH' or ob.name=='Stationary cream stone':continue
 for mat in ob.data.materials:
  assert 'Camera painted pigment' in mat.node_tree.nodes,(ob.name,'Missing camera pigment')
 if ob.data.shape_keys:continue
 ev=ob.evaluated_get(deps);me=ev.to_mesh();uv=me.uv_layers['Rest painting']
 coords=[world_to_camera_view(sc,sc.camera,ev.matrix_world@v.co) for v in me.vertices]
 for loop in me.loops:
  q=coords[loop.vertex_index];p=uv.data[loop.index].uv
  max_error=max(max_error,256*((p.x-q.x)**2+(p.y-q.y)**2)**.5)
 ev.to_mesh_clear()
assert max_error<.01,('Frozen UV registration',max_error)
report['finished_projection_max_error_px']=max_error
report['anatomy']={'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'origin':rig['origin']};report['geometry']={'mesh_count':sum(o.type=='MESH' for o in bpy.context.scene.objects),'projection':json.loads((M/'projection.json').read_text())['method']};report['clips']={}
neutral_staff=bpy.data.objects['Banner staff control'].matrix_world.copy()
for side in ['l','r']:
 boot=bpy.data.objects['Tall leather boot '+side]
 assert boot.get('pose_bound_costume') and boot.modifiers.get('Continuous costume skin')
 assert {'calf_'+side,'foot_'+side}=={g.name for g in boot.vertex_groups}
assert 'Painted dark woven breeches' in body.data.materials
ankle_overlap=[]
for name,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/name/'clip.blend'));sc=bpy.context.scene;base=bpy.data.objects['Stationary cream stone'];initial=base.matrix_world.copy();assert sc.frame_end==n
 sc.frame_set(1);bpy.context.view_layer.update()
 staff=bpy.data.objects['Banner staff control'].matrix_world
 assert name=='move' or max(abs(staff[r][c]-neutral_staff[r][c]) for r in range(4) for c in range(4))<.0001,(name,'Entry staff pop')
 for f in range(1,n+1):
  sc.frame_set(f);assert base.matrix_world==initial,'Base moved';assert not base.animation_data
  bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
  for side in ['l','r']:
   toe=bpy.data.objects['Leather toe '+side];te=toe.evaluated_get(deps);tm=te.to_mesh()
   tree=BVHTree.FromPolygons([te.matrix_world@v.co for v in tm.vertices],[list(p.vertices) for p in tm.polygons])
   boot=bpy.data.objects['Tall leather boot '+side];be=boot.evaluated_get(deps);bm=be.to_mesh()
   group=boot.vertex_groups['foot_'+side].index;inside=0
   for v in bm.vertices:
    if not any(g.group==group and g.weight>.999 for g in v.groups):continue
    point=be.matrix_world@v.co;near,normal,_,distance=tree.find_nearest(point)
    if near is not None and (point-near).dot(normal)<0:inside+=1
   be.to_mesh_clear();te.to_mesh_clear()
   assert inside>=8,(name,f,side,'Boot cuff is not embedded in shoe',inside)
   ankle_overlap.append(inside)
  if name=='move':
   soles=[]
   for side in ['r','l']:
    toe=bpy.data.objects['Leather toe '+side]
    lowest=min((toe.matrix_world@v.co).z for v in toe.data.vertices)
    assert lowest>=.089,(name,f,side,'Sole penetrates base',lowest)
    soles.append(lowest)
   assert min(soles)<.091,(name,f,'No planted foot',soles)
  for ob in sc.objects:
   assert min(abs(v) for v in ob.scale)>.001,(name,f,ob.name,'near-zero scale')
 report['clips'][name]={'frames':n,'base_stationary':True,'positive_scale':True}
# Inspect the mocap stance in the travelling frame, not only the in-place
# atlas. Record residuals separately from visual acceptance.
bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move/clip.blend'));sc=bpy.context.scene
motion=json.loads((M/'clips/move/clip.json').read_text())['motion'];feet=[];slips=[];previous={}
for index in range(8):
 sc.frame_set(index+1);bpy.context.view_layer.update();travel=Vector(motion['samples'][index]['root_motion_m'])
 for side in ['l','r']:
  toe=bpy.data.objects['Leather toe '+side];points=[toe.matrix_world@v.co for v in toe.data.vertices];low=min(p.z for p in points)
  contact=[p for p in points if p.z<low+.005];centre=sum(contact,Vector())/len(contact)+travel
  forward=toe.matrix_world.to_3x3()@Vector((0,-1,0));forward.z=0;forward.normalize()
  angle=math.degrees(math.acos(max(-1,min(1,forward.dot(Vector((0,-1,0)))))))
  planted=low<.115
  if side in previous and planted and previous[side][1]:
   delta=centre-previous[side][0];delta.z=0;slips.append(delta.length)
  previous[side]=(centre,planted);feet.append({'frame':index+1,'side':side,'sole_z':low,'yaw_from_travel_degrees':angle,'planted':planted})
assert max(slips,default=0)<.002,('Planted-foot slip exceeds 2mm',max(slips))
assert max(x['yaw_from_travel_degrees'] for x in feet if x['planted'])<10,'Planted feet do not face travel'
report['ankle_join']={'minimum_embedded_vertices':min(ankle_overlap),'samples':len(ankle_overlap),'method':'Evaluated lower boot vertices inside closed shoe BVH in all 40 poses, both legs'}
report['feet']={'samples':feet,'max_stance_step_residual_m':max(slips,default=0),'max_yaw_degrees':max(x['yaw_from_travel_degrees'] for x in feet),'note':'Measured residuals are not an automatic art PASS; inspect g-feet-check.png'}
report['limitations']=['Not a full cloth/body collision solver','Pixel bounds and held death are checked separately','Art verdict remains below painting'];(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_OK',json.dumps(report))

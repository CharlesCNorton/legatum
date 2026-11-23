"""Audit actual saved mesh/rig/clip data, not visual approval."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/byzantine-heir';report={}
bpy.ops.wm.open_mainfile(filepath=str(M/'byzantine-heir.blend'));rig=bpy.data.objects['Heir MPFB game_engine'];body=bpy.data.objects['Heir MPFB anatomy'];assert len(rig.data.bones)>=50;assert len(body.data.vertices)>10000
report['anatomy']={'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'origin':rig['origin']};report['geometry']={'mesh_count':sum(o.type=='MESH' for o in bpy.context.scene.objects),'projection':json.loads((M/'projection.json').read_text())['method']};report['clips']={}
for name,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/name/'clip.blend'));sc=bpy.context.scene;base=bpy.data.objects['Stationary cream stone'];initial=base.matrix_world.copy();assert sc.frame_end==n
 for f in range(1,n+1):
  sc.frame_set(f);assert base.matrix_world==initial,'Base moved';assert not base.animation_data
  for ob in sc.objects:
   assert min(abs(v) for v in ob.scale)>.001,(name,f,ob.name,'near-zero scale')
 report['clips'][name]={'frames':n,'base_stationary':True,'positive_scale':True}
report['limitations']=['Not a full cloth/body collision solver','Pixel bounds and held death are checked separately','Art verdict remains below painting'];(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_OK',json.dumps(report))

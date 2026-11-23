"""Seat native foot undersides inside their actual sandals, retaining rest pixels."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def fit_foot_undersides():
 sc=bpy.context.scene;body=bpy.data.objects['GEO-MPFB-anatomy'];rig=bpy.data.objects['RIG-eagle-warrior']
 view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1));assert view.z>.1
 count=0
 for v in body.data.vertices:
  groups={body.vertex_groups[g.group].name:g.weight for g in v.groups}
  if not any(n.startswith(('foot_','ball_','toe')) for n in groups):continue
  transforms=[(w,rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n,w in groups.items() if n in rig.pose.bones]
  total=sum(w for w,_ in transforms)
  if not total:continue
  deform=Matrix([[sum(w*m[r][c] for w,m in transforms)/total for c in range(4)] for r in range(4)])
  world=body.matrix_world@deform@v.co
  if world.z>=.237:continue
  world+=view*((.237-world.z)/view.z)
  v.co=deform.inverted()@body.matrix_world.inverted()@world;count+=1
 sc['foot_underside_fit']='native weighted vertices along rest camera rays; minimum .237 m inside sandals'
 bpy.context.view_layer.update()
 print('FOOT_FIT',count,flush=True)

if __name__=='__main__':
 for file in ['surface.blend','plain.blend','eagle-warrior.blend']:
  bpy.ops.wm.open_mainfile(filepath=str(M/file));fit_foot_undersides();save(file)

"""Remove the diagnosis-only duplicate paint mark; the source texture owns it."""
import bpy,os
from pathlib import Path
M=Path(os.environ['ANIM_MASTER'])
for name in ['spearman.blend','unpainted.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(M/name))
 ob=bpy.data.objects.get('Aspis red lambda painted relief')
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(M/name))

# Correct the cached attack's rear shaft framing without changing the rig or cloth.
from mathutils import Vector
path=M/'clips/attack/attack.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
if not sc.get('hoplite_attack_slide_043') and sc.get('attack_slide',.25)<.43:
 names=['Ash dory shaft','Spear bronze ferrule','Leaf spearhead','Iron spear butt']
 objects=[o for o in sc.objects if any(o.name.startswith(n) for n in names)]
 for f in range(sc.frame_start,sc.frame_end+1):
  sc.frame_set(f);t=max(0,min(1,(f-25)/max(1,sc.frame_end-25)))
  raised=[0,.35,.90,1,1,1,1,.85,.30,0][min(9,round(t*9))]
  shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
  direction=(shaft.matrix_world@Vector(pts[-1].co[:3])-shaft.matrix_world@Vector(pts[0].co[:3])).normalized()
  for o in objects:
   mat=o.matrix_world.copy();mat.translation+=direction*.18*raised;o.matrix_world=mat;o.keyframe_insert('location',frame=f)
 sc['hoplite_attack_slide_043']=True
 sc.frame_set(25);bpy.ops.wm.save_as_mainfile(filepath=str(path))

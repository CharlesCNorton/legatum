"""Apply the round-two rigid shaft slide to an already-baked attack cache.

No cloth collider moves: the shaft is not a cloth collider. Future full builds
use the identical formula in animate.py. The original cloth cache stays intact.
"""
import bpy, json, os, hashlib
from pathlib import Path
from mathutils import Vector
M=Path(os.environ['ANIM_MASTER']);path=M/'clips/attack/attack.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
assert sc['source_master_sha256']==hashlib.sha256((M/'spearman.blend').read_bytes()).hexdigest()
previous=sc.get('attack_guard_extra_slide',0);extra=.29-previous
objects=[o for o in sc.objects if o.name.startswith(('Ash dory shaft','Spear bronze ferrule','Leaf spearhead','Iron spear butt'))]
assert not any(m.type=='COLLISION' for o in objects for m in o.modifiers)
cloth=bpy.data.objects['Cloak • simulated wool'].modifiers['Cloth per clip'];assert cloth.point_cache.is_baked
cloth.show_viewport=False
for f in range(1,sc.frame_end+1):
 sc.frame_set(f);t=max(0,min(1,(f-25)/max(1,sc.frame_end-25)))
 raised=[0,.35,.90,1,1,1,1,.85,.30,0][min(9,round(t*9))]
 shaft=bpy.data.objects['Ash dory shaft'];pts=shaft.data.splines[0].points
 direction=(shaft.matrix_world @ Vector(pts[-1].co[:3])-shaft.matrix_world @ Vector(pts[0].co[:3])).normalized()
 for ob in objects:
  mat=ob.matrix_world.copy();mat.translation+=direction*extra*max(0,min(1,(raised-.4)/.4));ob.matrix_world=mat;ob.keyframe_insert('location',frame=f)
cloth.show_viewport=True;sc['attack_guard_extra_slide']=.29;sc.frame_set(25)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
meta=json.loads(path.with_name('clip.json').read_text());meta['attack_guard_extra_slide']=.29;path.with_name('clip.json').write_text(json.dumps(meta,indent=2))
print('ATTACK SHAFT: additional .29m slide only above raised phase .4; cloth unchanged')

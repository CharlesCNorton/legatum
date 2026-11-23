"""Untextured front/three-quarter/side proof, using the requested device."""
import bpy, os, sys, subprocess, json
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).parent))
from render import configure, sha
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';HERE=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(M/'registered.blend'));sc=bpy.context.scene;cam=sc.camera
configure(sc)
files=[]
for name,loc in [('plain',None),('front',(0,-7,3.5)),('side',(7,0,3.5))]:
 if loc is not None:
  cam.location=loc;cam.rotation_euler=(Vector((.12,0,.72))-cam.location).to_track_quat('-Z','Y').to_euler()
 path=M/f'b-{name}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 files.append({'path':path.name,'sha256':sha(path)})
(M/'plain-views.json').write_text(json.dumps({'blend_sha256':sha(M/'registered.blend'),'device':sc.cycles.device,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'files':files},indent=2))
subprocess.run([str(R/'venv/bin/python'),'-c',"import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from review import plain_views_review;plain_views_review()",str(HERE)],check=True)

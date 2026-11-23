"""Untextured front/three-quarter/side proof of full 3D geometry."""
import bpy,os,sys,subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';HERE=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));sc=bpy.context.scene;cam=sc.camera
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.threads_mode='FIXED';sc.render.threads=3
for name,loc in [('front',(0,-7,3.5)),('side',(7,0,3.5))]:
 cam.location=loc;cam.rotation_euler=(Vector((.12,0,.72))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(M/f'b-{name}.png');bpy.ops.render.render(write_still=True)
subprocess.run([str(R/'venv/bin/python'),'-c',"import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from review import sheet,M;sheet('b-plain',[M/'b-plain.png',M/'b-front.png',M/'b-side.png'],['Plain three-quarter','Plain front','Plain side'])",str(HERE)],check=True)

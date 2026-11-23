"""Actual front/top rendered move cycle, plus evaluated foot-axis evidence."""
import bpy, os, sys, json, subprocess
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from render import configure, sha
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer'
blend=M/'clips/move.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene;configure(sc)
cam=sc.camera;rig=bpy.data.objects['RIG-composite-archer'];out=M/'feet';out.mkdir(exist_ok=True)
# Remove torso/equipment occlusion from this diagnostic only; all feet/trouser
# geometry and its original animation remain visible, at real nonzero scale.
for ob in sc.objects:
 if ob.type in ('MESH','CURVE'):
  ob.hide_render=not ob.name.startswith(('GEO-soft leather boots','GEO-patterned trousers','GEO-stationary cream base'))
files=[];samples=[]
for view,loc,target in [('front',(0,-5,1.0),(0,0,.3)),('top',(0,0,5),(0,0,0))]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.5
 for frame in range(1,9):
  sc.frame_set(frame);bpy.context.view_layer.update()
  path=out/f'{view}-{frame:02d}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  files.append({'view':view,'frame':frame,'path':str(path.relative_to(M)),'sha256':sha(path)})
  if view=='top':
   samples.append({'frame':frame,'feet':{s:{'ankle':list(rig.matrix_world @ rig.pose.bones['foot_'+s].head),'toe':list(rig.matrix_world @ rig.pose.bones['ball_'+s].head)} for s in ['l','r']}})
(M/'feet.json').write_text(json.dumps({'blend_sha256':sha(blend),'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'files':files,'foot_positions':samples,'motion':json.loads((M/'clips/move.json').read_text())['motion'],'limitation':'Visual evidence; no automatic no-slide claim'},indent=2))
subprocess.run([str(R/'venv/bin/python'),str(Path(__file__).with_name('feet_sheet.py'))],check=True)

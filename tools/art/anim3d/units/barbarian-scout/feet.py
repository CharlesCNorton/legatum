"""Actual boot geometry over a move cycle, top/front cameras and contact evidence."""
import bpy, os, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout';HERE=Path(__file__).resolve().parent
source=M/'clips/move/move.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;rig=bpy.data.objects['Scout • MPFB rig']
boots=[bpy.data.objects['GEO-closed-boot-'+side] for side in ('l','r')]
for ob in sc.objects:
 if ob.type=='MESH':ob.hide_render=not ob.name.startswith(('GEO-closed-boot','GEO-boot-stitched-welt'))
# Use a plain physical material so source painting cannot disguise foot direction.
mat=bpy.data.materials.new('MAT-feet-diagnostic');mat.diffuse_color=(.20,.10,.04,1);mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.20,.10,.04,1)
for ob in boots:ob.data.materials.clear();ob.data.materials.append(mat)
sc.render.engine='CYCLES';sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.use_denoising=True
if sc.cycles.device=='GPU':
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
 assert any(d.type=='METAL' for d in pref.devices),'No Metal GPU'
 for d in pref.devices:d.use=d.type=='METAL'
res=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=res
out=M/'renders/g-feet';out.mkdir(exist_ok=True,parents=True);records=[]
for view in ('top','front'):
 for i in range(8):
  sc.frame_set(i+1);bpy.context.view_layer.update()
  center=Vector((0,.35,.18));sc.camera.location=(0,.35,5) if view=='top' else (0,-5,.25)
  sc.camera.rotation_euler=(center-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=1.25
  sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
  if view=='top':
   row={'frame':i+1,'feet':{}}
   for side,ob in zip(('l','r'),boots):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();points=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
    toe=rig.matrix_world@rig.pose.bones['ball_'+side].head;heel=rig.matrix_world@rig.pose.bones['foot_'+side].head
    row['feet'][side]={'ankle':list(heel),'toe':list(toe),'direction':list((toe-heel).normalized()),'sole_min_z':min(p.z for p in points)}
   records.append(row)
report={'clip_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'device':sc.cycles.device,'resolution':res,'samples':records,'note':'Diagnostic only: review toe direction, contact height and stance slide; no automatic visual pass.'}
(M/'feet.json').write_text(json.dumps(report,indent=2))
subprocess.run([str(R/'venv/bin/python'),str(HERE/'post.py'),'feet'],check=True)

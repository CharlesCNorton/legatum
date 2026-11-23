"""Render actual front/top feet across the complete source-retargeted walk."""
import bpy,os,json,hashlib,subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/eagle-warrior';out=M/'feet';out.mkdir(exist_ok=True)
source=M/'clips/move.blend';bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=160;sc.render.resolution_percentage=100
if sc.cycles.device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    assert any(d.use for d in prefs.devices),'Metal unavailable'
for ob in sc.objects:
    if ob.type=='MESH':ob.hide_render=not ob.name.startswith(('GEO-MPFB-anatomy','GEO-Sandal','GEO-cream-stone-base'))
cam=sc.camera;rig=bpy.data.objects['RIG-eagle-warrior'];files=[];positions=[]
for view,loc,target in [('front',(0,-5,.38),(0,0,.38)),('top',(0,0,5),(0,0,0))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.65;cam.data.clip_start=4.3 if view=='top' else .1
    for f in range(1,9):
        sc.frame_set(f);p=out/f'{view}-{f:02d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        files.append({'path':str(p.relative_to(M)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if view=='top':positions.append({s:{'ankle':list(rig.matrix_world @ rig.pose.bones['foot_'+s].head),'toe':list(rig.matrix_world @ rig.pose.bones['ball_'+s].head)} for s in ['l','r']})
(M/'feet.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'device':sc.cycles.device,'files':files,'positions':positions},indent=2))
subprocess.run([str(R/'venv/bin/python'),str(Path(__file__).with_name('feet_sheet.py'))],check=True)

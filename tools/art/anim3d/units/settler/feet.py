"""Render actual front/top feet across the complete source-retargeted walk."""
import bpy,os,json,hashlib,subprocess,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';out=M/'feet';out.mkdir(exist_ok=True)
source=M/'clips/move.blend';bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=160;sc.render.resolution_percentage=100
if sc.cycles.device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    assert any(d.use for d in prefs.devices),'Metal unavailable'
for ob in sc.objects:
    if ob.type in {'MESH','CURVE'}:ob.hide_render=ob.name not in {'GEO-MPFB female traveller','GEO-stationary cream base'} and 'sandal' not in ob.name
body=bpy.data.objects['GEO-MPFB female traveller']
# Mask upper anatomy only in this diagnostic scene, retaining weighted feet.
group=body.vertex_groups.new(name='Diagnostic lower legs')
for vertex in body.data.vertices:
    weight=sum(g.weight for g in vertex.groups if body.vertex_groups[g.group].name.startswith(('calf_','foot_','ball_')))
    if weight>.1:group.add([vertex.index],1,'REPLACE')
mask=body.modifiers.new('Diagnostic cutaway','MASK');mask.vertex_group=group.name
cam=sc.camera;rig=bpy.data.objects['RIG-Settler MPFB'];files=[];positions=[]
for view,loc,target in [('front',(0,-5,.65),(0,0,.30)),('top',(0,0,5),(0,0,0))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.45
    for f in range(1,9):
        sc.frame_set(f);p=out/f'{view}-{f:02d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        files.append({'path':str(p.relative_to(M)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if view=='top':positions.append({s:{'ankle':list(rig.matrix_world @ rig.pose.bones['foot_'+s].head),'toe':list(rig.matrix_world @ rig.pose.bones['ball_'+s].head)} for s in ['l','r']})
motion=json.loads((M/'motion-move.json').read_text())
speed=motion['contact']['virtual_ground_m_per_sample'];errors=[]
for side,start,end in [('l',1,4),('r',5,7)]:
    anchor=positions[start][side]['toe']
    for i in range(start,end+1):
        point=positions[i][side]['toe']
        errors.append(math.hypot(point[0]-anchor[0],point[1]-anchor[1]-speed*(i-start)))
assert max(errors)<.005,('stance slides relative to virtual ground',max(errors))
lateral=max(abs(f[s]['toe'][0]-f[s]['ankle'][0]) for f in positions for s in ['l','r'])
assert lateral<.02,('feet turn sideways',lateral)
(M/'feet.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'device':sc.cycles.device,'files':files,'positions':positions,
 'stance_max_residual_m':max(errors),'virtual_ground_m_per_sample':speed,'toe_lateral_max_m':lateral,
 'limits':'In-place walk uses virtual ground speed. Swing toes tuck downward as in the source; no post-retarget foot rotation. Not a complete collision test.'},indent=2))
subprocess.run([str(R/'venv/bin/python'),str(Path(__file__).with_name('feet_sheet.py'))],check=True)

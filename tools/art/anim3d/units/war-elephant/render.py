"""Short resumable stages; CPU preview default, explicit host GPU support."""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector

R=Path(os.environ['ANIM_ROOT']); M=R/'masters/war-elephant'
stage=sys.argv[sys.argv.index('--')+1]
if stage.startswith('e-') or stage in ('d','g'):
    clip=stage[2:] if stage.startswith('e-') else 'move' if stage=='g' else 'attack'
    blend=M/'clips'/clip/(clip+'.blend')
else:
    blend=M/('plain.blend' if stage=='b' else 'war-elephant.blend')
out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
(out/'render.json').unlink(missing_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(blend))
sc=bpy.context.scene
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
device=os.environ.get('CYCLES_DEVICE','CPU')
if sc.render.engine=='CYCLES':
    sc.cycles.device=device
    sc.cycles.samples=int(os.environ.get('SAMPLES','4'))
    sc.cycles.use_denoising=True
    sc.cycles.max_bounces=3
    if device=='GPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='METAL';prefs.get_devices()
        gpu=[d for d in prefs.devices if d.type=='METAL']
        if not gpu:raise RuntimeError('Requested Metal GPU is unavailable')
        for d in prefs.devices:d.use=d in gpu
resolution=int(os.environ.get('RESOLUTION','512'))
sc.render.resolution_x=sc.render.resolution_y=resolution
sc.render.resolution_percentage=100
frames=[]
if stage.startswith('e-'):
    info=json.loads((blend.parent/'clip.json').read_text())
    expected=hashlib.sha256((M/'war-elephant.blend').read_bytes()).hexdigest()
    assert info['source_master_sha256']==expected,'Stale animation master'
    samples=list(range(info['frames']))
elif stage=='d':samples=[0,2,5,8]
elif stage=='g':samples=list(range(8))*2
elif stage=='b':samples=[0,0,0]
else:samples=[0]
for i,frame in enumerate(samples):
    sc.frame_set(frame)
    if stage=='g':
        # Actual evaluated lower limbs, cut away above the knee so the saddle
        # cannot obscure the top view. Never alter the saved animated master.
        body=bpy.data.objects['GEO-Elephant continuous sculpt']
        for ob in sc.objects:
            if ob.type=='MESH':ob.hide_render=True
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(ev)
        import bmesh
        bm=bmesh.new();bm.from_mesh(mesh)
        leg_groups={g.index for g in body.vertex_groups if g.name.startswith(('front.','back.'))}
        leg_vertices={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in leg_groups)>.98}
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in leg_vertices or (body.matrix_world@v.co).z>1.05],context='VERTS')
        bm.to_mesh(mesh);bm.free()
        cut=bpy.data.objects.new('GEO-Feet diagnostic cutaway',mesh)
        sc.collection.objects.link(cut);cut.matrix_world=body.matrix_world.copy()
        if i<8:
            sc.camera.location=(.05,0,9)
            aim=Vector((.05,0,0))
        else:
            sc.camera.location=(9,0,.65)
            aim=Vector((0,0,.65))
        sc.camera.rotation_euler=(aim-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.camera.data.ortho_scale=3.5
    if stage=='b':
        if i:
            sc.camera.location=[(0,-11,4.0),(10,0,4.1)][i-1]
            sc.camera.rotation_euler=(Vector((.19,0,1.65))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
            sc.camera.data.ortho_scale=4.6
    target=out/f'{i:02}.png'
    if stage=='e-death' and i==len(samples)-1:
        shutil.copyfile(out/f'{i-1:02}.png',target)
    else:
        sc.render.filepath=str(target)
        assert sc.camera is not None
        bpy.ops.render.render(write_still=True)
    if stage=='g':
        bpy.data.objects.remove(cut,do_unlink=True)
        bpy.data.meshes.remove(mesh)
    frames.append({'path':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
report={'stage':stage,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
        'engine':sc.render.engine,'device':device,'resolution':resolution,
        'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'frames':frames}
(out/'render.json').write_text(json.dumps(report,indent=2)+'\n')
print('RENDERED',stage,len(frames),resolution,device)

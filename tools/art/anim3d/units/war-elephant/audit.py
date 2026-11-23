"""Check saved rig/geometry, contact, stationary base and exact loop closures."""
import hashlib
import json
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(os.environ['ANIM_ROOT']);M=ROOT/'masters/war-elephant'
report_path=ROOT/'review/3d-v2/war-elephant-audit.json'
report_path.unlink(missing_ok=True)
results={}
bpy.ops.wm.open_mainfile(filepath=str(M/'war-elephant.blend'))
scene=bpy.context.scene
assert scene['projection_method']=='finished surfaces; visibility and facing; camera-only pigment'
uv_error=0
for ob in scene.objects:
    if ob.type!='MESH' or ob.name=='GEO-Stationary cream stone base':continue
    assert ob.data.shape_keys is None,ob.name
    assert all(mod.type=='ARMATURE' for mod in ob.modifiers),ob.name
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    assert len(me.vertices)==len(ob.data.vertices),ob.name
    pixels=[world_to_camera_view(scene,scene.camera,ev.matrix_world@v.co) for v in me.vertices]
    uv=ob.data.uv_layers['Painting projection']
    for i,loop in enumerate(ob.data.loops):
        p=pixels[loop.vertex_index]
        uv_error=max(uv_error,abs(p.x-uv.data[i].uv.x),abs(p.y-uv.data[i].uv.y))
    ev.to_mesh_clear()
    for mat in ob.data.materials:
        assert any(n.type=='LIGHT_PATH' for n in mat.node_tree.nodes),mat.name
assert uv_error<1e-5,('Finished-surface UV drift',uv_error)
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    folder=M/'clips'/clip
    info=json.loads((folder/'clip.json').read_text())
    assert info['source_master_sha256']==hashlib.sha256((M/'war-elephant.blend').read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(folder/(clip+'.blend')))
    sc=bpy.context.scene;rig=bpy.data.objects['RIG-Elephant']
    base=bpy.data.objects['GEO-Stationary cream stone base']
    base_matrix=base.matrix_world.copy();camera=sc.camera.matrix_world.copy()
    assert len(rig.data.bones)==20
    for role in ['Officer','Mahout']:
        human=bpy.data.objects[f'GEO-{role} MPFB anatomy']
        assert len(human.data.vertices)>10000
        assert len(bpy.data.objects[f'RIG-{role} MPFB'].data.bones)==53
        assert any(m.type=='ARMATURE' for m in human.modifiers)
    assert len(json.loads(sc['projected_meshes']))>100
    matrices=[];bounds=[];torso_low=None
    for frame in range(count+int(info['loop'])):
        sc.frame_set(frame);bpy.context.view_layer.update()
        assert base.matrix_world==base_matrix
        assert sc.camera.matrix_world==camera
        assert min(o.scale.length for o in sc.objects)>.01
        matrices.append([tuple(v for row in p.matrix for v in row) for p in rig.pose.bones])
        body=bpy.data.objects['GEO-Elephant continuous sculpt'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        me=body.to_mesh();low=min((body.matrix_world@v.co).z for v in me.vertices)
        if clip=='death' and frame==count-1:
            original=bpy.data.objects['GEO-Elephant continuous sculpt']
            torso=original.vertex_groups['body'].index
            torso_low=min((body.matrix_world@me.vertices[v.index].co).z for v in original.data.vertices
                          if any(g.group==torso and g.weight>.95 for g in v.groups))
        body.to_mesh_clear()
        assert low>=.125,(clip,frame,low)
        bounds.append(round(low,4))
    if info['loop']:assert max(abs(a-b) for left,right in zip(matrices[0],matrices[-1]) for a,b in zip(left,right))<1e-6,clip+' loop does not close'
    if clip=='death':
        assert matrices[-2]==matrices[-1],'Death must hold'
        assert torso_low<.30,('Death torso still hovering',torso_low)
    results[clip]={'frames':count,'min_body_z':min(bounds),'base_and_camera':'fixed','skeleton_bones':len(rig.data.bones),'clip_sha256':hashlib.sha256((folder/(clip+'.blend')).read_bytes()).hexdigest()}
report_path.write_text(json.dumps({'source_master_sha256':hashlib.sha256((M/'war-elephant.blend').read_bytes()).hexdigest(),
    'finished_surface_uv_error':uv_error,'death_torso_min_z':torso_low,'clips':results},indent=2)+'\n')
print('AUDIT',json.dumps(results))

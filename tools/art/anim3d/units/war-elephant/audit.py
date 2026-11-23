"""Check saved rig/geometry, contact, stationary base and exact loop closures."""
import hashlib
import json
import os
from pathlib import Path

import bpy

ROOT=Path(os.environ['ANIM_ROOT']);M=ROOT/'masters/war-elephant'
report_path=ROOT/'review/3d-v2/war-elephant-audit.json'
report_path.unlink(missing_ok=True)
results={}
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
        assert any(m.type=='ARMATURE' for m in human.modifiers)
    assert len(json.loads(sc['projected_meshes']))>100
    matrices=[];bounds=[]
    for frame in range(count+int(info['loop'])):
        sc.frame_set(frame);bpy.context.view_layer.update()
        assert base.matrix_world==base_matrix
        assert sc.camera.matrix_world==camera
        assert min(o.scale.length for o in sc.objects)>.01
        matrices.append([tuple(v for row in p.matrix for v in row) for p in rig.pose.bones])
        body=bpy.data.objects['GEO-Elephant continuous sculpt'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        me=body.to_mesh();low=min((body.matrix_world@v.co).z for v in me.vertices);body.to_mesh_clear()
        assert low>=.125,(clip,frame,low)
        bounds.append(round(low,4))
    if info['loop']:assert max(abs(a-b) for left,right in zip(matrices[0],matrices[-1]) for a,b in zip(left,right))<1e-6,clip+' loop does not close'
    if clip=='death':assert matrices[-2]==matrices[-1],'Death must hold'
    results[clip]={'frames':count,'min_body_z':min(bounds),'base_and_camera':'fixed','skeleton_bones':len(rig.data.bones),'clip_sha256':hashlib.sha256((folder/(clip+'.blend')).read_bytes()).hexdigest()}
report_path.write_text(json.dumps({'source_master_sha256':hashlib.sha256((M/'war-elephant.blend').read_bytes()).hexdigest(),'clips':results},indent=2)+'\n')
print('AUDIT',json.dumps(results))

"""Read the saved Blender master and audit evaluated animation, without a GPU."""
import json
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view

MASTER=Path.home()/'LegatumRuns/anim-pilot/masters/spearman-3d'
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'spearman-3d.blend'))
scene=bpy.context.scene
rig=bpy.data.objects['Spearman · volumetric rig']
base=bpy.data.objects['Cream limestone plinth']
base_matrix=base.matrix_world.copy()
report={'frames':40,'max_joint_gap':0,'max_grip_gap':0,'lowest_meshes':{},'bounds':[1,1,0,0],'out_of_frame':[]}
for frame in range(1,41):
    scene.frame_set(frame)
    assert base.matrix_world==base_matrix
    for side in ('r','l'):
        for a,b in [('thigh','shin'),('shin','foot'),('upper','fore'),('fore','hand')]:
            gap=(rig.pose.bones[a+'_'+side].tail-rig.pose.bones[b+'_'+side].head).length
            report['max_joint_gap']=max(report['max_joint_gap'],gap)
    gap=(rig.pose.bones['hand_r'].head-rig.pose.bones['spear'].head).length
    report['max_grip_gap']=max(report['max_grip_gap'],gap)
    deps=bpy.context.evaluated_depsgraph_get()
    for ob in scene.objects:
        if ob.type!='MESH':continue
        evaluated=ob.evaluated_get(deps)
        mesh=evaluated.to_mesh()
        world=[evaluated.matrix_world @ v.co for v in mesh.vertices]
        low=min(v.z for v in world)
        if low<.135 and ob!=base:
            report['lowest_meshes'][ob.name]=min(report['lowest_meshes'].get(ob.name,999),round(low,4))
        for v in world:
            uv=world_to_camera_view(scene,scene.camera,v)
            if (uv.x<0 or uv.y<0 or uv.x>1 or uv.y>1) and [frame,ob.name] not in report['out_of_frame']:report['out_of_frame'].append([frame,ob.name])
            report['bounds']=[min(report['bounds'][0],uv.x),min(report['bounds'][1],uv.y),max(report['bounds'][2],uv.x),max(report['bounds'][3],uv.y)]
        evaluated.to_mesh_clear()
assert report['max_joint_gap']<.005,report['max_joint_gap']
assert report['max_grip_gap']<.005,report['max_grip_gap']
assert min(report['bounds'][:2])>0 and max(report['bounds'][2:])<1,report['bounds']
assert not report['lowest_meshes'],report['lowest_meshes']
(MASTER/'rig-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

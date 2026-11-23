"""Verify the unsampled loop endpoint and the source contact transfer receipt."""
import hashlib
import json
import os
from pathlib import Path
import bpy

root = Path(os.environ['ANIM_ROOT'])
report = {}
for clip in ('idle','move'):
    blend = root/'masters/horseman-3d/clips'/f'{clip}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    horse = bpy.data.objects['Horse']
    points = []
    for frame in (1,9):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        obj = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        points.append([obj.matrix_world@v.co for v in mesh.vertices])
        obj.to_mesh_clear()
    error = max((a-b).length for a,b in zip(*points))
    assert error<.002,(clip,'Loop fails to close',error)
    report[clip] = {'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'loop_vertex_error_m':error}
    if clip=='move':
        transfer = json.loads(scene['source_contact_transfer'])
        positional = max(o['sole_position_error_m'] for o in transfer['offsets'])
        angular = max(o['foot_rotation_error_rad'] for o in transfer['offsets'])
        assert positional<.005 and angular<.001
        report[clip].update(max_sole_position_error_m=positional,max_foot_rotation_error_rad=angular)
(root/'review/3d-v2/horseman-motion-check.json').write_text(json.dumps(report,indent=2))
print('MOTION_CHECK',json.dumps(report))

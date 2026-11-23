"""Blender regression: sparse Idle must not inherit Walk's IK translations."""
import os
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path('tools/art/anim3d/mounted').resolve()))
from source_pose import reset_pose

root = Path(os.environ['ANIM_ROOT'])
bpy.ops.wm.open_mainfile(filepath=str(root/'masters/horseman-3d/horseman-unpainted.blend'))
arm = bpy.data.objects['AnimalArmature']
scene = bpy.context.scene


def sample(name, frame, reset=True):
    if reset:
        reset_pose(arm)
    action = bpy.data.actions['AnimalArmature|'+name]
    arm.animation_data.action = action
    arm.animation_data.action_slot = action.slots[0]
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {bone.name:bone.matrix.copy() for bone in arm.pose.bones}


def error(a,b):
    return max(abs(a[n][r][c]-b[n][r][c]) for n in a for r in range(4) for c in range(4))


reference = sample('Idle',0)
sample('Walk',19)
contaminated = sample('Idle',0,reset=False)
assert error(reference,contaminated)>1e-5, 'Fixture no longer exposes sparse-channel contamination'
for preceding in ('Walk','Gallop','Death','Idle_HitReact_Left'):
    sample(preceding,7)
    clean = sample('Idle',0)
    assert error(reference,clean)<1e-6, (preceding,error(reference,clean))
print('SOURCE_POSE_OK: four action transitions independent; old contamination reproduced',error(reference,contaminated))

"""Source glTF actions are sparse, so every action starts from its bind pose."""
from mathutils import Matrix


def reset_pose(armature):
    # An omitted channel means bind/default, not the preceding action's value.
    # In particular Idle omits the translations keyed by Walk's IK foot controls.
    for bone in armature.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)

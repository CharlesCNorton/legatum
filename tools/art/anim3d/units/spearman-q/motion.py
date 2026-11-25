"""Small equipment/transition layers over the preserved CC0 library body motion."""
import math
import bpy
from mathutils import Matrix, Vector

AIM = Vector((-.30, -.954, .04)).normalized()
ARM = ['upperarm_r', 'lowerarm_r', 'hand_r']
LEFT = ['upperarm_l', 'lowerarm_l', 'hand_l']
EXTENSION = [0, 0, -.025, -.04, -.02, .16, .36, .39, .39, .35, .28, .19, .10, .035, 0, 0, 0, 0]


def snapshot(rig):
    return {p.name: p.matrix_basis.copy() for p in rig.pose.bones if not p.name.startswith('prop_')}


def restore(rig, values):
    for name, mat in values.items():
        rig.pose.bones[name].matrix_basis = mat.copy()
    bpy.context.view_layer.update()


def mix_pose(rig, values, weight, names=None):
    for name in names or values:
        p = rig.pose.bones[name]
        a, q, scale = p.matrix_basis.decompose()
        b, r, _ = values[name].decompose()
        p.matrix_basis = Matrix.LocRotScale(a.lerp(b, weight), q.slerp(r, weight), scale)
    bpy.context.view_layer.update()


def solve_arm(rig, target, hand_rotation, side="r"):
    """Two-bone IK using the donor elbow side; no stretch or rest-rig edits."""
    upper, lower, hand = [rig.pose.bones[n] for n in (ARM if side=="r" else LEFT)]
    matrices = {p.name: p.matrix.copy() for p in rig.pose.bones}
    shoulder, elbow, wrist = upper.head.copy(), lower.head.copy(), hand.head.copy()
    a, b = (elbow-shoulder).length, (wrist-elbow).length
    axis = target-shoulder
    distance = min(axis.length, a+b-.005)
    axis.normalize()
    target = shoulder+axis*distance
    pole = elbow-shoulder
    pole -= axis*pole.dot(axis)
    if pole.length < .001:
        pole = Vector((-.2, .1, -.5)); pole -= axis*pole.dot(axis)
    pole.normalize()
    along = (a*a-b*b+distance*distance)/(2*distance)
    height = math.sqrt(max(0, a*a-along*along))
    joint = shoulder+axis*along+pole*height
    for p, start, old_end, end in [(upper, shoulder, elbow, joint), (lower, joint, wrist, target)]:
        old_start = matrices[p.name].translation
        delta = (old_end-old_start).rotation_difference(end-start)
        m = (delta @ matrices[p.name].to_quaternion()).to_matrix().to_4x4()
        m.translation = start; matrices[p.name] = m
    m = hand_rotation.to_matrix().to_4x4(); m.translation = target
    matrices[hand.name] = m
    # Convert with explicit evaluated parents; setting p.matrix sequentially is stale.
    for p in [upper, lower, hand]:
        p.matrix_basis = p.bone.convert_local_to_pose(
            matrices[p.name], p.bone.matrix_local, invert=True,
            parent_matrix=matrices[p.parent.name], parent_matrix_local=p.parent.bone.matrix_local)
    bpy.context.view_layer.update()
    return (hand.head-target).length


def prepare(body, donors, actions, pose):
    pose(body, donors['ual2'], actions['ual2', 'Idle_Shield_Loop'], 0)
    guard = snapshot(body)
    pose(body, donors['ual1'], actions['ual1', 'Punch_Cross'], 0)
    carry = snapshot(body)
    restore(body, guard)
    mix_pose(body, carry, 1, ARM)
    hand_start=body.pose.bones['hand_r'].head.copy();hand_start.x-=.12
    solve_arm(body,hand_start,body.pose.bones['hand_r'].matrix.to_quaternion())
    left_start=body.pose.bones['hand_l'].head.copy();left_start.y-=.07
    solve_arm(body,left_start,body.pose.bones['hand_l'].matrix.to_quaternion(),'l')
    seat_body(body)
    guard = snapshot(body)
    body['carry_wrist_offset']=list(body.pose.bones['hand_r'].head-body.pose.bones['upperarm_r'].head)
    body['shield_guard_hand'] = list(body.pose.bones['hand_l'].head)
    body['shield_guard_rotation'] = list(body.pose.bones['hand_l'].matrix.to_quaternion())
    body['shield_guard_normal'] = list(body.pose.bones['lowerarm_l'].matrix.to_3x3().inverted() @ Vector((0,-1,0)))
    return guard, body.pose.bones['hand_r'].matrix.to_quaternion().copy(), body.pose.bones['hand_r'].head.copy()


def layer(body, clip, index, guard, hand_rotation, hand_start):
    if clip in ('idle', 'walk', 'hit'):
        mix_pose(body, guard, 1, ARM+LEFT)
    if clip == 'attack':
        # Preserve the donor's pelvis, spine, step and heel lift. Hold the shield
        # guard as an arm-only layer, with a Cartesian spear target above it.
        mix_pose(body, guard, 1, LEFT)
        blend = [1, .8, .35]+[0]*11+[.3, .7, 1, 1]
        if blend[index]: mix_pose(body, guard, blend[index])
        from mathutils import Quaternion
        solve_arm(body, Vector(body['shield_guard_hand'])+Vector((0,-.10*max(0,EXTENSION[index])/.39,0)), Quaternion(body['shield_guard_rotation']), 'l')
        fore=body.pose.bones['lowerarm_l']
        m=fore.matrix.copy();axis=m.col[1].xyz.normalized()
        normal=m.to_3x3() @ Vector(body['shield_guard_normal'])
        desired=Vector((0,-1,0));normal-=axis*normal.dot(axis);desired-=axis*desired.dot(axis)
        normal.normalize();desired.normalize()
        angle=math.atan2(axis.dot(normal.cross(desired)),normal.dot(desired))
        rot=Quaternion(axis,angle) @ m.to_quaternion()
        corrected=rot.to_matrix().to_4x4();corrected.translation=m.translation
        fore.matrix_basis=fore.bone.convert_local_to_pose(corrected,fore.bone.matrix_local,invert=True,parent_matrix=fore.parent.matrix,parent_matrix_local=fore.parent.bone.matrix_local)
        bpy.context.view_layer.update()
        return solve_arm(body, hand_start+AIM*EXTENSION[index], hand_rotation)
    if clip == 'hit':
        # Hit_Chest is a recoil, not a complete recover-to-idle action.
        mix_pose(body, guard, [1, .15, 0, 0, .2, .55, .85, 1][index])
    if clip == 'death':
        if index < 3:
            mix_pose(body, guard, [1, .65, .2][index])
            mix_pose(body,guard,1,ARM+LEFT)
        root=body.pose.bones['root'];m=root.matrix.copy()
        t=min(1,max(0,(index-3)/6));m.translation.y-=.66*t*t*(3-2*t)
        root.matrix=m;bpy.context.view_layer.update()
    if clip in ('idle','walk','hit'):
        return solve_arm(body,body.pose.bones['upperarm_r'].head+Vector(body['carry_wrist_offset']),hand_rotation)
    return 0.0


def release_props(body, count):
    """Release the equipment after recoil, then land it outside the body footprint.

    The meshes stay rigid socket children. The nondeforming sockets compensate
    their old parent after release; no mesh deformation or zero scale is used.
    """
    from mathutils import Quaternion
    scene=bpy.context.scene
    starts={}
    scene.frame_set(3);bpy.context.view_layer.update()
    for n in ('prop_shield_grip','prop_spear_grip'):
        starts[n]=body.pose.bones[n].matrix.copy()
    shield=bpy.data.objects['GEO-Rigid bronze shield']
    shaft=bpy.data.objects['GEO-Rigid spear shaft']
    offsets={n:body.pose.bones[n].matrix.inverted() @ body.matrix_world.inverted() @ ob.matrix_world
             for n,ob in [('prop_shield_grip',shield),('prop_spear_grip',shaft)]}
    goals={}
    for n in starts:
        if 'shield' in n:
            world=Matrix.Rotation(-math.pi/2,4,'X');world.translation=Vector((.86,-.15,.175))
        else:
            world=Matrix.Rotation(math.pi/2,4,'Y') @ Matrix.Rotation(math.pi/2,4,'X');world.translation=Vector((-.72,-.02,.21))
        goals[n]=body.matrix_world.inverted() @ world @ offsets[n].inverted()
    for frame in range(1,count+1):
        scene.frame_set(frame);bpy.context.view_layer.update()
        t=min(1,max(0,(frame-3)/6));ease=1-(1-t)**3
        for n in starts:
            p=body.pose.bones[n]
            if frame<=3:
                p.matrix_basis=Matrix.Identity(4)
            else:
                a,q,scale=starts[n].decompose();b,r,_=goals[n].decompose()
                loc=a.lerp(b,ease);loc.z=a.z+(b.z-a.z)*t*t
                mat=Matrix.LocRotScale(loc,q.slerp(r,t*t),scale)
                p.matrix_basis=p.bone.convert_local_to_pose(mat,p.bone.matrix_local,invert=True,parent_matrix=p.parent.matrix,parent_matrix_local=p.parent.bone.matrix_local)
            bpy.context.view_layer.update()
            if frame>3:
                objects=[o for o in scene.objects if o.type=='MESH' and o.parent==body and o.parent_bone==n and not o.hide_render]
                lowest=min((o.matrix_world @ v.co).z for o in objects for v in o.data.vertices)
                if lowest<.108 or t==1:
                    mat=p.matrix.copy();mat.translation.z+=.108-lowest
                    p.matrix_basis=p.bone.convert_local_to_pose(mat,p.bone.matrix_local,invert=True,parent_matrix=p.parent.matrix,parent_matrix_local=p.parent.bone.matrix_local)
            p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame)


def seat_body(body):
    """Seat evaluated original skin on the shared 0.105 m stone, never scale it."""
    ob=bpy.data.objects['SuperHero_Male']
    deps=bpy.context.evaluated_depsgraph_get();evaluated=ob.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    lowest=min((ob.matrix_world @ v.co).z for v in mesh.vertices)
    evaluated.to_mesh_clear()
    for item in bpy.context.scene.objects:
        if item.type=='MESH' and item.name.startswith('KIT ') and item.get('look_part') not in ('shield','crest','skirt'):
            lowest=min(lowest,min((item.matrix_world @ v.co).z for v in item.data.vertices))
    if lowest<.107:
        p=body.pose.bones['root'];m=p.matrix.copy();m.translation.z+=.107-lowest
        p.matrix=m;bpy.context.view_layer.update()

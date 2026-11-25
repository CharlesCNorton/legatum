"""Small anatomical corrections over the native 0 A.D. animation, in Blender."""
import math
import bpy
from mathutils import Matrix, Vector, Quaternion


def solve_limb(upper, lower, end, target):
    """Two-bone position solve; retain the source bend plane and bone lengths."""
    bpy.context.view_layer.update()
    root, elbow, tip = [p.matrix.translation.copy() for p in (upper, lower, end)]
    a, b = (elbow-root).length, (tip-elbow).length
    reach = target-root; distance = min(reach.length, a+b-.001)
    direction = reach.normalized(); target = root+direction*distance
    pole = elbow-root; pole = (pole-direction*pole.dot(direction)).normalized()
    along = (a*a-b*b+distance*distance)/(2*distance)
    solved_elbow = root+direction*along+pole*math.sqrt(max(0, a*a-along*along))
    for joint, endpoint, goal in [(upper, elbow, solved_elbow), (lower, None, target)]:
        bpy.context.view_layer.update()
        pivot = joint.matrix.translation.copy()
        endpoint = endpoint if endpoint is not None else end.matrix.translation.copy()
        rotation = (endpoint-pivot).rotation_difference(goal-pivot).to_matrix().to_4x4()
        joint.matrix = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot) @ joint.matrix
    bpy.context.view_layer.update()


def rotate_about_joint(joint, axis, degrees):
    bpy.context.view_layer.update()
    pivot = joint.matrix.translation.copy()
    joint.matrix = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees),4,axis)
                    @ Matrix.Translation(-pivot) @ joint.matrix)
    bpy.context.view_layer.update()


def envelope(t, keys):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if t <= b:
            u=max(0,min(1,(t-a)/(b-a)));u=u*u*(3-2*u)
            return x+(y-x)*u
    return keys[-1][1]


def attack_weight(rig, phase, planted_feet):
    # The donor already contributes about 7 cm; add 6 cm to reach ~13 cm total.
    drive=envelope(phase,[(0,0),(.30,-.008),(.38,-.008),(.55,.06),(.66,.055),(1,0)])
    hip=rig.pose.bones['hip'];m=hip.matrix.copy();m.translation.y-=drive/rig.scale.x;hip.matrix=m
    bpy.context.view_layer.update()
    # Lower the pelvis only as much as needed to retain a bent, reachable knee
    # over both planted ankles. Never stretch the lower leg to force the plant.
    lower_by=0
    for side,target in planted_feet.items():
        root,knee,ankle=[rig.pose.bones[n+'_'+side].matrix.translation.copy() for n in ('thigh','leg','foot')]
        reach=(knee-root).length+(ankle-knee).length-.01/rig.scale.x
        delta=root-target.translation
        allowed_vertical=math.sqrt(max(0,reach*reach-delta.x*delta.x-delta.y*delta.y))
        lower_by=max(lower_by,delta.z-allowed_vertical)
    m=hip.matrix.copy();m.translation.z-=lower_by;hip.matrix=m
    bpy.context.view_layer.update()
    for side,target in planted_feet.items():
        upper,lower,end=[rig.pose.bones[n+'_'+side] for n in ('thigh','leg','foot')]
        solve_limb(upper,lower,end,target.translation)
        end.matrix=target.copy()
        bpy.context.view_layer.update()
    rotate_about_joint(rig.pose.bones['spine'],'X',4*max(0,drive)/.06)


def hit_recoil(rig, phase):
    # Peak on exported frame 5 (0.167 s), settle by frame 20; five held keys.
    recoil=envelope(phase,[(0,0),(5/24,1),(8/24,.82),(20/24,0),(1,0)])
    rotate_about_joint(rig.pose.bones['spine'],'X',-14*recoil)
    rotate_about_joint(rig.pose.bones['neck'],'X',-3*recoil)


def open_idle_guard(rig):
    """Move the carrying hand back/out with a two-bone solve, at fixed lengths.

    The shield inherits the forearm rotation. Its socket, grip and rigid weights
    are untouched; no prop-only translation can pull it away from the arm.
    """
    bpy.context.view_layer.update()
    arm, forearm, hand = [rig.pose.bones[n] for n in ('arm_L', 'forearm_L', 'hand_L')]
    target = hand.matrix.translation + Vector((.10, .22, -.05)) / rig.scale.x
    solve_limb(arm,forearm,hand,target)

    # Supinate about the forearm's own axis. The wrist position is preserved;
    # the shield turns outward with the arm rather than covering the cuirass.
    pivot = forearm.matrix.translation.copy()
    axis = (hand.matrix.translation-pivot).normalized()
    turn = Quaternion(axis, math.radians(-35)).to_matrix().to_4x4()
    forearm.matrix = Matrix.Translation(pivot) @ turn @ Matrix.Translation(-pivot) @ forearm.matrix
    bpy.context.view_layer.update()


def attack_time(t):
    """Monotone cubic time warp: measured takeback, fast drive, slower recovery."""
    xs = (0., .35, .53, .66, 1.)
    ys = (0., .30, .58, .70, 1.)
    slopes = [(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(4)]
    tangents = [slopes[0]] + [2*a*b/(a+b) for a,b in zip(slopes,slopes[1:])] + [slopes[-1]]
    i = next((i for i in range(4) if t <= xs[i+1]), 3)
    span = xs[i+1]-xs[i]; u = (t-xs[i])/span
    return ((2*u**3-3*u**2+1)*ys[i] + (u**3-2*u**2+u)*span*tangents[i]
            + (-2*u**3+3*u**2)*ys[i+1] + (u**3-u**2)*span*tangents[i+1])

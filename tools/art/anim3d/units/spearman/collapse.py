"""Spearman death: an authored, weighted collapse.

The open Death01 clip flips onto its back along the camera's depth axis with
both arms up and ends off the base (round 9/10 review). This choreography is
therefore keyed: recoil, knees give, drop to the knees, topple onto the spear
side and settle lying ACROSS the stone with the aspis still strapped to the
forearm. Channels are plain numbers interpolated between keys; limbs are solved
with the same two-bone helper as the weapon attack. Metres and radians.

Frames: body axes are armature-local (X = his left, -Y = forward, Z = up).
`pelvis` is the pelvis joint in world space; `rot` is (roll about the world X
axis after the fall, fall about Y, yaw about Z). Leg targets are ankle
positions in armature space; while `plant` is 1 they come from `ankle_*_w`
world positions instead (feet stay where they stood as the knees give). Arm
targets are in the neutral chest's frame and are carried by the bent spine.
"""
import math
from mathutils import Vector, Quaternion, Matrix

PELVIS = Vector((0, -.006, .913))        # pelvis joint, armature space
NEUTRAL_PELVIS_W = Vector((.065, -.006, .998))

KEYS = [
    # 0 guard
    (0.00, dict(pelvis=(.065, -.006, .998), rot=(0, 0, 0), spine=(0, 0, 0), head=(0, 0, 0),
                plant=1, ankle_l_w=(.25, .150, .191), ankle_r_w=(-.272, -.073, .191),
                ankle_l=(.185, .15, .106), ankle_r=(-.337, -.073, .106),
                knee_l=(.42, -.50, .48), knee_r=(-.40, -.20, .48), foot=(0, 0),
                hand_l=(.29, -.34, 1.12), elbow_l=(.53, -.10, 1.13),
                hand_r=(-.432, -.02, 1.197), elbow_r=(-.48, -.12, 1.08), ease='out')),
    # 1 struck: chest and head thrown back, shield knocked in, weight on the heels
    (0.09, dict(pelvis=(.065, .055, .985), rot=(0, 0, 0), spine=(-.34, -.05, .10), head=(-.42, 0, .10),
                plant=1, ankle_l_w=(.25, .150, .191), ankle_r_w=(-.272, -.073, .191),
                ankle_l=(.185, .15, .106), ankle_r=(-.337, -.073, .106),
                knee_l=(.42, -.50, .48), knee_r=(-.40, -.20, .48), foot=(0, 0),
                hand_l=(.24, -.27, 1.20), elbow_l=(.56, -.02, 1.10),
                hand_r=(-.50, -.10, 1.16), elbow_r=(-.56, .05, 1.05), ease='in')),
    # 2 knees give: pelvis drops, torso folds over the belt, head hangs
    (0.21, dict(pelvis=(.10, -.02, .74), rot=(0, 0, 0), spine=(.34, -.06, 0), head=(.30, -.05, 0),
                plant=1, ankle_l_w=(.25, .170, .25), ankle_r_w=(-.272, .020, .26),
                ankle_l=(.185, .15, .106), ankle_r=(-.337, -.073, .106),
                knee_l=(.42, -.80, .30), knee_r=(-.50, -.80, .30), foot=(.50, .55),
                hand_l=(.30, -.33, 1.08), elbow_l=(.55, -.08, 1.10),
                hand_r=(-.44, -.16, .96), elbow_r=(-.60, .05, 1.10), ease='in')),
    # 3 on the knees: shins down, toes dragged back, torso sagging to the spear side
    (0.32, dict(pelvis=(.16, .02, .50), rot=(-.04, -.10, 0), spine=(.42, -.16, 0), head=(.42, -.18, 0),
                plant=1, ankle_l_w=(.26, .27, .215), ankle_r_w=(-.28, .25, .24),
                ankle_l=(.22, .26, .62), ankle_r=(-.32, .26, .645),
                knee_l=(.30, -2.0, .30), knee_r=(-.40, -2.0, .30), foot=(2.6, 2.6),
                hand_l=(.30, -.32, 1.06), elbow_l=(.56, -.08, 1.08),
                hand_r=(-.40, -.14, .78), elbow_r=(-.58, .06, 1.08), ease='in')),
    # 4 toppling over the spear-side knee; head and shield lag behind the hips
    (0.50, dict(pelvis=(.22, .06, .46), rot=(-.15, -.62, 0), spine=(.30, .16, 0), head=(.25, .25, 0),
                plant=0, ankle_l_w=(.26, .27, .215), ankle_r_w=(-.28, .25, .24),
                ankle_l=(.18, .22, .62), ankle_r=(-.28, .24, .63),
                knee_l=(.20, -2.0, .40), knee_r=(-.40, -2.0, .40), foot=(2.6, 2.6),
                hand_l=(.28, -.30, 1.02), elbow_l=(.60, -.10, 1.06),
                hand_r=(-.42, -.24, 1.02), elbow_r=(-.62, .02, 1.12),
                arm_w=0, hand_l_w=(.28, -.02, .50), elbow_l_w=(.0, .30, .90),
                hand_r_w=(-.25, -.45, .14), elbow_r_w=(-.55, -.25, .10),
                shield_w=0, shield_arc=.06, ease='in')),
    # 5 shoulder and hip strike the stone; the arm goes limp and the aspis slips off it
    (0.70, dict(pelvis=(.28, .10, .34), rot=(-.35, -1.25, 0), spine=(.18, .12, 0), head=(.10, .20, -.2),
                plant=0, ankle_l_w=(.26, .27, .215), ankle_r_w=(-.28, .25, .24),
                ankle_l=(.06, .14, .60), ankle_r=(-.125, .06, .55),
                knee_l=(.15, -2.0, .50), knee_r=(-.25, -2.0, .60), foot=(2.0, 1.9),
                hand_l=(.16, -.34, 1.06), elbow_l=(.60, -.30, 1.10),
                hand_r=(-.40, -.30, 1.25), elbow_r=(-.60, -.30, 1.00),
                arm_w=.6, hand_l_w=(.28, -.02, .50), elbow_l_w=(.0, .30, .90),
                hand_r_w=(-.25, -.45, .14), elbow_r_w=(-.55, -.25, .10),
                shield_w=.5, shield_arc=.06, ease='out')),
    # 6 settles on his side facing out, knees drawn up; the aspis tips back against them
    (0.86, dict(pelvis=(.30, .12, .31), rot=(-.50, -1.40, 0), spine=(.15, .0, 0), head=(.05, -.10, -.45),
                plant=0, ankle_l_w=(.26, .27, .215), ankle_r_w=(-.28, .25, .24),
                ankle_l=(-.02, .10, .56), ankle_r=(-.125, -.08, .58),
                knee_l=(.125, -2.0, .60), knee_r=(-.125, -2.0, .80), foot=(1.4, 1.35),
                hand_l=(-.12, -.32, .98), elbow_l=(.60, -.30, 1.10),
                hand_r=(-.50, -.38, 1.20), elbow_r=(-.45, -.25, 1.60),
                arm_w=1, hand_l_w=(.28, -.02, .50), elbow_l_w=(.0, .30, .90),
                hand_r_w=(-.25, -.45, .14), elbow_r_w=(-.55, -.25, .10),
                shield_w=.92, shield_arc=.06, ease='out')),
    # 7 at rest (held)
    (0.96, dict(pelvis=(.30, .12, .30), rot=(-.55, -1.40, 0), spine=(.15, .0, 0), head=(.0, .0, -.5),
                plant=0, ankle_l_w=(.26, .27, .215), ankle_r_w=(-.28, .25, .24),
                ankle_l=(-.02, .10, .56), ankle_r=(-.125, -.08, .58),
                knee_l=(.125, -2.0, .60), knee_r=(-.125, -2.0, .80), foot=(1.3, 1.3),
                hand_l=(-.12, -.32, .98), elbow_l=(.60, -.30, 1.10),
                hand_r=(-.50, -.38, 1.20), elbow_r=(-.45, -.25, 1.60),
                arm_w=1, hand_l_w=(.28, -.02, .50), elbow_l_w=(.0, .30, .90),
                hand_r_w=(-.25, -.45, .14), elbow_r_w=(-.55, -.25, .10),
                shield_w=1, ease='out')),
]


def quaternion(rot):
    roll, fall, yaw = rot[:3]
    # Optional fourth value: a turn about the world vertical after the fall
    # (swings the lying body round on the stone).
    spin = rot[3] if len(rot) > 3 else 0
    return (Quaternion((0, 0, 1), spin) @ Quaternion((1, 0, 0), roll)
            @ Quaternion((0, 1, 0), fall) @ Quaternion((0, 0, 1), yaw))


GUARD = KEYS[0][1]
# Hit reaction, four delivered samples at phases 0, 1/3, 2/3, 1. The open
# Hit_Chest crouched forward and read as a shrug at 160 px; this is a keyed
# blow to the shield: chest and head snap back over planted feet, the aspis is
# driven up into the body and the spear rocks, then he catches himself low and
# returns to the exact guard (entry and exit match idle for clean transitions).
HIT_KEYS = [
    (0.00, GUARD),
    (0.30, dict(GUARD, pelvis=(.065, .085, .955), spine=(-.46, .06, .16), head=(-.50, 0, .12),
                hand_l=(.275, -.31, 1.17), elbow_l=(.55, -.08, 1.135),
                hand_r=(-.50, -.02, 1.24), elbow_r=(-.60, .06, 1.06), spear=(-.16, .06), ease='out')),
    (0.66, dict(GUARD, pelvis=(.065, .03, .962), spine=(.09, -.03, -.05), head=(.08, 0, 0),
                hand_l=(.31, -.37, 1.07), elbow_l=(.55, -.10, 1.10),
                hand_r=(-.44, -.05, 1.17), elbow_r=(-.50, -.10, 1.06), spear=(.07, -.02), ease='smooth')),
    (1.00, dict(GUARD, ease='smooth')),
]


def sample(t, KEYS=KEYS):
    """Interpolated channel values at clip phase t (0..1)."""
    t = max(0., min(1., t))
    if t >= KEYS[-1][0]:
        a = b = KEYS[-1]; u = 0.
    else:
        i = max(k for k in range(len(KEYS)-1) if KEYS[k][0] <= t)
        a, b = KEYS[i], KEYS[i+1]
        u = (t-a[0])/(b[0]-a[0])
        ease = b[1]['ease']
        # 'in' accelerates like a fall; 'out' decelerates into a rest.
        u = u*u*(.4+.6*u) if ease == 'in' else 1-(1-u)**2 if ease == 'out' else u*u*(3-2*u)
    out = {}
    for name in set(a[1]) | set(b[1]):
        if name == 'ease':
            continue
        # A channel missing from one key takes the other key's value; weights
        # (`*_w`) and the hit's spear rock default to zero.
        zero = 0. if name.endswith('_w') and name in ('arm_w', 'shield_w') else (0, 0) if name == 'spear' else None
        value = a[1].get(name, zero if zero is not None else b[1].get(name))
        other = b[1].get(name, zero if zero is not None else a[1].get(name))
        if name == 'rot':
            out[name] = quaternion(value).slerp(quaternion(other), u)
        elif isinstance(value, tuple):
            out[name] = Vector(value).lerp(Vector(other), u)
        else:
            out[name] = value+(other-value)*u
    return out


# Where the aspis comes to rest once the dying arm slides out of the forearm
# band: standing on its rim on the stone, leaning back against his drawn-up
# knees with the face toward the camera. World space; centre of the shell and
# the outward facing.
SHIELD_REST = (Vector((.40, -.14, .53)), Vector((.39, -.77, .50)))
_shield_points = {}


def place_shield(c, rig):
    """Blend the aspis from the forearm to SHIELD_REST by `shield_w` (0..1).

    Call again after anything moves the rig (the floor fit), so the rest
    stays where it was authored in the world."""
    import bpy
    weight = c.get('shield_w', 0.)
    if weight <= 1e-4:
        return
    shield = bpy.data.objects['Aspis control']
    if 'centre' not in _shield_points:
        inverse = shield.matrix_world.inverted()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        points = []
        for ob in shield.children:
            evaluated = ob.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            points.extend(inverse @ ob.matrix_world @ v.co for v in mesh.vertices)
            evaluated.to_mesh_clear()
        _shield_points['centre'] = sum(points, Vector())/len(points)
    matrix = shield.matrix_world.copy()
    location, rotation, scale = matrix.decompose()
    centre = matrix @ _shield_points['centre']
    normal = rotation @ Vector((0, -1, 0))
    rest_centre, rest_normal = SHIELD_REST
    turned = normal.rotation_difference(rest_normal.normalized()) @ rotation
    rotation = rotation.slerp(turned, weight)
    centre = centre.lerp(rest_centre, weight)
    # Slipping off the arm it drops rim-first: a small arc keeps the rim out
    # of his thigh on the way down.
    centre.z += c.get('shield_arc', 0.)*math.sin(math.pi*weight)
    matrix = Matrix.LocRotScale(Vector(), rotation, scale)
    matrix.translation = centre-matrix.to_3x3() @ _shield_points['centre']
    shield.matrix_world = matrix
    bpy.context.view_layer.update()


def apply(t, rig, neutral_world, limb, turn, keys=KEYS):
    """Pose the rig object and bones for phase t. Call after reset()."""
    import bpy
    c = sample(t, keys)
    rig.rotation_mode = 'QUATERNION'
    rig.rotation_quaternion = c['rot']
    rig.location = c['pelvis']-c['rot'] @ PELVIS
    bpy.context.view_layer.update()
    for name in ['spine_01', 'spine_02', 'spine_03']:
        for axis, angle in zip('XYZ', c['spine']):
            if abs(angle) > 1e-6:
                turn(name, axis, angle/3)
    for name in ['neck_01', 'head']:
        for axis, angle in zip('XYZ', c['head']):
            if abs(angle) > 1e-6:
                turn(name, axis, angle/2)
    inverse = rig.matrix_world.inverted()
    for side, sign in [('l', 1), ('r', -1)]:
        target = c['ankle_'+side].lerp(inverse @ c['ankle_'+side+'_w'], c['plant'])
        limb('thigh_'+side, 'calf_'+side, target, c['knee_'+side])
        pitch = c['foot'][0 if side == 'l' else 1]
        # Absolute foot pitch from the flat neutral sole (armature space), so a
        # tilting shin does not drive the toes into the stone.
        foot = rig.pose.bones['foot_'+side]
        matrix = Matrix.Rotation(pitch, 4, 'X') @ neutral_world['foot_'+side]
        matrix.translation = foot.head
        foot.matrix = matrix
        bpy.context.view_layer.update()
    carry = rig.pose.bones['spine_03'].matrix @ neutral_world['spine_03'].inverted()
    reach = c.get('arm_w', 0.)
    for side in ['l', 'r']:
        hand, elbow = carry @ c['hand_'+side], carry @ c['elbow_'+side]
        if reach > 0:
            # Limp arms come to rest on things in the world (stone, hip), not
            # at a place in the chest's frame.
            hand = hand.lerp(inverse @ c['hand_'+side+'_w'], reach)
            elbow = elbow.lerp(inverse @ c['elbow_'+side+'_w'], reach)
        limb('upperarm_'+side, 'lowerarm_'+side, hand, elbow)
    place_shield(c, rig)
    if 'spear' in c:
        # The grip keeps its guard orientation in armature space (the spear is
        # carried by the hand), plus a small rock about X/Y.
        hand = rig.pose.bones['hand_r']
        matrix = (Matrix.Rotation(c['spear'][0], 4, 'X') @ Matrix.Rotation(c['spear'][1], 4, 'Y')
                  @ neutral_world['hand_r'])
        matrix.translation = hand.head
        hand.matrix = matrix
    bpy.context.view_layer.update()
    global LAST
    LAST = c
    return c

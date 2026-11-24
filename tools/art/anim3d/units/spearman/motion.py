"""Spearman timing and passive equipment response; no anatomy/material edits.

Source actions own human joint motion except for the weapon-specific attack.
Secondary motion is a damped inertial response to the evaluated carrier, not a
second hand-keyed performance. Units are metres, seconds and radians.
"""
import math

# Complete donor-space attenuation; never alter target foot orientation.
WALK_INFLUENCE = .90


def walk_calibration_axis(target, anatomical_axis, donor_axis):
    """Match donor leg axes; track width is a separate constant IK offset."""
    return donor_axis


def blend_walk_source(source, carry):
    """Carry the idle arms on the walking donor's moving torso, before retarget."""
    for name in ['DEF-hips', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003']:
        carry.pose.bones[name].rotation_quaternion = carry.pose.bones[name].rotation_quaternion.slerp(
            source.pose.bones[name].rotation_quaternion, .50)


def walk_offsets(corrections):
    """Widen ankle tracks in travel space; no camera-dependent or toe rotation."""
    from mathutils import Vector
    return {side: offset+Vector((.085 if side == 'l' else -.085, 0, 0))
            for side, offset in corrections.items()}


def curve(phase, values):
    """Bounded C1 Hermite interpolation, with zero slope only at extrema.

Unlike nearest-pose indexing this gives cloth a continuous 24Hz driver. Harmonic
slopes preserve monotonic segments and cannot overshoot weapon clearance keys.
"""
    x = max(0., min(1., phase))*(len(values)-1)
    i = min(len(values)-2, int(x))
    t = x-i
    slopes = [0.]
    for a, b, c in zip(values, values[1:], values[2:]):
        left, right = b-a, c-b
        slopes.append(2*left*right/(left+right) if left*right > 0 else 0.)
    slopes.append(0.)
    return ((2*t**3-3*t*t+1)*values[i] + (t**3-2*t*t+t)*slopes[i]
            + (-2*t**3+3*t*t)*values[i+1] + (t**3-t*t)*slopes[i+1])


def attack_channels(phase):
    return (curve(phase, [0, -.10, -.06, .38, 1, .83, .35, .12, .02, 0]),
            curve(phase, [0, .25, .85, 1, 1, .99, .88, .55, .12, 0]))


def source_phase(clip, phase):
    if clip == 'hit':
        return min(1., phase*3.)
    if clip == 'death':
        # Sample the knee yield and torso descent separately, then traverse the
        # donor's brief feet-up recoil between delivery samples. No new poses.
        # Reserve the final quarter for contact settling and an exact hold.
        return curve(phase, [0, .14, .27, .35, .395, .43, .49, .63, 1, 1])
    return phase


def hit_envelope(phase):
    t = max(0., min(1., (phase-.30)/.70))
    return 1-t*t*(3-2*t)


class Spring:
    """Stable substepped spring forced by carrier acceleration; bounded offset."""
    def __init__(self, frequency, damping, gain, limit):
        self.omega = 2*math.pi*frequency
        self.damping, self.gain, self.limit = damping, gain, limit
        self.offset = self.velocity = 0.
        self.previous = None
        self.previous_velocity = 0.
        self.maximum = 0.

    def step(self, carrier, dt=1/24):
        if self.previous is None:
            self.previous = carrier
        velocity = (carrier-self.previous)/dt
        acceleration = (velocity-self.previous_velocity)/dt
        self.previous, self.previous_velocity = carrier, velocity
        for _ in range(8):
            h = dt/8
            force = (-self.omega**2*self.offset
                     - 2*self.damping*self.omega*self.velocity
                     - self.gain*acceleration)
            self.velocity += force*h
            self.offset += self.velocity*h
            if abs(self.offset) > self.limit:
                self.offset = math.copysign(self.limit, self.offset)
                self.velocity = 0.
        self.maximum = max(self.maximum, abs(self.offset))
        return self.offset


class EquipmentResponse:
    """Keep crest roots fixed; flex tips and lag the strapped shield slightly."""
    def __init__(self, rig, shield, clip):
        import bpy
        from mathutils import Vector
        self.rig, self.shield, self.clip = rig, shield, clip
        self.crest = []
        self.hair_spring = (Spring(3.6, .95, .35, .016) if clip == 'death'
                            else Spring(4.2, .48, .7, .026))
        self.shield_spring = (Spring(3.0, 1., .025, math.radians(1)) if clip == 'death'
                              else Spring(3.0, .72, .06, math.radians(3)))
        if clip in ['idle', 'move', 'hit']:
            return
        anchors = []
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH' and ob.name.startswith('Horsehair crest tuft'):
                # Solidified four-corner tuft: first two corners attach to the
                # saddle, next two are tips. Height alone reverses the bend on
                # the back of the crest where the free tip points downward.
                points = [ob.matrix_world @ v.co for v in ob.data.vertices]
                root = (points[0]+points[1])*.5
                tip = (points[2]+points[3])*.5
                anchors.append((root, tip))
        for ob in bpy.context.scene.objects:
            if ob.type != 'MESH' or not ob.name.startswith(('Horsehair crest tuft', 'Horsehair painted fibre')):
                continue
            # Finished mesh and UVs remain untouched at Basis. Squared length
            # weights pin the tuft's root while its free tips bend up to 26mm.
            points = [ob.matrix_world @ v.co for v in ob.data.vertices]
            center = sum(points, Vector())/len(points)
            root, tip = min(anchors, key=lambda pair: (center-(pair[0]+pair[1])*.5).length)
            axis = tip-root
            ob.shape_key_add(name='Basis')
            bend = ob.shape_key_add(name='Carrier inertia')
            bend.slider_min = -1
            direction = ob.matrix_world.to_3x3().inverted() @ Vector((0, 1, 0))
            for v, point in zip(bend.data, points):
                weight = max(0., min(1., (point-root).dot(axis)/axis.length_squared))**2
                v.co += direction*.026*weight
            self.crest.append(bend)

    def key(self, frame, phase):
        import bpy
        from mathutils import Matrix, Vector
        if self.clip in ['idle', 'move', 'hit']:
            return
        head = self.rig.matrix_world @ self.rig.pose.bones['head'].matrix
        # A point above the attachment senses both translation and head rotation.
        carrier = head @ Vector((0, .20, 0))
        flex = self.hair_spring.step(carrier.y)
        # Attack/hit return to exact guard; settle secondary response first.
        envelope = 1.
        if self.clip in ['attack', 'hit']:
            t = max(0., min(1., (phase-.72)/.28))
            envelope = 1-t*t*(3-2*t)
        for bend in self.crest:
            bend.value = flex/.026*envelope
            bend.keyframe_insert('value', frame=frame)
        if self.shield is not None:
            matrix = self.shield.matrix_world.copy()
            angle = self.shield_spring.step(matrix.translation.y)*envelope
            # Released equipment has its own contact trajectory. A strapped
            # aspis pivots around its grip, never disconnecting from the arm.
            if self.clip != 'death' or phase <= .30:
                pivot = self.rig.matrix_world @ self.rig.pose.bones['lowerarm_l'].tail
                self.shield.matrix_world = (Matrix.Translation(pivot)
                    @ Matrix.Rotation(angle, 4, 'X') @ Matrix.Translation(-pivot) @ matrix)
        bpy.context.view_layer.update()

    def report(self):
        return {'method': 'carrier acceleration, damped passive spring',
                'max_crest_tip_deflection_m': self.hair_spring.maximum,
                'max_shield_lag_radians': self.shield_spring.maximum}


class ShieldContact:
    """Ground-aware rotation about the carried grip; never detach or translate.

Cache evaluated geometry in control space. Hang edge-down with damped donor
heading, then tip face-up only as far as the floor requires. The grip is fixed.
"""
    def __init__(self, rig, shield):
        import bpy
        self.rig, self.shield = rig, shield
        self.points = []
        inverse = shield.matrix_world.inverted()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for ob in shield.children:
            evaluated = ob.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            self.points.extend(inverse @ ob.matrix_world @ v.co for v in mesh.vertices)
            evaluated.to_mesh_clear()
        self.max_angle = 0.
        self.previous = None

    def solve(self, face_up=False):
        from mathutils import Matrix, Vector, Quaternion
        matrix = self.shield.matrix_world.copy()
        pivot = self.rig.matrix_world @ self.rig.pose.bones['lowerarm_l'].tail
        # The shell was authored in the control's XZ plane.
        normal = matrix.to_quaternion() @ Vector((0, -1, 0))
        # A freely hinged carrying grip lets the heavy shield hang edge-down.
        # Remove the donor wrist's tray tilt, retain its yaw/roll, and damp the
        # carrier's rotation in world space. Contact below determines the tilt.
        horizontal = Vector((normal.x, normal.y, 0)).normalized()
        hanging = normal.rotation_difference(horizontal)
        desired = hanging @ matrix.to_quaternion()
        if self.previous is not None:
            desired = self.previous.slerp(desired, 1-math.exp(-1/(24*.12)))
        hanging = desired @ matrix.to_quaternion().inverted()
        matrix = (Matrix.Translation(pivot) @ hanging.to_matrix().to_4x4()
                  @ Matrix.Translation(-pivot) @ matrix)
        normal = matrix.to_quaternion() @ Vector((0, -1, 0))
        world = [matrix @ point-pivot for point in self.points]
        def lowest(rotation):
            return min((rotation @ point).z+pivot.z for point in world)
        settle=max(0.,min(1.,(.38-pivot.z)/.14)) if face_up else 0.
        settle=settle*settle*(3-2*settle)
        if lowest(Quaternion()) >= .109 and not settle:
            self.shield.matrix_world = matrix
            self.previous = matrix.to_quaternion()
            return
        rotation = normal.rotation_difference(Vector((0, 0, 1)))
        assert lowest(rotation) >= .109, 'Attached shield has no floor-clear hinge pose'
        lo, hi = 0., 1.
        for _ in range(14):
            mid = (lo+hi)*.5
            if lowest(Quaternion().slerp(rotation, mid)) >= .109:
                hi = mid
            else:
                lo = mid
        rotation = Quaternion().slerp(rotation, max(hi,settle))
        self.max_angle = max(self.max_angle, rotation.angle)
        self.shield.matrix_world = (Matrix.Translation(pivot)
            @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ matrix)
        self.previous = self.shield.matrix_world.to_quaternion()


def death_source_layers(source, action):
    """Sample two existing open poses for source-local recoil/carry blending."""
    import bpy
    scene = bpy.context.scene
    scene.frame_set(int(action.frame_range[1]))
    settled = {p.name: p.rotation_quaternion.copy() for p in source.pose.bones
               if p.name.startswith(('DEF-thigh.', 'DEF-shin.', 'DEF-foot.', 'DEF-toe.'))}
    idle = bpy.data.actions['Idle_Loop']
    source.animation_data.action = idle
    source.animation_data.action_slot = idle.slots[0]
    scene.frame_set(int(idle.frame_range[0]))
    carried = {name: source.pose.bones[name].rotation_quaternion.copy()
               for name in [f'DEF-{bone}.{side}' for side in ['L', 'R']
                            for bone in ['upper_arm', 'forearm', 'hand']]}
    source.animation_data.action = action
    source.animation_data.action_slot = action.slots[0]
    return settled, carried


def blend_death_source(source, phase, layers):
    """Blend open donor poses before world/rest-roll retargeting, never feet after.

The terminal donor leg pose restrains its comedic impact recoil. Idle's local
arm poses retain the carried shield and soften the free-arm recoil as the donor torso falls. Neither
layer authors a human pose; the original source curves remain intact.
"""
    settled, carried = layers
    recoil = curve(phase, [0, 0, 0, .25, .85, .90, .55, 0, 0, 0])
    carry = min(1., max(0., phase/.45))
    carry = carry*carry*(3-2*carry)*.85
    for poses, weight in [(settled, recoil), (carried, carry)]:
        for name, rotation in poses.items():
            p = source.pose.bones[name]
            p.rotation_quaternion = p.rotation_quaternion.slerp(
                rotation, weight*(.65/.85 if poses is carried and name.endswith('.R') else 1.))

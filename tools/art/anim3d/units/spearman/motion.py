"""Spearman timing and passive equipment response; no anatomy/material edits.

Source actions own human joint motion except for the weapon-specific attack.
Secondary motion is a damped inertial response to the evaluated carrier, not a
second hand-keyed performance. Units are metres, seconds and radians.
"""
import math


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
        # Preserve the open clip's poses; spend fewer samples on its slow squat
        # and more on impact/settle. The final two delivered samples still hold.
        return curve(phase, [0, .12, .31, .48, .66, .82, .93, .985, 1, 1])
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
        self.hair_spring = Spring(4.2, .48, .7, .026)
        self.shield_spring = Spring(3.0, .72, .06, math.radians(3))
        if clip in ['idle', 'move']:
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
        if self.clip in ['idle', 'move']:
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


class WalkWeight:
    """Weight shift layered on the retargeted open walk; legs and feet untouched.

The donor's legs carry the gait, but under a fixed spear-and-shield guard the
torso was rigid, which is what made the in-place cycle read as a march. Real
walking drops the pelvis at double support, carries it over the stance foot
and counter-rotates the shoulders. Phase comes from the measured stance
intervals of the same clip, so the layer cannot drift against the feet. The
caller re-solves both ankles to their previous world positions, so planted
contacts are unchanged. Metres and radians.
"""
    DIP, SWAY, TWIST, LEAN, NOD = .022, .020, .045, .045, .03
    STEP_WIDTH = .085
    # The guard stands right of the disc centre; walk nearer the middle so
    # the wider steps stay on the stone.
    CENTRE_X = -.07
    SPEAR = .045

    def __init__(self, planted, first, count):
        import math
        # Centre of the left stance interval, as a cycle phase.
        frames = [first+i for i in range(count)]
        flags = [bool(planted.get(str(f), {}).get('l')) for f in frames]
        angle = [2*math.pi*i/count for i, on in enumerate(flags) if on]
        self.left = math.atan2(sum(math.sin(a) for a in angle), sum(math.cos(a) for a in angle))/(2*math.pi) if angle else 0.
        self.opposite = [bool(planted.get(str(f), {}).get('r')) for f in frames]

    def channels(self, phase):
        import math
        a = 2*math.pi*(phase-self.left)
        side = math.cos(a)                      # +1 over the left foot, -1 over the right
        dip = (1-math.cos(2*a))/2               # 0 at mid-stance, 1 at double support
        return {'sway': self.SWAY*side, 'dip': -self.DIP*dip,
                'twist': self.TWIST*math.sin(a), 'lean': self.LEAN+self.NOD*dip,
                'spear': self.SPEAR*math.sin(a+.6)}

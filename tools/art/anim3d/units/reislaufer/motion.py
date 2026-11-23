"""CC0 Quaternius samples, retargeted as world-space deltas onto the standing rig.

Source joint axes are evaluated in their own hierarchy before converting Y-up to
Blender Z-up and aligning forward with the reislaufer's -Y travel direction. The
reference pose cancels source bone rolls; no post-retarget foot yaw correction.
"""
import bisect
import hashlib
import json
import math
import struct
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

CLIPS = {'neutral': 'A_TPose', 'idle': 'Idle_Loop', 'move': 'Walk_Loop',
         'hit': 'Hit_Chest', 'death': 'Death01'}
MAP = {'pelvis': 'DEF-hips', 'spine_01': 'DEF-spine.001',
       'spine_02': 'DEF-spine.002', 'spine_03': 'DEF-spine.003',
       'neck_01': 'DEF-neck', 'head': 'DEF-head'}
for side, suffix in [('l', '.L'), ('r', '.R')]:
    for dst, src in [('upperarm', 'upper_arm'), ('lowerarm', 'forearm'),
                     ('hand', 'hand'), ('thigh', 'thigh'), ('calf', 'shin'),
                     ('foot', 'foot'), ('ball', 'toe')]:
        MAP[dst+'_'+side] = 'DEF-'+src+suffix


class Motion:
    def __init__(self, root):
        self.path = Path(root)/'assets/quaternius-ual/AnimationLibrary_Godot_Standard.gltf'
        self.data = json.loads(self.path.read_text())
        self.binary_path = self.path.with_suffix('.bin')
        self.binary = self.binary_path.read_bytes()
        lock = json.loads((Path(__file__).parent/'motion.lock.json').read_text())
        for name, digest in lock.items():
            assert hashlib.sha256((self.path.parent/name).read_bytes()).hexdigest() == digest, f'Motion source changed: {name}'
        self.animations = {a['name']: a for a in self.data['animations']}
        self.parents = {child: i for i, n in enumerate(self.data['nodes']) for child in n.get('children', [])}
        self.accessors = {}
        self.axes = Matrix.Rotation(math.pi/2, 4, 'X')

    def values(self, index):
        if index in self.accessors:
            return self.accessors[index]
        a = self.data['accessors'][index]
        assert a['componentType'] == 5126 and 'sparse' not in a
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        view = self.data['bufferViews'][a['bufferView']]
        offset = view.get('byteOffset', 0)+a.get('byteOffset', 0)
        stride = view.get('byteStride', width*4)
        values = [struct.unpack_from('<'+'f'*width, self.binary, offset+i*stride) for i in range(a['count'])]
        self.accessors[index] = values
        return values

    def sample(self, clip, phase):
        animation = self.animations[CLIPS[clip]]
        duration = max(self.values(s['input'])[-1][0] for s in animation['samplers'])
        time = max(0, min(1, phase))*duration
        transforms = {}
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]
            assert sampler.get('interpolation', 'LINEAR') in ('LINEAR', 'STEP')
            times = [v[0] for v in self.values(sampler['input'])]
            values = self.values(sampler['output'])
            lo = max(0, min(len(times)-2, bisect.bisect_right(times, time)-1))
            t = max(0, min(1, (time-times[lo])/max(1e-9, times[lo+1]-times[lo])))
            if sampler.get('interpolation') == 'STEP':
                t = 0
            path = channel['target']['path']
            a, b = values[lo], values[lo+1]
            if path == 'rotation':
                qa, qb = Quaternion((a[3], *a[:3])), Quaternion((b[3], *b[:3]))
                value = qa.slerp(qb, t)
            else:
                value = Vector(a).lerp(Vector(b), t)
            transforms.setdefault(channel['target']['node'], {})[path] = value
        world = {}
        def evaluate(i):
            if i in world:
                return world[i]
            node = self.data['nodes'][i]
            v = transforms.get(i, {})
            rotation = node.get('rotation', (0, 0, 0, 1))
            q = v.get('rotation', Quaternion((rotation[3], *rotation[:3])))
            m = Matrix.LocRotScale(v.get('translation', Vector(node.get('translation', (0, 0, 0)))), q,
                                  v.get('scale', Vector(node.get('scale', (1, 1, 1)))))
            if i in self.parents:
                m = evaluate(self.parents[i]) @ m
            world[i] = m
            return m
        return {n.get('name', str(i)): self.axes @ evaluate(i) for i, n in enumerate(self.data['nodes'])}

    def provenance(self, clip):
        return {'provider': 'Quaternius Universal Animation Library Standard', 'license': 'CC0-1.0',
                'clip': CLIPS[clip], 'source': 'https://quaternius.com/packs/universalanimationlibrary.html',
                'gltf_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(),
                'bin_sha256': hashlib.sha256(self.binary).hexdigest(),
                'retarget': 'world-space reference-pose deltas, Y-up conversion, fixed -Y forward alignment; standing rig with source gait'}

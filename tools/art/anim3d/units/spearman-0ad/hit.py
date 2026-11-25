"""Round 6: replace only hit's existing 25 sampled keys in the delivered GLB.

Run with gated Blender for mathutils. No mesh import/export, material edits or
resampling of approved clips. All transforms below use glTF world metres/Y-up.
The input can be round 5 or this script's output: idle is the only pose source.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys

from mathutils import Matrix, Vector

UNIT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def ease(frame, keys):
    for (a, x), (b, y) in zip(keys, keys[1:]):
        if frame <= b:
            t = max(0, min(1, (frame-a)/(b-a)))
            return x+(y-x)*t*t*(3-2*t)
    return keys[-1][1]


def rebuild(path):
    g = GLB(path)
    d = copy.deepcopy(g.doc)
    names = {n['name']: i for i, n in enumerate(d['nodes']) if 'name' in n}
    parents = {c: i for i, n in enumerate(d['nodes']) for c in n.get('children', [])}
    clips = {a['name']: a for a in d['animations']}
    idle, hit = clips['idle'], clips['hit']
    initial = {i: Matrix([[m[c*4+r] for c in range(4)] for r in range(4)])
               for i, m in g.worlds(idle, 0).items()}
    rest = {i: initial[parents[i]].inverted() @ m if i in parents else m.copy()
            for i, m in initial.items()}
    idle_values = {(c['target']['node'], c['target']['path']):
                   g.accessor(idle['samplers'][c['sampler']]['output'])[0]
                   for c in idle['channels']}
    sampled = []
    for frame in range(25):
        local = {i: m.copy() for i, m in rest.items()}

        def world(i):
            return world(parents[i]) @ local[i] if i in parents else local[i].copy()

        def set_world(name, m):
            i = names[name]
            local[i] = world(parents[i]).inverted() @ m if i in parents else m.copy()

        def rotate(name, degrees, axis='X'):
            m = world(names[name]); p = m.translation.copy()
            set_world(name, Matrix.Translation(p) @ Matrix.Rotation(math.radians(degrees), 4, axis)
                      @ Matrix.Translation(-p) @ m)

        def limb(upper, lower, end, target):
            root, elbow, tip = [world(names[n]).translation.copy() for n in (upper, lower, end)]
            a, b = (elbow-root).length, (tip-elbow).length
            reach = target.translation-root
            assert reach.length < a+b, 'Unreachable foot target'
            direction = reach.normalized()
            pole = elbow-root; pole = (pole-direction*pole.dot(direction)).normalized()
            along = (a*a-b*b+reach.length_squared)/(2*reach.length)
            knee = root+direction*along+pole*math.sqrt(max(0, a*a-along*along))
            for joint, child, goal in [(upper, lower, knee), (lower, end, target.translation)]:
                m = world(names[joint]); p = m.translation.copy()
                delta = (world(names[child]).translation-p).rotation_difference(goal-p).to_matrix().to_4x4()
                set_world(joint, Matrix.Translation(p) @ delta @ Matrix.Translation(-p) @ m)
            # Foot orientation stays flat; translation is the fixed-length solve.
            m = target.copy(); m.translation = world(names[end]).translation
            set_world(end, m)

        recoil = ease(frame, [(0,0),(4,1),(8,1),(24,0)])
        catch = ease(frame, [(0,0),(4,0),(8,1),(12,1),(24,0)])
        head = ease(frame, [(0,0),(1,0),(5,1),(8,1),(24,0)])
        hip = world(names['hip'])
        hip.translation += Vector((0, -.065*recoil, -.15*recoil))
        set_world('hip', hip)
        for side in ['L', 'R']:
            target = initial[names['foot_'+side]].copy()
            if side == 'L':
                target.translation.z -= .15*catch
                target.translation.y += .045*ease(frame, [(0,0),(4,0),(6,1),(8,0),(14,0),(18,1),(24,0)])
            limb('thigh_'+side, 'leg_'+side, 'foot_'+side, target)
        rotate('spine', -14*recoil)
        rotate('chest', -11*recoil)
        rotate('neck', -9*head)
        # Shield stays attached to its forearm: outward arm rotation, recoil
        # behind the torso and a short wrist jolt; no prop-only translation.
        rotate('arm_L', 18*recoil)
        rotate('arm_L', 18*recoil, 'Z')
        rotate('forearm_L', 10*recoil, 'Y')
        # Dropped weapon elbow and wrist pitch dip the spearhead visibly.
        rotate('arm_R', 22*recoil)
        rotate('hand_R', 36*recoil)
        # Keep the butt clear of the ground as the torso sinks. The arm solve
        # lifts the actual grip, preserving bone lengths and rigid attachment.
        grip = world(names['hand_R']); grip.translation.y += .09*recoil
        limb('arm_R', 'forearm_R', 'hand_R', grip)
        sampled.append(local)

    blob = bytearray(g.bin)
    edited = []
    other_outputs = {s['output'] for a in d['animations'] if a['name'] != 'hit' for s in a['samplers']}
    for channel in hit['channels']:
        node, field = channel['target']['node'], channel['target']['path']
        sampler = hit['samplers'][channel['sampler']]
        index = sampler['output']; assert index not in other_outputs
        acc = d['accessors'][index]; view = d['bufferViews'][acc['bufferView']]
        assert acc['count'] == 25 and acc['componentType'] == 5126
        values = []
        for frame, local in enumerate(sampled):
            loc, quat, scale = local[node].decompose()
            value = {'translation': tuple(loc), 'rotation': (quat.x,quat.y,quat.z,quat.w), 'scale': tuple(scale)}[field]
            if frame in (0,24) or node == names['Spearman']:
                value = idle_values.get((node,field), g.accessor(index)[0])
            if field == 'rotation' and values and sum(a*b for a,b in zip(value,values[-1])) < 0:
                value = tuple(-x for x in value)
            values.append(value)
        width = len(values[0]); stride = view.get('byteStride', width*4)
        offset = view.get('byteOffset',0)+acc.get('byteOffset',0)
        for frame, value in enumerate(values):
            struct.pack_into('<'+'f'*width, blob, offset+frame*stride, *value)
            edited.append((offset+frame*stride, offset+frame*stride+width*4))
        if 'min' in acc: acc['min'] = [min(v[i] for v in values) for i in range(width)]
        if 'max' in acc: acc['max'] = [max(v[i] for v in values) for i in range(width)]

    # A strict byte-level isolation check covers geometry, atlas and approved
    # animation samplers, including data the contract validator does not inspect.
    allowed = bytearray(len(blob))
    for a,b in edited: allowed[a:b] = b'\1'*(b-a)
    assert all(a == b or allowed[i] for i,(a,b) in enumerate(zip(g.bin,blob)))
    before = copy.deepcopy(g.doc); after = copy.deepcopy(d)
    for doc in [before,after]:
        for sampler in hit['samplers']:
            for key in ['min','max']: doc['accessors'][sampler['output']].pop(key,None)
    assert before == after
    raw = json.dumps(d,separators=(',',':')).encode(); raw += b' '*(-len(raw)%4)
    Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))
                           +struct.pack('<II',len(raw),0x4e4f534a)+raw
                           +struct.pack('<II',len(blob),0x004e4942)+blob)
    report = {'only_hit_changed': True, 'unchanged_binary_sha256': hashlib.sha256(bytes(b for i,b in enumerate(blob) if not allowed[i])).hexdigest(),
              'glb_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
              'frames':25,'fps':30,'duration':.8,'pelvis_back_m':.15,'pelvis_drop_m':.065,
              'spine_chest_recoil_degrees':25,'head_delay_frames':1,'rear_step_m':.15}
    work = Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))/'oad/r6'
    work.mkdir(parents=True,exist_ok=True)
    (work/'hit-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    rebuild(UNIT/'spearman.glb')

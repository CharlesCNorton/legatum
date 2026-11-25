"""Conservative hip clearance envelope, evaluated between exported 30 fps keys.

Rotating rigid props can cross the floor between two clear sampled poses. Raise
the two enclosing hip keys by that interval's measured deficit. A short maximum
envelope spreads the correction without lowering a required clearance sample.
The skeleton root stays fixed and loop endpoints retain identical corrections.
"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_glb import GLB, point
from merge import inverse


def correct(path):
    report = {}
    for name in ['attack', 'death', 'walk']:
        g = GLB(path); d = g.doc
        clip = next(a for a in d['animations'] if a['name'] == name)
        hip = next(i for i,n in enumerate(d['nodes']) if n.get('name') == 'hip')
        parent = next(i for i,n in enumerate(d['nodes']) if hip in n.get('children', []))
        channel = next(c for c in clip['channels'] if c['target'] == {'node': hip, 'path': 'translation'})
        sampler = clip['samplers'][channel['sampler']]
        times = [t[0] for t in g.accessor(sampler['input'])]
        shifts = [0.0]*len(times)
        for i in range(len(times)-1):
            minimum = min(p[1] for sub in range(5)
                          for _,p in g.vertices(clip, times[i]+(times[i+1]-times[i])*sub/4))
            deficit = max(0, .0002-minimum) if minimum < -.00005 else 0
            shifts[i] = max(shifts[i], deficit); shifts[i+1] = max(shifts[i+1], deficit)
        # Keep a correction's onset/exit gentle without reducing its peak.
        shifts = [max(shifts[j]*(.5**abs(i-j)) for j in range(max(0,i-2),min(len(shifts),i+3))) for i in range(len(shifts))]
        if name == 'walk': shifts[0] = shifts[-1] = max(shifts[0], shifts[-1])
        acc = d['accessors'][sampler['output']]; view = d['bufferViews'][acc['bufferView']]
        offset = view.get('byteOffset',0)+acc.get('byteOffset',0); stride = view.get('byteStride',12)
        blob = bytearray(g.bin); values = []
        for i, (original, lift) in enumerate(zip(g.accessor(sampler['output']), shifts)):
            inv = inverse(g.worlds(clip,times[i])[parent]); origin = point(inv,(0,0,0)); up = point(inv,(0,lift,0))
            value = tuple(v+b-a for v,a,b in zip(original,origin,up)); values.append(value)
            struct.pack_into('<3f',blob,offset+i*stride,*value)
        acc['min'] = [min(v[i] for v in values) for i in range(3)]
        acc['max'] = [max(v[i] for v in values) for i in range(3)]
        raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
        Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
        report[name] = {'maximum_hip_lift_m': max(shifts)}
    return report


if __name__ == '__main__': print(correct(Path(sys.argv[1])))

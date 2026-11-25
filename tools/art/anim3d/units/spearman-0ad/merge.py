"""Collapse the authored GLB into one draw call without changing its motion.

Rigid props use the same inverse-bind space as the body, with one unit weight.
COLOR_0 is data, not display colour: red = team weight, G/B = 0, A = 1.
"""
import json, math, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB, multiply, point, IDENTITY


def inverse(m):
    rows = [[m[c*4+r] for c in range(4)] + [int(r == c) for c in range(4)] for r in range(4)]
    for c in range(4):
        pivot = max(range(c, 4), key=lambda r: abs(rows[r][c]))
        rows[c], rows[pivot] = rows[pivot], rows[c]
        divisor = rows[c][c]
        rows[c] = [v/divisor for v in rows[c]]
        for r in range(4):
            if r != c:
                factor = rows[r][c]
                rows[r] = [v-factor*w for v, w in zip(rows[r], rows[c])]
    return [rows[r][c+4] for c in range(4) for r in range(4)]


def merge(path):
    g = GLB(path); d = g.doc
    assert len(d['meshes']) > 1, 'Rebuild from the preserved input; already merged'
    skin = d['skins'][0]; binds = list(g.accessor(skin['inverseBindMatrices']))
    names = {n.get('name'): i for i, n in enumerate(d['nodes'])}
    head = names['head']
    # A dedicated rigid helmet socket, following the native head unchanged.
    d['nodes'][names['helmet']]['name'] = 'source_helmet'
    helmet = len(d['nodes']); d['nodes'].append({'name': 'helmet'})
    d['nodes'][head].setdefault('children', []).append(helmet)
    skin['joints'].append(helmet); binds.append(binds[skin['joints'].index(head)])
    parents = {c: i for i, n in enumerate(d['nodes']) for c in n.get('children', [])}
    worlds = g.worlds(next(a for a in d['animations'] if a['name'] == 'idle'), 0)
    attrs = {k: [] for k in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0', 'COLOR_0']}
    indices = []; regions = []; mesh_nodes = []
    for ni, node in enumerate(d['nodes']):
        if 'mesh' not in node: continue
        mesh_nodes.append(ni); name = node['name'].removeprefix('source_')
        rigid = 'skin' not in node
        if rigid:
            bone = helmet if name in {'helmet', 'crest', 'crest_base'} else parents[ni]
            joint = skin['joints'].index(bone)
            transform = multiply(inverse(multiply(worlds[bone], binds[joint])), worlds[ni])
            inv = inverse(transform)
        for prim in d['meshes'][node['mesh']]['primitives']:
            old = {k: g.accessor(v) for k, v in prim['attributes'].items()}
            start = len(attrs['POSITION']); count = len(old['POSITION'])
            team = d['materials'][prim['material']]['name'] == 'team'
            regions.append({'part': name, 'start': start, 'count': count,
                            'bone': d['nodes'][bone]['name'] if rigid else None,
                            'team': {'body': 'cloak trim', 'aspis': 'shield rim', 'crest': 'crest'}.get(name) if team else None})
            for i, pos in enumerate(old['POSITION']):
                normal = old['NORMAL'][i]
                if rigid:
                    pos = point(transform, pos)
                    normal = tuple(sum(inv[r*4+c]*normal[c] for c in range(3)) for r in range(3))
                    length = math.sqrt(sum(v*v for v in normal)); normal = tuple(v/length for v in normal)
                attrs['POSITION'].append(pos); attrs['NORMAL'].append(normal)
                attrs['TEXCOORD_0'].append(old['TEXCOORD_0'][i])
                attrs['JOINTS_0'].append((joint, 0, 0, 0) if rigid else old['JOINTS_0'][i])
                attrs['WEIGHTS_0'].append((1, 0, 0, 0) if rigid else old['WEIGHTS_0'][i])
                attrs['COLOR_0'].append((int(team), 0, 0, 1))
            indices.extend((start+i[0],) for i in g.accessor(prim['indices']))
    # Repack only live data; do not leave the original meshes/buffers behind.
    old_views = d['bufferViews']; old_accessors = d['accessors']
    d['bufferViews'] = []; d['accessors'] = []; blob = bytearray()
    def view(raw, target=None):
        blob.extend(b'\0' * (-len(blob) % 4)); offset = len(blob); blob.extend(raw)
        v = {'buffer': 0, 'byteOffset': offset, 'byteLength': len(raw)}
        if target: v['target'] = target
        d['bufferViews'].append(v); return len(d['bufferViews'])-1
    def accessor(values, kind, component=5126, target=None):
        fmt = {5126: 'f', 5123: 'H', 5125: 'I'}[component]
        raw = b''.join(struct.pack('<'+fmt*len(row), *row) for row in values)
        a = {'bufferView': view(raw, target), 'componentType': component, 'count': len(values), 'type': kind}
        if kind != 'MAT4':
            a.update(min=[min(v[i] for v in values) for i in range(len(values[0]))],
                     max=[max(v[i] for v in values) for i in range(len(values[0]))])
        d['accessors'].append(a); return len(d['accessors'])-1
    # Read through the original tables while copying animation samples.
    copied = {}
    for a in d['animations']:
        for sampler in a['samplers']:
            for key in ['input', 'output']:
                old = sampler[key]
                if old not in copied:
                    live_a, live_v = d['accessors'], d['bufferViews']
                    d['accessors'], d['bufferViews'] = old_accessors, old_views
                    values = g.accessor(old)
                    d['accessors'], d['bufferViews'] = live_a, live_v
                    copied[old] = accessor(values, old_accessors[old]['type'])
                sampler[key] = copied[old]
    skin['inverseBindMatrices'] = accessor(binds, 'MAT4')
    for im in d['images']:
        v = old_views[im['bufferView']]; off = v.get('byteOffset', 0)
        im['bufferView'] = view(g.bin[off:off+v['byteLength']])
    newattrs = {k: accessor(v, 'VEC'+str(len(v[0])), 5123 if k == 'JOINTS_0' else 5126, 34962) for k, v in attrs.items()}
    primitive = {'attributes': newattrs, 'indices': accessor(indices, 'SCALAR', 5123, 34963), 'material': 0}
    d['meshes'] = [{'name': 'Spearman', 'primitives': [primitive], 'extras': {'vertex_regions': regions}}]
    for ni in mesh_nodes:
        node = d['nodes'][ni]; node.pop('mesh'); node.pop('skin', None)
    body = names['body']; d['nodes'][body].update(mesh=0, skin=0)
    mat = next(m for m in d['materials'] if m['name'] == 'pigment')
    mat['name'] = 'pigment'; mat['extras'] = {'team': {'attribute': 'COLOR_0', 'channel': 'r', 'default_srgb': '#a52627', 'operation': 'baseColor *= mix(vec3(1), teamColorLinear, COLOR_0.r)'}}
    d['materials'] = [mat]
    texture_index=mat['pbrMetallicRoughness']['baseColorTexture']['index']
    d['textures']=[d['textures'][texture_index]]
    mat['pbrMetallicRoughness']['baseColorTexture']['index']=0
    d['asset']['extras']['team'] = mat['extras']['team']
    d['buffers'] = [{'byteLength': len(blob)}]; blob.extend(b'\0'*(-len(blob)%4))
    raw = json.dumps(d, separators=(',', ':')).encode(); raw += b' '*(-len(raw)%4)
    Path(path).write_bytes(struct.pack('<4sII', b'glTF', 2, 28+len(raw)+len(blob)) + struct.pack('<II', len(raw), 0x4e4f534a) + raw + struct.pack('<II', len(blob), 0x004e4942) + blob)


if __name__ == '__main__': merge(Path(sys.argv[1]))

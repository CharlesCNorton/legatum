"""Pack Blender-authored geometry while copying approved rig/clip bytes exactly."""
import copy, hashlib, json, struct
from mathutils import Vector
from pathlib import Path

def write_glb(source, lods, textures, path, master_size=2048):
    d=copy.deepcopy(source.doc); d['accessors']=[];d['bufferViews']=[];blob=bytearray()
    def view(raw,target=None):
        blob.extend(b'\0'*(-len(blob)%4));off=len(blob);blob.extend(raw)
        v={'buffer':0,'byteOffset':off,'byteLength':len(raw)}
        if target:v['target']=target
        d['bufferViews'].append(v);return len(d['bufferViews'])-1
    def acc(values,kind,component=5126,target=None,normalized=False):
        fmt={5120:'b',5121:'B',5122:'h',5126:'f',5123:'H',5125:'I'}[component]
        rows=[struct.pack('<'+fmt*len(v),*v) for v in values]
        stride=(len(rows[0])+3)//4*4 if target==34962 else len(rows[0])
        raw=b''.join(row+b'\0'*(stride-len(row)) for row in rows)
        a={'bufferView':view(raw,target),'componentType':component,'count':len(values),'type':kind}
        if stride!=len(rows[0]):d['bufferViews'][a['bufferView']]['byteStride']=stride
        if normalized:a['normalized']=True
        if kind!='MAT4':
            a['min']=[min(v[i] for v in values) for i in range(len(values[0]))]
            a['max']=[max(v[i] for v in values) for i in range(len(values[0]))]
        d['accessors'].append(a);return len(d['accessors'])-1
    copied={}
    def original(i):
        if i not in copied:
            a=copy.deepcopy(source.doc['accessors'][i]);v=source.doc['bufferViews'][a['bufferView']]
            assert 'byteStride' not in v
            raw=source.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
            a['bufferView']=view(raw);d['accessors'].append(a);copied[i]=len(d['accessors'])-1
        return copied[i]
    for a in d['animations']:
        for sampler in a['samplers']:
            for key in ('input','output'):sampler[key]=original(sampler[key])
    d['skins'][0]['inverseBindMatrices']=original(d['skins'][0]['inverseBindMatrices'])
    d['meshes']=[]
    for level,(attrs,indices,regions) in enumerate(lods):
        attrs['JOINTS_0']=[tuple(j if round(w*65535)>0 else 0 for j,w in zip(js,ws)) for js,ws in zip(attrs['JOINTS_0'],attrs['WEIGHTS_0'])]
        packed={}
        for key,values in attrs.items():
            component=5126;normalized=False
            if key=='COLOR_0':
                values=[tuple(round(x*255) for x in row) for row in values];component=5121;normalized=True
            elif key=='JOINTS_0':component=5121
            elif key in ('NORMAL','TANGENT'):
                values=[tuple(round(max(-1,min(1,x))*127) for x in row) for row in values];component=5120;normalized=True
            elif key=='TEXCOORD_0':
                assert all(0<=x<=1 for row in values for x in row)
                values=[tuple(round(x*65535) for x in row) for row in values];component=5123;normalized=True
            elif key=='WEIGHTS_0':
                quantized=[]
                for row in values:
                    q=[round(x*65535) for x in row];q[max(range(4),key=lambda i:q[i])]+=65535-sum(q);quantized.append(tuple(q))
                values=quantized;component=5123;normalized=True
            packed[key]=acc(values,'VEC'+str(len(values[0])),component,34962,normalized)
        attrs=packed
        primitive={'attributes':attrs,'indices':acc([(i,) for i in indices],'SCALAR',5123 if max(indices)<65535 else 5125,34963),'material':0}
        d['meshes'].append({'name':f'spearman_LOD{level}','primitives':[primitive],'extras':{'vertex_regions':regions,'lod':level}})
    oldnode=next(n for n in d['nodes'] if 'mesh' in n)
    oldnode.update(name='spearman_LOD0',mesh=0)
    d['nodes'].append({'name':'spearman_LOD1','mesh':1,'skin':0})
    d['scenes'][d.get('scene',0)]['nodes'].append(len(d['nodes'])-1)
    d['images']=[{'name':name,'mimeType':'image/webp','bufferView':view(Path(p).read_bytes())} for name,p in textures.items()]
    d['textures']=[{'extensions':{'EXT_texture_webp':{'source':i}},'sampler':0} for i in range(3)]
    d['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
    team=source.doc['asset']['extras']['team']
    d['materials']=[{'name':'Spearman PBR','doubleSided':True,'pbrMetallicRoughness':{'baseColorTexture':{'index':0,'texCoord':0},'metallicRoughnessTexture':{'index':2,'texCoord':0},'metallicFactor':1,'roughnessFactor':1},'normalTexture':{'index':1,'texCoord':0,'scale':.45},'occlusionTexture':{'index':2,'texCoord':0,'strength':.65},'extras':{'team':team}}]
    d['extensionsUsed']=['KHR_mesh_quantization','EXT_texture_webp'];d['extensionsRequired']=['KHR_mesh_quantization','EXT_texture_webp']
    d['asset']['extras'].update(lods={'nodes':['spearman_LOD0','spearman_LOD1'],'policy':'Select exactly one LOD; shared skeleton and material; no MSFT_lod'},texture_master_px=master_size,look='pbr-r2',approved_motion_sha256=hashlib.sha256(source.path.read_bytes()).hexdigest())
    d['buffers']=[{'byteLength':len(blob)}];blob.extend(b'\0'*(-len(blob)%4))
    raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
    Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)

def extract(ob, catalog):
    """Split corners at UV/normal seams; group indices into auditable part ranges."""
    me=ob.data;me.calc_loop_triangles();me.calc_tangents(uvmap=me.uv_layers.active.name)
    attrs={k:[] for k in ['POSITION','NORMAL','TANGENT','TEXCOORD_0','JOINTS_0','WEIGHTS_0','COLOR_0']};indices=[];regions=[]
    for mi,mat in enumerate(me.materials):
        meta=catalog[mat.name];start=len(attrs['POSITION']);seen={}
        for tri in me.loop_triangles:
            if tri.material_index!=mi or tri.area<1e-12:continue
            for li in tri.loops:
                loop=me.loops[li];v=me.vertices[loop.vertex_index];uv=me.uv_layers.active.data[li].uv
                # Blender mesh is authored directly in glTF bind coordinates.
                n=me.corner_normals[li].vector.copy()
                if n.length<.5:n=tri.normal.copy()
                n.normalize();t=loop.tangent.copy()
                if t.length<.5:
                    t=n.cross(Vector((0,1,0)))
                    if t.length<.01:t=n.cross(Vector((1,0,0)))
                t.normalize()
                key=(v.index,tuple(uv),tuple(n),tuple(t),loop.bitangent_sign)
                if key not in seen:
                    seen[key]=len(attrs['POSITION']);attrs['POSITION'].append(tuple(v.co));attrs['NORMAL'].append(tuple(n))
                    # Match Blender glTF exporter: UV image-origin conversion does not
                    # change tangent handedness (there is no reflected object transform).
                    attrs['TANGENT'].append((*t,loop.bitangent_sign));attrs['TEXCOORD_0'].append((uv.x,1-uv.y))
                    weights=sorted([(int(ob.vertex_groups[g.group].name[1:]),g.weight) for g in v.groups if ob.vertex_groups[g.group].name.startswith('j') and g.weight>1e-8],key=lambda x:-x[1])[:4]
                    assert weights,(ob.name,v.index)
                    total=sum(w for _,w in weights);js=[j for j,w in weights];ws=[w/total for j,w in weights]
                    attrs['JOINTS_0'].append(tuple(js+[0]*(4-len(js))));attrs['WEIGHTS_0'].append(tuple(ws+[0]*(4-len(ws))))
                    attrs['COLOR_0'].append((int(bool(meta['team'])),0,0,1))
                indices.append(seen[key])
        if len(attrs['POSITION'])>start:regions.append({**meta,'start':start,'count':len(attrs['POSITION'])-start})
    return attrs,indices,regions

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
    def acc(values,kind,component=5126,target=None):
        fmt={5126:'f',5123:'H',5125:'I'}[component]
        raw=b''.join(struct.pack('<'+fmt*len(v),*v) for v in values)
        a={'bufferView':view(raw,target),'componentType':component,'count':len(values),'type':kind}
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
        attrs={k:acc(v,'VEC'+str(len(v[0])),5123 if k=='JOINTS_0' else 5126,34962) for k,v in attrs.items()}
        primitive={'attributes':attrs,'indices':acc([(i,) for i in indices],'SCALAR',5125,34963),'material':0}
        d['meshes'].append({'name':f'spearman_LOD{level}','primitives':[primitive],'extras':{'vertex_regions':regions,'lod':level}})
    oldnode=next(n for n in d['nodes'] if 'mesh' in n)
    oldnode.update(name='spearman_LOD0',mesh=0)
    d['nodes'].append({'name':'spearman_LOD1','mesh':1,'skin':0})
    d['scenes'][d.get('scene',0)]['nodes'].append(len(d['nodes'])-1)
    d['images']=[{'name':name,'mimeType':'image/png','bufferView':view(Path(p).read_bytes())} for name,p in textures.items()]
    d['textures']=[{'source':i,'sampler':0} for i in range(3)]
    d['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
    team=source.doc['asset']['extras']['team']
    d['materials']=[{'name':'Spearman PBR','doubleSided':True,'pbrMetallicRoughness':{'baseColorTexture':{'index':0,'texCoord':0},'metallicRoughnessTexture':{'index':2,'texCoord':0},'metallicFactor':1,'roughnessFactor':1},'normalTexture':{'index':1,'texCoord':0},'occlusionTexture':{'index':2,'texCoord':0,'strength':.65},'extras':{'team':team}}]
    d.pop('extensionsUsed',None);d.pop('extensionsRequired',None)
    d['asset']['extras'].update(lods={'nodes':['spearman_LOD0','spearman_LOD1'],'policy':'Select exactly one LOD; shared skeleton and material; no MSFT_lod'},texture_master_px=master_size,look='pbr-r1',approved_motion_sha256=hashlib.sha256(source.path.read_bytes()).hexdigest())
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
                    attrs['TANGENT'].append((*t,-loop.bitangent_sign));attrs['TEXCOORD_0'].append((uv.x,1-uv.y))
                    weights=sorted([(int(ob.vertex_groups[g.group].name[1:]),g.weight) for g in v.groups if ob.vertex_groups[g.group].name.startswith('j') and g.weight>1e-8],key=lambda x:-x[1])[:4]
                    assert weights,(ob.name,v.index)
                    total=sum(w for _,w in weights);js=[j for j,w in weights];ws=[w/total for j,w in weights]
                    attrs['JOINTS_0'].append(tuple(js+[0]*(4-len(js))));attrs['WEIGHTS_0'].append(tuple(ws+[0]*(4-len(ws))))
                    attrs['COLOR_0'].append((int(bool(meta['team'])),0,0,1))
                indices.append(seen[key])
        if len(attrs['POSITION'])>start:regions.append({**meta,'start':start,'count':len(attrs['POSITION'])-start})
    return attrs,indices,regions

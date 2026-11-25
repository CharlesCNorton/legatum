"""Repack art around untouched round-six skeleton and animation accessor bytes."""
import copy,json,struct,hashlib

def package(g,meshes,unit,work):
    d=copy.deepcopy(g.doc);old=d['accessors'];views=d['bufferViews'];blob=bytearray();d['accessors']=[];d['bufferViews']=[]
    def view(raw,target=None):
        blob.extend(b'\0'*(-len(blob)%4));v={'buffer':0,'byteOffset':len(blob),'byteLength':len(raw)};blob.extend(raw)
        if target:v['target']=target
        d['bufferViews'].append(v);return len(d['bufferViews'])-1
    def acc(values,kind,component=5126,target=None):
        fmt={5126:'f',5123:'H',5125:'I'}[component];a={'bufferView':view(b''.join(struct.pack('<'+fmt*len(row),*row) for row in values),target),'componentType':component,'count':len(values),'type':kind}
        if kind!='MAT4':a.update(min=[min(v[i] for v in values) for i in range(len(values[0]))],max=[max(v[i] for v in values) for i in range(len(values[0]))])
        d['accessors'].append(a);return len(d['accessors'])-1
    copied={}
    def original(i):
        if i not in copied:
            a=copy.deepcopy(old[i]);v=views[a['bufferView']];assert 'byteStride' not in v
            a['bufferView']=view(g.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);d['accessors'].append(a);copied[i]=len(d['accessors'])-1
        return copied[i]
    for a in d['animations']:
        for s in a['samplers']:
            for k in ['input','output']:s[k]=original(s[k])
    for skin in d['skins']:skin['inverseBindMatrices']=original(skin['inverseBindMatrices'])
    d['meshes']=[]
    for m in meshes:
        aa={k:acc(v,'VEC'+str(len(v[0])),5123 if k=='JOINTS_0' else 5126,34962) for k,v in m['attrs'].items()}
        d['meshes'].append({'name':m['name'],'primitives':[{'attributes':aa,'indices':acc(m['indices'],'SCALAR',5125,34963),'material':0}],'extras':{'vertex_regions':m['regions'],'lod':len(d['meshes'])}})
    node=next(n for n in d['nodes'] if 'mesh' in n);node.update(name='spearman_LOD0',mesh=0,skin=0)
    d['nodes'].append({'name':'spearman_LOD1','mesh':1,'skin':0});d['scenes'][d.get('scene',0)]['nodes'].append(len(d['nodes'])-1)
    d['images']=[];d['textures']=[]
    for name in ['basecolor','normal','orm']:
        d['images'].append({'name':name,'mimeType':'image/png','bufferView':view((unit/f'spearman-{name}.png').read_bytes())});d['textures'].append({'source':len(d['images'])-1,'sampler':0})
    d['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
    team=d['asset']['extras']['team']
    d['materials']=[{'name':'Painted bronze, linen and crimson','pbrMetallicRoughness':{'baseColorTexture':{'index':0,'texCoord':0},'metallicRoughnessTexture':{'index':2,'texCoord':0},'metallicFactor':1,'roughnessFactor':1},'normalTexture':{'index':1,'texCoord':0},'occlusionTexture':{'index':2,'texCoord':0,'strength':.6},'doubleSided':True,'extras':{'team':team}}]
    d['asset']['extras'].update(lod_meshes=['spearman_LOD0','spearman_LOD1'],default_lod=0,texture_master_size=2048,look='painted',approved_motion_sha256=hashlib.sha256(g.path.read_bytes()).hexdigest())
    d['buffers']=[{'byteLength':len(blob)}];blob.extend(b'\0'*(-len(blob)%4));raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
    (unit/'spearman.glb').write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
    report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'triangles':{m['name']:len(m['indices'])//3 for m in meshes},'high_poly_bake':'Cycles CPU, selected-to-active NORMAL and AO, subdivision + geometric displacement','texture_master_px':2048,'texture_delivery_px':1024}
    (work/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

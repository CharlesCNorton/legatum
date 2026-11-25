"""Repack art around untouched round-six skeleton and animation accessor bytes."""
import copy,json,struct,hashlib,zlib

def compact_png(path):
    """Lossless PNG container recompression; filtered pixels and colour metadata stay exact."""
    data=path.read_bytes();chunks=[];compressed=[];offset=8
    while offset<len(data):
        size=struct.unpack_from('>I',data,offset)[0];tag=data[offset+4:offset+8]
        chunk=data[offset:offset+size+12];offset+=size+12
        if tag==b'IDAT':compressed.append(chunk[8:-4])
        else:chunks.append((tag,chunk))
    pixels=zlib.decompress(b''.join(compressed));packed=zlib.compress(pixels,9)
    assert zlib.decompress(packed)==pixels
    idat=struct.pack('>I',len(packed))+b'IDAT'+packed+struct.pack('>I',zlib.crc32(b'IDAT'+packed))
    output=data[:8]
    for tag,chunk in chunks:
        if tag==b'IEND':output+=idat
        output+=chunk
    if len(output)<len(data):path.write_bytes(output)


def package(g,meshes,unit,work):
    d=copy.deepcopy(g.doc);old=d['accessors'];views=d['bufferViews'];blob=bytearray();d['accessors']=[];d['bufferViews']=[];view_cache={}
    def view(raw,target=None,stride=None):
        key=(raw,target,stride)
        if key in view_cache:return view_cache[key]
        blob.extend(b'\0'*(-len(blob)%4));v={'buffer':0,'byteOffset':len(blob),'byteLength':len(raw)};blob.extend(raw)
        if target:v['target']=target
        if stride:v['byteStride']=stride
        d['bufferViews'].append(v);view_cache[key]=len(d['bufferViews'])-1;return view_cache[key]
    def acc(values,kind,component=5126,target=None,normalized=False):
        fmt={5126:'f',5121:'B',5122:'h',5123:'H',5125:'I'}[component]
        row_size=struct.calcsize(fmt)*len(values[0]);stride=(row_size+3)//4*4 if target==34962 else row_size
        raw=b''.join(struct.pack('<'+fmt*len(row),*row)+b'\0'*(stride-row_size) for row in values)
        a={'bufferView':view(raw,target,stride if stride!=row_size else None),'componentType':component,'count':len(values),'type':kind}
        if normalized:a['normalized']=True
        if kind!='MAT4':a.update(min=[min(v[i] for v in values) for i in range(len(values[0]))],max=[max(v[i] for v in values) for i in range(len(values[0]))])
        d['accessors'].append(a);return len(d['accessors'])-1
    copied={};accessor_cache={}
    def original(i):
        if i not in copied:
            a=copy.deepcopy(old[i]);v=views[a['bufferView']];assert 'byteStride' not in v
            a['bufferView']=view(g.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
            if a['type']!='SCALAR':a.pop('min',None);a.pop('max',None)
            key=json.dumps(a,sort_keys=True)
            if key not in accessor_cache:d['accessors'].append(a);accessor_cache[key]=len(d['accessors'])-1
            copied[i]=accessor_cache[key]
        return copied[i]
    for a in d['animations']:
        for s in a['samplers']:
            for k in ['input','output']:s[k]=original(s[k])
    for skin in d['skins']:skin['inverseBindMatrices']=original(skin['inverseBindMatrices'])
    d['meshes']=[]
    for m in meshes:
        packed_weights=[]
        for row in m['attrs']['WEIGHTS_0']:
            quant=[int(x*65535) for x in row]
            for i in sorted(range(4),key=lambda i:-(row[i]*65535-quant[i]))[:65535-sum(quant)]:quant[i]+=1
            packed_weights.append(quant)
        aa={}
        for k,v in m['attrs'].items():
            normalized=k in {'COLOR_0','NORMAL','TANGENT','TEXCOORD_0','WEIGHTS_0'}
            component=5126
            if k=='COLOR_0':v=[tuple(round(x*255) for x in row) for row in v];component=5121
            elif k=='JOINTS_0':v=[tuple(j if w else 0 for j,w in zip(row,q)) for row,q in zip(v,packed_weights)];component=5121
            elif k in {'NORMAL','TANGENT'}:v=[tuple(round(max(-1,min(1,x))*32767) for x in row) for row in v];component=5122
            elif k=='TEXCOORD_0':v=[tuple(round(max(0,min(1,x))*65535) for x in row) for row in v];component=5123
            elif k=='WEIGHTS_0':v=packed_weights;component=5123
            aa[k]=acc(v,'VEC'+str(len(v[0])),component,34962,normalized)
        d['meshes'].append({'name':m['name'],'primitives':[{'attributes':aa,'indices':acc(m['indices'],'SCALAR',5123 if max(v[0] for v in m['indices'])<65536 else 5125,34963),'material':0}],'extras':{'vertex_regions':m['regions'],'lod':len(d['meshes'])}})
    node=next(n for n in d['nodes'] if 'mesh' in n);node.update(name='spearman_LOD0',mesh=0,skin=0)
    d['nodes'].append({'name':'spearman_LOD1','mesh':1,'skin':0});d['scenes'][d.get('scene',0)]['nodes'].append(len(d['nodes'])-1)
    d['extensionsUsed']=['KHR_mesh_quantization'];d['extensionsRequired']=['KHR_mesh_quantization']
    d['images']=[];d['textures']=[]
    for name in ['basecolor','normal','orm']:
        choices=[unit/f'spearman-{name}.{ext}' for ext in ['png','jpg','webp']]
        path=max((p for p in choices if p.exists()),key=lambda p:p.stat().st_mtime)
        if path.suffix=='.png':compact_png(path)
        mime={'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}[path.suffix]
        d['images'].append({'name':name,'mimeType':mime,'bufferView':view(path.read_bytes())})
        source=len(d['images'])-1
        if path.suffix=='.webp':
            d['textures'].append({'extensions':{'EXT_texture_webp':{'source':source}},'sampler':0})
            for key in ['extensionsUsed','extensionsRequired']:
                if 'EXT_texture_webp' not in d[key]:d[key].append('EXT_texture_webp')
        else:d['textures'].append({'source':source,'sampler':0})
    d['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
    team=d['asset']['extras']['team']
    d['materials']=[{'name':'Painted bronze, linen and crimson','pbrMetallicRoughness':{'baseColorTexture':{'index':0,'texCoord':0},'metallicRoughnessTexture':{'index':2,'texCoord':0},'metallicFactor':1,'roughnessFactor':1},'normalTexture':{'index':1,'texCoord':0},'occlusionTexture':{'index':2,'texCoord':0,'strength':.6},'doubleSided':True,'extras':{'team':team}}]
    master_px=struct.unpack_from('>II',(work/'basecolor-master.png').read_bytes(),16)[0]
    d['asset']['extras'].update(lod_meshes=['spearman_LOD0','spearman_LOD1'],default_lod=0,texture_master_size=master_px,look='painted',approved_motion_sha256=hashlib.sha256(g.path.read_bytes()).hexdigest())
    d['buffers']=[{'byteLength':len(blob)}];blob.extend(b'\0'*(-len(blob)%4));raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
    (unit/'spearman.glb').write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
    report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'triangles':{m['name']:len(m['indices'])//3 for m in meshes},'high_poly_bake':'Cycles CPU, selected-to-active NORMAL and AO, subdivision + geometric displacement','texture_master_px':master_px,'texture_delivery_px':1024}
    (work/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

#!/usr/bin/env python3
"""Validate Legatum's real-time unit contract directly from GLB JSON/BIN.

No dependencies. Checks actual geometry, hierarchy, pixels, animation samples and
skinned bounds; aesthetic flatness and recognisability still require visual review.
"""
import argparse, bisect, copy, json, math, struct
from pathlib import Path

CREDIT='0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum'
IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]

def multiply(a,b):
    return [sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4)]

def point(m,p):
    return tuple(sum(m[c*4+r]*p[c] for c in range(3))+m[12+r] for r in range(3))

def matrix(node):
    if 'matrix' in node:return node['matrix']
    x,y,z,w=node.get('rotation',[0,0,0,1]);sx,sy,sz=node.get('scale',[1,1,1])
    tx,ty,tz=node.get('translation',[0,0,0])
    return [(1-2*y*y-2*z*z)*sx,(2*x*y+2*w*z)*sx,(2*x*z-2*w*y)*sx,0,
            (2*x*y-2*w*z)*sy,(1-2*x*x-2*z*z)*sy,(2*y*z+2*w*x)*sy,0,
            (2*x*z+2*w*y)*sz,(2*y*z-2*w*x)*sz,(1-2*x*x-2*y*y)*sz,0,tx,ty,tz,1]

class GLB:
    def __init__(self,path):
        self.path=Path(path);data=self.path.read_bytes()
        magic,version,size=struct.unpack_from('<4sII',data)
        assert magic==b'glTF' and version==2 and size==len(data),'Invalid GLB header'
        pos=12;chunks=[]
        while pos<len(data):
            n,kind=struct.unpack_from('<II',data,pos);pos+=8
            assert n%4==0 and pos+n<=len(data),'Invalid chunk size'
            chunks.append((kind,data[pos:pos+n]));pos+=n
        assert chunks[0][0]==0x4e4f534a and len(chunks)==2 and chunks[1][0]==0x004e4942
        self.doc=json.loads(chunks[0][1]);self.bin=chunks[1][1];self.cache={}
    def accessor(self,i):
        if i in self.cache:return self.cache[i]
        a=self.doc['accessors'][i];view=self.doc['bufferViews'][a['bufferView']]
        assert 'sparse' not in a,'Sparse accessor unsupported by contract validator'
        fmt={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}[a['componentType']]
        count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        step=struct.calcsize(fmt)*count;stride=view.get('byteStride',step)
        offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        assert a['count']==0 or offset+(a['count']-1)*stride+step<=len(self.bin)
        vals=[struct.unpack_from('<'+fmt*count,self.bin,offset+n*stride) for n in range(a['count'])]
        if a.get('normalized'):
            maxval={5120:127,5121:255,5122:32767,5123:65535}[a['componentType']]
            vals=[tuple(max(-1,v/maxval) for v in row) for row in vals]
        assert all(math.isfinite(x) for row in vals for x in row),'Non-finite accessor'
        self.cache[i]=vals;return vals
    def worlds(self,animation=None,time=0):
        nodes=copy.deepcopy(self.doc['nodes'])
        if animation:
            for ch in animation['channels']:
                sampler=animation['samplers'][ch['sampler']];times=self.accessor(sampler['input'])
                values=self.accessor(sampler['output'])
                idx=max(0,min(len(times)-1,bisect.bisect_right([t[0] for t in times],time)-1))
                value=values[idx]
                if idx+1<len(times) and sampler.get('interpolation','LINEAR')=='LINEAR':
                    t=max(0,min(1,(time-times[idx][0])/(times[idx+1][0]-times[idx][0])))
                    a=values[idx];b=values[idx+1]
                    if ch['target']['path']=='rotation':
                        dot=sum(x*y for x,y in zip(a,b))
                        if dot<0:b=tuple(-x for x in b);dot=-dot
                        if dot<.9995:
                            angle=math.acos(min(1,dot));denom=math.sin(angle)
                            value=tuple((x*math.sin((1-t)*angle)+y*math.sin(t*angle))/denom for x,y in zip(a,b))
                        else:
                            v=tuple(x*(1-t)+y*t for x,y in zip(a,b));length=math.sqrt(sum(x*x for x in v));value=tuple(x/length for x in v)
                    else:value=tuple(x*(1-t)+y*t for x,y in zip(a,b))
                nodes[ch['target']['node']][ch['target']['path']]=value
        worlds={}
        def walk(i,parent):
            worlds[i]=multiply(parent,matrix(nodes[i]))
            for child in nodes[i].get('children',[]):walk(child,worlds[i])
        for root in self.doc['scenes'][self.doc.get('scene',0)]['nodes']:walk(root,IDENTITY)
        return worlds
    def vertices(self,animation=None,time=0,exclude=()):
        worlds=self.worlds(animation,time)
        for ni,node in enumerate(self.doc['nodes']):
            if 'mesh' not in node or node.get('name') in exclude:continue
            joint_matrices=None
            if 'skin' in node:
                skin=self.doc['skins'][node['skin']];inv=self.accessor(skin['inverseBindMatrices'])
                joint_matrices=[multiply(worlds[j],inv[k]) for k,j in enumerate(skin['joints'])]
            for prim in self.doc['meshes'][node['mesh']]['primitives']:
                attrs=prim['attributes'];positions=self.accessor(attrs['POSITION'])
                if joint_matrices:
                    joints=self.accessor(attrs['JOINTS_0']);weights=self.accessor(attrs['WEIGHTS_0'])
                    regions=self.doc['meshes'][node['mesh']].get('extras',{}).get('vertex_regions',[])
                    for vi,(p,js,ws) in enumerate(zip(positions,joints,weights)):
                        if any(r['part'] in exclude and r['start']<=vi<r['start']+r['count'] for r in regions):continue
                        transformed=[point(joint_matrices[int(j)],p) for j in js]
                        yield ni,tuple(sum(v[k]*w for v,w in zip(transformed,ws)) for k in range(3))
                else:
                    for p in positions:yield ni,point(worlds[ni],p)

def image_dimensions(data):
    """Read dimensions of PNG, JPEG and EXT_texture_webp encodings without dependencies."""
    if data[:8]==b'\x89PNG\r\n\x1a\n':return struct.unpack_from('>II',data,16)
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP':
        kind=data[12:16]
        if kind==b'VP8 ':return tuple(x&0x3fff for x in struct.unpack_from('<HH',data,26))
        if kind==b'VP8L':
            bits=struct.unpack_from('<I',data,21)[0];return (bits&0x3fff)+1,((bits>>14)&0x3fff)+1
        if kind==b'VP8X':return int.from_bytes(data[24:27],'little')+1,int.from_bytes(data[27:30],'little')+1
        raise ValueError('Unsupported WebP header')
    assert data[:2]==b'\xff\xd8','Expected PNG, JPEG or WebP'
    pos=2
    while pos<len(data):
        assert data[pos]==255,'Malformed JPEG marker'
        while data[pos]==255:pos+=1
        marker=data[pos];pos+=1
        if marker in (0xd8,0xd9):continue
        length=struct.unpack_from('>H',data,pos)[0]
        if marker in (0xc0,0xc1,0xc2):
            height,width=struct.unpack_from('>HH',data,pos+3);return width,height
        pos+=length
    raise ValueError('JPEG dimensions missing')

def validate(path):
    g=GLB(path);d=g.doc;errors=[];warnings=[]
    def require(test,message):
        if not test:errors.append(message)
    require(d['asset']['version']=='2.0','Must be glTF 2.0')
    require(Path(path).stat().st_size<2_000_000,'Shipping GLB must be under 2 MB (decimal)')
    require(len(d.get('buffers',[]))==1 and 'uri' not in d['buffers'][0],'Must be self-contained')
    extras=d['asset'].get('extras',{})
    require(d['asset'].get('copyright')==CREDIT and extras.get('credit')==CREDIT,'Missing exact credit')
    require(extras.get('license')=='CC-BY-SA-3.0','Missing licence in asset.extras')
    require(extras.get('up_axis')=='Y' and extras.get('forward')=='+Z' and extras.get('units')=='metres','Missing axis/metre declarations')
    require(Path(path).with_name('PROVENANCE.md').is_file(),'Missing adjacent PROVENANCE.md')
    require(Path(path).with_name('LICENSE-ART').is_file(),'Missing adjacent LICENSE-ART')
    nodes=d['nodes']
    skinned=[i for i,n in enumerate(nodes) if 'skin' in n]
    require(len(skinned)==2 and len(d.get('skins',[]))==1,'Exactly two LOD meshes must share one skin')
    require({nodes[i].get('name') for i in skinned}=={'spearman_LOD0','spearman_LOD1'},'Named LOD nodes required')
    require(all(nodes[i]['skin']==0 for i in skinned),'LODs must share skin 0')
    require('MSFT_lod' not in d.get('extensionsUsed',[]),'Do not use MSFT_lod')
    joints=set(j for skin in d.get('skins',[]) for j in skin['joints'])
    require(all(len(skin['joints'])<=40 for skin in d.get('skins',[])),'More than 40 joints')
    require(all(len(set(skin['joints']))==len(skin['joints']) for skin in d.get('skins',[])),'Duplicate joint index')
    tris=0;team_regions=[];lod_triangles={}
    require(len(d.get('meshes',[]))==2,'Must have exactly 2 LOD meshes')
    require({m.get('name') for m in d.get('meshes',[])}=={'spearman_LOD0','spearman_LOD1'},'Named LOD meshes required')
    require({nodes[i]['mesh'] for i in skinned}=={0,1},'Each LOD node must select a distinct mesh')
    require(all(nodes[i]['name']==d['meshes'][nodes[i]['mesh']].get('name') for i in skinned),'LOD node/mesh names must match')
    require(len(d.get('materials',[]))==1,'Must have exactly 1 material')
    draw_calls=sum(len(d['meshes'][n['mesh']]['primitives']) for n in nodes if 'mesh' in n)
    require(draw_calls==2 and all(len(m['primitives'])==1 for m in d['meshes']),'Exactly one draw call per LOD required')
    require(all(p.get('material')==0 for m in d['meshes'] for p in m['primitives']),'LODs must share material 0')
    for ni,node in enumerate(nodes):
        require(all(abs(v)>1e-6 for v in node.get('scale',[1,1,1])),'Zero-scaled node')
        if 'mesh' not in node:continue
        for prim in d['meshes'][node['mesh']]['primitives']:
            require(prim.get('mode',4)==4,'Only triangle primitives supported')
            count=d['accessors'][prim['indices']]['count'] if 'indices' in prim else d['accessors'][prim['attributes']['POSITION']]['count']
            tris+=count//3
            lod_triangles[node['name']]=count//3
            budget=10000 if node['name']=='spearman_LOD0' else 3000
            require(count//3<=budget,f"{node['name']} over budget: {count//3} > {budget}")
            require('TEXCOORD_0' in prim['attributes'],'Missing albedo UVs')
            require('COLOR_0' in prim['attributes'],'Missing team mask COLOR_0')
            if 'skin' in node:
                weights=g.accessor(prim['attributes']['WEIGHTS_0'])
                require(all(abs(sum(w)-1)<.001 for w in weights),'Weights do not sum to one')
    rigid_counts={}
    for mesh in d['meshes']:
        lod_rigid=set();lod_teams=set()
        regions=mesh.get('extras',{}).get('vertex_regions',[])
        require(bool(regions),'Missing auditable vertex_regions')
        for prim in mesh['primitives']:
            attrs=prim['attributes'];count=d['accessors'][attrs['POSITION']]['count']
            colors=g.accessor(attrs['COLOR_0']) if 'COLOR_0' in attrs else []
            weights=g.accessor(attrs['WEIGHTS_0']);js=g.accessor(attrs['JOINTS_0'])
            require(all(len(g.accessor(v))==count for v in attrs.values()),'Vertex attribute count mismatch')
            require(all(0<=c[0]<=1 and c[1:]==(0,0,1) for c in colors),'Invalid COLOR_0 team data')
            covered=[]
            for region in regions:
                start=region['start'];end=start+region['count']
                require(0<=start<end<=count,'Invalid vertex region range')
                if not 0<=start<end<=count:continue
                covered.extend(range(start,end))
                bone=region.get('bone');part=region['part']
                expected={'spear':'weapon_R','aspis':'shield_arm','Aspis back':'shield_arm','Aspis handgrip':'shield_arm','helmet':'helmet','crest':'helmet','crest_base':'helmet','Greek head':'head'}.get(part,region.get('bone'))
                if expected:
                    require(bone==expected,f'{part} must attach to {expected}')
                    valid=True
                    for i in range(start,end):
                        active=[int(j) for j,w in zip(js[i],weights[i]) if w>1e-6]
                        valid &= len(active)==1 and max(weights[i])==1
                        valid &= all(j<len(d['skins'][0]['joints']) and nodes[d['skins'][0]['joints'][j]].get('name')==expected for j in active)
                    require(valid,f'{part} must have single-bone unit weights to {expected}')
                    rigid_counts[part]=rigid_counts.get(part,0)+end-start
                    lod_rigid.add(part)
                if region.get('team'):
                    team_regions.append(region['team']);lod_teams.add(region['team'])
                    require(bool(colors) and all(colors[i][0]==1 for i in range(start,end)),f'{part} team mask must be one')
                elif colors:require(all(colors[i][0]==0 for i in range(start,end)),f'{part} non-team mask must be zero')
            require(sorted(covered)==list(range(count)),'vertex_regions must partition every vertex exactly once')
        require({'spear','aspis','helmet'}<=lod_rigid,f"{mesh['name']}: missing rigid props")
        require({'cloak trim','shield rim','crest'}<=lod_teams,f"{mesh['name']}: missing team regions")
    require({'spear','aspis','helmet'}<=set(rigid_counts),'Missing required rigid prop regions')
    require({'cloak trim','shield rim','crest'}<=set(team_regions),'team must cover cloak trim, shield rim and crest')
    require(extras.get('team',{}).get('attribute')=='COLOR_0' and extras.get('team',{}).get('channel')=='r','Missing team mask semantics')
    images=d.get('images',[]);require(len(images)==3,'Exactly three PBR atlas images required')
    texture_size=[]
    for im in images:
        require('bufferView' in im and im.get('mimeType') in ('image/png','image/jpeg','image/webp'),'PBR atlas must be embedded PNG, JPEG or WebP')
        if 'bufferView' in im:
            view=d['bufferViews'][im['bufferView']];off=view.get('byteOffset',0)
            png=g.bin[off:off+view['byteLength']]
            size=image_dimensions(png);texture_size.append(size)
            require(size==(1024,1024),'Every shipped texture must be 1024 square')
    require(extras.get('texture_master_px')==2048,'Declare 2048 master textures')
    for mat in d.get('materials',[]):
        pbr=mat.get('pbrMetallicRoughness',{})
        refs=[pbr.get('baseColorTexture'),mat.get('normalTexture'),pbr.get('metallicRoughnessTexture'),mat.get('occlusionTexture')]
        require(all(refs),'Base colour, normal, ORM and occlusion bindings required')
        if all(refs):
            require(all(t.get('texCoord',0)==0 for t in refs),'All maps must use UV0')
            require(refs[2]['index']==refs[3]['index'],'AO and metallic/roughness must share packed ORM')
            require(len({t['index'] for t in refs})==3,'Base colour, normal and ORM must be distinct')
        require('KHR_materials_unlit' not in mat.get('extensions',{}),'Material must accept runtime lighting')
        require(not any(mat.get('emissiveFactor',[0,0,0])),'No emission-projection material')
    animations=d.get('animations',[]);require(sorted(a.get('name') for a in animations)==sorted(['idle','walk','attack','hit','death']),'Exactly five named clips required')
    clips={}
    roots=set(d['scenes'][d.get('scene',0)]['nodes'])
    for a in animations:
        duration=0;loop_error=0
        for ch in a['channels']:
            sam=a['samplers'][ch['sampler']];times=[t[0] for t in g.accessor(sam['input'])];vals=g.accessor(sam['output'])
            require(sam.get('interpolation','LINEAR')=='LINEAR','Clips must be linearly sampled')
            require(abs(times[0])<1e-5 and all(abs(t*30-round(t*30))<1e-4 for t in times),'Animation samples must lie on 30 fps grid')
            require(all(abs(b-a-1/30)<1e-5 for a,b in zip(times,times[1:])),'Animation must include every 30 fps sample')
            duration=max(duration,times[-1])
            if ch['target']['node'] in roots:
                require(all(max(abs(x-y) for x,y in zip(v,vals[0]))<1e-5 for v in vals),'Root motion is forbidden')
            if ch['target']['path']=='scale':require(all(min(v)>1e-6 for v in vals),'Animated zero scale')
            diff=max(abs(x-y) for x,y in zip(vals[0],vals[-1]))
            if ch['target']['path']=='rotation':diff=min(diff,max(abs(x+y) for x,y in zip(vals[0],vals[-1])))
            loop_error=max(loop_error,diff)
        if a['name'] in {'idle','walk'}:require(loop_error<1e-4,f'{a["name"]} loop endpoint mismatch: {loop_error}')
        clips[a['name']]={'duration_s':round(duration,6),'fps':30,'loop_endpoint_max_error':round(loop_error,7)}
    if any(len(skin['joints'])!=d['accessors'][skin['inverseBindMatrices']]['count'] for skin in d.get('skins',[])):
        errors.append('Inverse-bind count must equal joint count')
        return {'valid':False,'errors':errors}
    idle=next((a for a in animations if a['name']=='idle'),None)
    pts=[p for _,p in g.vertices(idle,0,exclude=('spear',))]
    minimum=[min(p[i] for p in pts) for i in range(3)];maximum=[max(p[i] for p in pts) for i in range(3)]
    height=maximum[1]-minimum[1]
    require(1.65<=height<=1.95,f'Figure must be about 1.8m: {height:.3f}')
    bodypts=[p for ni,p in g.vertices(idle,0) if ni in skinned]
    feet=[p for p in bodypts if p[1]<min(v[1] for v in bodypts)+.035]
    feet_centre=[(min(p[i] for p in feet)+max(p[i] for p in feet))/2 for i in range(3)]
    require(abs(min(p[1] for p in feet))<.02,'Feet must sit at y=0')
    require(abs(feet_centre[0])<.15 and abs(feet_centre[2])<.15,'Origin must be at feet centre')
    # Mesh toes establish +Z, independently of metadata (front-most low vertex).
    require(max(p[2] for p in feet)>abs(min(p[2] for p in feet)), 'Toe geometry must face +Z')
    warnings.append('Premium quality, material separation, close-up faceting and animation collisions require visual review. Runtime must select one LOD.')
    return {'valid':not errors,'glb':str(Path(path).resolve()),'bytes':Path(path).stat().st_size,'triangles':lod_triangles,'total_stored_triangles':tris,'joints':len(joints),'skinned_meshes':len(skinned),'atlas_px':texture_size,'texture_master_px':extras.get('texture_master_px'),'texture_bytes':[d['bufferViews'][im['bufferView']]['byteLength'] for im in images],'figure_height_m':round(height,4),'feet_centre_m':[round(v,4) for v in feet_centre],'meshes':len(d['meshes']),'materials':len(d['materials']),'draw_calls_per_lod':1,'stored_primitives':draw_calls,'team_regions':team_regions,'rigid_vertices':rigid_counts,'clips':clips,'errors':errors,'review_required':warnings}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('glb',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    result=validate(args.glb);out=json.dumps(result,indent=2);print(out)
    if args.output:args.output.write_text(out+'\n')
    raise SystemExit(0 if result['valid'] else 1)

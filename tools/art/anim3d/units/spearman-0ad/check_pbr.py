"""Exact round-6 rig/animation comparison and vectorised 120 fps contact audit."""
import argparse, copy, hashlib, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB

def payload(g,i):
    a=g.doc['accessors'][i];v=g.doc['bufferViews'][a['bufferView']]
    assert 'byteStride' not in v
    return g.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]

def check(source,output):
    before,after=GLB(source),GLB(output);frozen={};errors=[]
    for old,new in zip(before.doc['animations'],after.doc['animations']):
        assert old['name']==new['name'] and old['channels']==new['channels']
        assert len(old['samplers'])==len(new['samplers'])
        digest=hashlib.sha256()
        for a,b in zip(old['samplers'],new['samplers']):
            assert a.get('interpolation')==b.get('interpolation')
            for key in ('input','output'):
                x,y=payload(before,a[key]),payload(after,b[key]);assert x==y,(old['name'],key);digest.update(y)
        frozen[old['name']]={'byte_identical':True,'sha256':digest.hexdigest()}
    assert payload(before,before.doc['skins'][0]['inverseBindMatrices'])==payload(after,after.doc['skins'][0]['inverseBindMatrices'])
    assert before.doc['skins'][0]['joints']==after.doc['skins'][0]['joints']
    for i,old in enumerate(before.doc['nodes']):
        new=copy.deepcopy(after.doc['nodes'][i]);old=copy.deepcopy(old)
        for n in (old,new):
            if 'mesh' in n:n.pop('name',None)
            n.pop('mesh',None)
        assert old==new,('changed original node',i)
    skin=after.doc['skins'][0];inv=np.array(after.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    geometry=[]
    for m in after.doc['meshes']:
        p=m['primitives'][0];a=p['attributes'];pos=np.array(after.accessor(a['POSITION']));pos=np.column_stack((pos,np.ones(len(pos))))
        geometry.append((m,pos,np.array(after.accessor(a['JOINTS_0']),dtype=int),np.array(after.accessor(a['WEIGHTS_0']))))
    contact={}
    for clip in after.doc['animations']:
        duration=max(after.accessor(s['input'])[-1][0] for s in clip['samplers']);count=round(duration*120)
        rows={m['name']:{'minimum_m':float('inf')} for m,*_ in geometry}
        for f in range(count+1):
            worlds=after.worlds(clip,duration*f/count);wm=np.array([worlds[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1);jm=wm@inv
            for m,pos,js,ws in geometry:
                y=np.zeros(len(pos))
                for k in range(4):y+=np.einsum('ij,ij->i',jm[js[:,k],1,:],pos)*ws[:,k]
                i=int(y.argmin());row=rows[m['name']]
                if y[i]<row['minimum_m']:
                    region=next(r for r in m['extras']['vertex_regions'] if r['start']<=i<r['start']+r['count'])
                    row.update(minimum_m=float(y[i]),time_s=duration*f/count,part=region['part'])
                if f==count and clip['name']=='death':
                    ids=[i for r in m['extras']['vertex_regions'] if r['part']=='body' for i in range(r['start'],r['start']+r['count'])]
                    row['final_body_ground_m']=float(y[ids].min())
        for name,row in rows.items():
            if row['minimum_m']<-.002:errors.append(f'{clip["name"]} {name} penetrates floor: {row}')
        contact[clip['name']]={'samples_at_120fps':count+1,'lods':rows}
    return {'valid':not errors,'approved_source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'delivered_sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),'frozen_animation':frozen,'rig_and_inverse_binds_identical':True,'contact':contact,'errors':errors,'limits':'Contact only; no mesh/mesh collision claim. All clip bytes and original hierarchy transforms match round 6.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('glb',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    r=check(a.source,a.glb);raw=json.dumps(r,indent=2);print(raw)
    if a.output:a.output.write_text(raw+'\n')
    raise SystemExit(0 if r['valid'] else 1)

"""Audit transferred MPFB weights through all five locked clips at 30 Hz.

Reports minimum singular value of the blended skin transform around shoulders,
elbows and knees. This detects severe LBS volume collapse, not intersections,
surface quality or every visible form of candy wrapping. Review the joint sheet.
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def check(path):
    g=GLB(path);d=g.doc;skin=d['skins'][0]
    bones=[d['nodes'][j]['name'] for j in skin['joints']]
    inv=np.array(g.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    report={};errors=[]
    for mesh in d['meshes']:
        attrs=mesh['primitives'][0]['attributes']
        js=np.asarray(g.accessor(attrs['JOINTS_0']),int);ws=np.asarray(g.accessor(attrs['WEIGHTS_0']))
        anatomy=np.zeros(len(js),bool)
        for r in mesh['extras']['vertex_regions']:
            if r['part']=='heroicbody':anatomy[r['start']:r['start']+r['count']]=True
        groups={}
        for label,names in [('shoulders',['arm_L','arm_R','shoulder_L','shoulder_R']),
                ('elbows',['forearm_L','forearm_R']),('knees',['leg_L','leg_R','thigh_L','thigh_R'])]:
            ids=[bones.index(n) for n in names]
            groups[label]=anatomy&np.any(np.isin(js,ids)&(ws>.05),axis=1)
            if not groups[label].any():errors.append(f'{mesh["name"]}: no {label} anatomy')
        clips={}
        for clip in d['animations']:
            duration=max(g.accessor(s['input'])[-1][0] for s in clip['samplers'])
            lows={name:{'minimum_axis_scale':1.,'time_s':0.} for name in groups}
            for t in np.linspace(0,duration,round(duration*30)+1):
                worlds=g.worlds(clip,float(t))
                mat=np.asarray([worlds[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1)@inv
                for name,mask in groups.items():
                    blend=np.einsum('nijk,ni->njk',mat[js[mask],:3,:3],ws[mask])
                    smallest=np.linalg.svd(blend,compute_uv=False)[:,-1]
                    value=float(smallest.min())
                    if value<lows[name]['minimum_axis_scale']:lows[name]={'minimum_axis_scale':value,'time_s':float(t)}
                    if value<.20:errors.append(f'{mesh["name"]}/{clip["name"]}/{name}: severe collapse at {t:.3f}s')
            clips[clip['name']]=lows
        report[mesh['name']]=clips
    return {'valid':not errors,'errors':errors,'lods':report,
        'asset_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'scope':'30 Hz LBS axis-collapse indicator; visual joint and intersection review also required.'}


if __name__=='__main__':
    result=check(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(not result['valid'])

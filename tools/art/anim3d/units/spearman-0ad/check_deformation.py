"""Measure LBS compression at anatomy joints; flag samples for visual inspection.

A low singular value detects the classic candy-wrapper collapse of blended
rotation matrices. It does not prove absence of garment/body intersections.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB


def check(path):
    g=GLB(path);d=g.doc;mesh=next(m for m in d['meshes'] if m['name']=='spearman_LOD0')
    attrs=mesh['primitives'][0]['attributes'];skin=d['skins'][0]
    names=[d['nodes'][j]['name'] for j in skin['joints']]
    js=np.array(g.accessor(attrs['JOINTS_0']),dtype=int);ws=np.array(g.accessor(attrs['WEIGHTS_0']))
    body=np.zeros(len(js),dtype=bool)
    for r in mesh['extras']['vertex_regions']:
        if r['part']=='body' and not r.get('team'):body[r['start']:r['start']+r['count']]=True
    groups={'shoulders':('shoulder_L','arm_L','shoulder_R','arm_R'),
            'elbows':('forearm_L','forearm_R'), 'knees':('leg_L','leg_R')}
    masks={name:body & (np.sum(ws*np.isin(js,[names.index(b) for b in bones]),axis=1)>.15) for name,bones in groups.items()}
    inv=np.array(g.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    report={}
    for clip in d['animations']:
        duration=max(g.accessor(s['input'])[-1][0] for s in clip['samplers']);steps=round(duration*60)
        rows={name:{'minimum_axis_scale':1.,'sample_time_s':0.,'vertices':int(mask.sum())} for name,mask in masks.items()}
        for frame in range(steps+1):
            time=duration*frame/steps;world=g.worlds(clip,time)
            matrices=np.array([world[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1)@inv
            for name,mask in masks.items():
                blend=sum(matrices[js[mask,k],:3,:3]*ws[mask,k,None,None] for k in range(4))
                values=np.linalg.svd(blend,compute_uv=False)[:,-1]
                worst=float(values.min())
                if worst<rows[name]['minimum_axis_scale']:
                    vertex=int(np.flatnonzero(mask)[int(values.argmin())])
                    candidates=[(float(w),names[int(j)]) for j,w in zip(js[vertex],ws[vertex]) if names[int(j)] in groups[name]]
                    joint=max(candidates)[1]
                    rows[name].update(minimum_axis_scale=worst,sample_time_s=time,percentile_1=float(np.percentile(values,1)),joint=joint)
        report[clip['name']]=rows
    return {'sampling_fps':60,'lod':'spearman_LOD0','clips':report,
            'interpretation':'1 means no local LBS volume collapse; near 0 is severe compression. Inspect worst poses visually. No collision or aesthetic pass implied.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('glb',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    r=check(a.glb);raw=json.dumps(r,indent=2);print(raw)
    if a.output:a.output.write_text(raw+'\n')

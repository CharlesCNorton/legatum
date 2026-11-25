"""Vectorized 120 Hz contact audit, attributed to individual art regions."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB

def check(path):
    g=GLB(path);d=g.doc;skin=d['skins'][0];inv=np.array(g.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    report={};fail=[]
    for mesh in d['meshes']:
        at=mesh['primitives'][0]['attributes'];pos=np.array(g.accessor(at['POSITION']));pos=np.column_stack([pos,np.ones(len(pos))]);js=np.array(g.accessor(at['JOINTS_0']),dtype=int);ws=np.array(g.accessor(at['WEIGHTS_0']))
        region=mesh['extras']['vertex_regions'];parts=np.empty(len(pos),object)
        for r in region:parts[r['start']:r['start']+r['count']]=r['part']
        clips={}
        for clip in d['animations']:
            duration=max(g.accessor(s['input'])[-1][0] for s in clip['samplers']);lows={};low=100
            for t in np.linspace(0,duration,round(duration*120)+1):
                worlds=g.worlds(clip,float(t));mat=np.array([worlds[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1)@inv
                pp=np.einsum('nijk,nk,ni->nj',mat[js],pos,ws)
                i=int(np.argmin(pp[:,1]));low=min(low,float(pp[i,1]));part=parts[i];lows[part]=min(lows.get(part,100),float(pp[i,1]))
            clips[clip['name']]={'min_ground_m':low,'lowest_regions':lows}
            if low<-.002:fail.append(f'{mesh["name"]}/{clip["name"]}: {low:.6f} m')
        report[mesh['name']]=clips
    return {'valid':not fail,'lods':report,'errors':fail,'scope':'Ground only, not mesh intersections. Skeleton/motion never corrected here.'}
if __name__=='__main__':
    result=check(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(not result['valid'])

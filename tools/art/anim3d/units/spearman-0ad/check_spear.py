"""Check death spear mesh-edge crossings at 120 fps (requires NumPy).

The first 0.1 s contains the authored hand grip as the weapon releases. From
0.1 s onward, no spear edge may cross a triangle of the figure or shield.
This is not a general body self-intersection or coplanar-contact solver.
"""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('glb',type=Path);parser.add_argument('--output',type=Path)
args=parser.parse_args()
g=GLB(args.glb);d=g.doc;a=next(a for a in d['animations'] if a['name']=='death')
rs=d['meshes'][0]['extras']['vertex_regions'];pr=d['meshes'][0]['primitives'][0];idx=np.array(g.accessor(pr['indices'])).reshape(-1,3)
spear=np.array([i for r in rs if r['part']=='spear' for i in range(r['start'],r['start']+r['count'])]);targets=np.array([i for r in rs if r['part']!='spear' for i in range(r['start'],r['start']+r['count'])]);faces=idx[np.all(np.isin(idx,targets),axis=1)]
spfaces=idx[np.all(np.isin(idx,spear),axis=1)];edges=np.unique(np.sort(np.concatenate([spfaces[:,[0,1]],spfaces[:,[1,2]],spfaces[:,[2,0]]]),axis=1),axis=0)
duration=max(g.accessor(s["input"])[-1][0] for s in a["samplers"])
samples=round(duration*120)+1
hits=[]
for f in range(samples):
 t=duration*f/(samples-1);vs=np.array([p for _,p in g.vertices(a,t)]);tris=vs[faces];lo=vs[spear].min(axis=0);hi=vs[spear].max(axis=0)
 tris=tris[np.all(tris.max(axis=1)>=lo,axis=1)&np.all(tris.min(axis=1)<=hi,axis=1)]
 if len(tris)==0:continue
 e1=tris[:,1]-tris[:,0];e2=tris[:,2]-tris[:,0]
 for x,y in edges:
  v=vs[y]-vs[x];h=np.cross(v,e2);det=np.sum(e1*h,axis=1);valid=np.abs(det)>1e-10
  inv=np.divide(1,det,out=np.zeros_like(det),where=valid);s=vs[x]-tris[:,0];u=inv*np.sum(s*h,axis=1);q=np.cross(s,e1);vv=inv*np.sum(v*q,axis=1);tt=inv*np.sum(e2*q,axis=1)
  if np.any(valid&(u>=0)&(vv>=0)&(u+vv<=1)&(tt>0)&(tt<1)):
   hits.append(round(t,4));break
failures=[t for t in hits if t>=.1]
result={'valid':not failures,'sample_count':samples,'grip_release_contact_times': [t for t in hits if t<.1],
        'post_release_intersection_times':failures,
        'limits':'Spear mesh edges against figure/shield triangles; excludes first 0.1 s grip contact, coplanar contact and body self-intersections.'}
raw=json.dumps(result,indent=2);print(raw)
if args.output:args.output.write_text(raw+'\n')
raise SystemExit(bool(failures))

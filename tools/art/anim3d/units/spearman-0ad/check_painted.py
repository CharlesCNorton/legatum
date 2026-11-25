"""Exact approved-motion and skeleton comparison, independent of art buffers."""
import sys, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB

def fingerprint(g):
    d=g.doc
    # Mesh node names/layout may change. Bone transforms, parents and root do not.
    joints=d['skins'][0]['joints'];used=set(joints)
    parents={c:i for i,n in enumerate(d['nodes']) for c in n.get('children',[])}
    for j in joints:
        while j in parents:j=parents[j];used.add(j)
    nodes={i:{k:v for k,v in d['nodes'][i].items() if k!='children'} for i in sorted(used)}
    hierarchy={i:parents.get(i) for i in sorted(used)}
    clips={}
    for a in d['animations']:
        sam=[{**{k:v for k,v in s.items() if k not in {'input','output'}},'input':g.accessor(s['input']),'output':g.accessor(s['output'])} for s in a['samplers']]
        clips[a['name']]={'channels':a['channels'],'samplers':sam}
    data={'nodes':nodes,'parents':hierarchy,'joints':joints,'inverse_bind':g.accessor(d['skins'][0]['inverseBindMatrices']),'clips':clips}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
if __name__=='__main__':
    before=GLB(sys.argv[1]);after=GLB(sys.argv[2]);a=fingerprint(before);b=fingerprint(after)
    print(json.dumps({'identical':a==b,'approved_motion_skeleton_sha256':a,'delivered_motion_skeleton_sha256':b},indent=2));assert a==b

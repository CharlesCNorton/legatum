"""Fit rest geometry to the approved animation's ground envelope, without new keys.
Each sampled posed ground plane is a linear half-space in each vertex's bind space.
Projection changes only mesh vertices; joint transforms and weights remain untouched.
"""
import numpy as np

def fit(objects,g,bones):
    skin=g.doc['skins'][0];inv=np.array(g.accessor(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    mats=[]
    for clip in g.doc['animations']:
        duration=max(g.accessor(s['input'])[-1][0] for s in clip['samplers'])
        for t in np.linspace(0,duration,round(duration*120)+1):
            worlds=g.worlds(clip,float(t));m=np.array([worlds[j] for j in skin['joints']]).reshape(-1,4,4).transpose(0,2,1)@inv;mats.append(m[:,1,:])
    vertices=[];joints=[];weights=[]
    for ob in objects:
        for v in ob.data.vertices:
            vertices.append(v)
            ww=sorted([(bones.index(ob.vertex_groups[x.group].name),x.weight) for x in v.groups if x.weight>1e-6 and ob.vertex_groups[x.group].name in bones],key=lambda x:-x[1])[:4]
            total=sum(w for _,w in ww);joints.append([j for j,w in ww]+[0]*(4-len(ww)));weights.append([w/total for j,w in ww]+[0]*(4-len(ww)))
    xyz=np.array([tuple(v.co) for v in vertices]);before=xyz.copy();js=np.array(joints);ws=np.array(weights)
    for _ in range(4):
        worst=0
        for m in mats:
            plane=np.einsum('nij,ni->nj',m[js],ws);height=(plane[:,:3]*xyz).sum(1)+plane[:,3];need=np.maximum(0,-.0005-height);worst=max(worst,float(need.max()))
            ids=need>0
            xyz[ids]+=plane[ids,:3]*(need[ids]/(plane[ids,:3]**2).sum(1))[:,None]
        if worst<.00005:break
    for v,p in zip(vertices,xyz):v.co=p
    for ob in objects:ob.data.update()
    delta=np.linalg.norm(xyz-before,axis=1)
    report={'changed_vertices':int((delta>1e-7).sum()),'max_bind_adjustment_m':float(delta.max()),'last_projection_m':worst}
    print('REST_CONTACT_FIT',report,flush=True);return report

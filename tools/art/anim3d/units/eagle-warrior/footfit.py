"""Fit native weighted foot anatomy to the real sandal volume before projection."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def fit_foot_undersides():
    sc=bpy.context.scene;body=bpy.data.objects['GEO-MPFB-anatomy'];rig=bpy.data.objects['RIG-eagle-warrior']
    bpy.context.view_layer.update()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    bounds={}
    for side in ['l','r']:
        names={'foot_'+side,'ball_'+side}
        points=[]
        for v in me.vertices:
            weight=sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in names)
            if weight>.8:points.append(ev.matrix_world@v.co)
        assert points,side
        bounds[side]=([min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)])
    ev.to_mesh_clear();count=0
    for v in body.data.vertices:
        groups={body.vertex_groups[g.group].name:g.weight for g in v.groups}
        weights={s:sum(w for n,w in groups.items() if n in {'foot_'+s,'ball_'+s}) for s in ['l','r']}
        side=max(weights,key=weights.get);weight=weights[side]
        if weight<.01:continue
        transforms=[(w,rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n,w in groups.items() if n in rig.pose.bones]
        total=sum(w for w,_ in transforms)
        if not total:continue
        deform=Matrix([[sum(w*m[r][c] for w,m in transforms)/total for c in range(4)] for r in range(4)])
        world=body.matrix_world@deform@v.co
        lo,hi=bounds[side];sole=bpy.data.objects['GEO-Sandal sole '+side].matrix_world.translation
        # Preserve native heel, arch and individual toes with one full-volume
        # affine fit, then blend the ankle transition by the original skin weights.
        half_width=.084 if side=='r' else .071
        target_lo=sole+Vector((-half_width,-.100,.012));target_hi=sole+Vector((half_width,.100,.092))
        target=Vector(tuple(target_lo[i]+(world[i]-lo[i])/max(.001,hi[i]-lo[i])*(target_hi[i]-target_lo[i]) for i in range(3)))
        target=world.lerp(target,min(1,weight*1.3))
        v.co=deform.inverted()@body.matrix_world.inverted()@target;count+=1
    sc['foot_underside_fit']='native masked foot bounds fitted to actual sandal volume; original topology/weights retained'
    bpy.context.view_layer.update();print('FOOT_FIT',count,bounds,flush=True)

"""Inspect saved 3D geometry, static base, source binding, equipment and terminal pose."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/legionary';V=R/'review/3d-v2';records=[];failures=[];warnings=[]
source=hashlib.sha256((M/'legionary.blend').read_bytes()).hexdigest()
for clip in ['idle','move','attack','hit','death']:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Legionary MPFB game_engine'];base=bpy.data.objects['Stationary cream stone'];initial=base.matrix_world.copy()
    assert len(rig.data.bones)==53;assert len(bpy.data.objects['MPFB anatomical male • original topology'].data.vertices)==19158
    assert sc['source_master_sha256']==source
    samples=json.loads(sc['sample_frames']);previous=None
    for i,f in enumerate(samples):
        sc.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();assert base.matrix_world==initial
        for o in sc.objects:
            assert min(abs(v) for v in o.scale)>.001,(clip,i,o.name,'degenerate scale')
        meshes={};low=100;bodylow=100;highest=-100
        for o in sc.objects:
            if o.type not in ['MESH','CURVE'] or o.hide_render:continue
            ev=o.evaluated_get(dg);me=ev.to_mesh();verts=[ev.matrix_world@v.co for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];ev.to_mesh_clear()
            if not verts:continue
            meshes[o.name]=(verts,polys)
            if o.name!='Stationary cream stone':
                lo=min(v.z for v in verts);hi=max(v.z for v in verts);low=min(low,lo);highest=max(highest,hi)
                if o.name.startswith('MPFB anatomical'):bodylow=lo
        if low<.075:failures.append(f'{clip}/{i}: geometry below base top {low:.4f}')
        # Ray-test the pilum shaft and shank against rigid visible armour and shield.
        collisions=[]
        for name in ['GEO-pilum ash shaft','GEO-pilum long iron shank']:
            ob=bpy.data.objects[name];pts=ob.data.splines[0].points;start=ob.matrix_world@Vector(pts[0].co[:3]);end=ob.matrix_world@Vector(pts[-1].co[:3]);direction=end-start
            for target,(verts,polys) in meshes.items():
                if target.startswith(('GEO-lorica iron band','GEO-bronze helmet bowl','GEO-scutum painted convex')):
                    tree=BVHTree.FromPolygons(verts,polys)
                    if tree.ray_cast(start,direction.normalized(),direction.length)[0] is not None:collisions.append(target)
        if clip!='death' or i==0:
            ob=bpy.data.objects['GEO-pilum ash shaft'];pts=ob.data.splines[0].points;a=ob.matrix_world@Vector(pts[0].co[:3]);b=ob.matrix_world@Vector(pts[-1].co[:3]);hand=rig.pose.bones['hand_r'];palm=rig.matrix_world@((hand.head+hand.tail)*.5);v=b-a;nearest=a+v*max(0,min(1,(palm-a).dot(v)/v.length_squared));distance=(palm-nearest).length
            if distance>.065:failures.append(f'{clip}/{i}: hand-to-shaft distance {distance:.4f}')
        if collisions:failures.append(f'{clip}/{i}: pilum intersects {collisions}')
        matrices={o.name:[list(row) for row in o.matrix_world] for o in sc.objects};matrices.update({p.name:[list(row) for row in p.matrix] for p in rig.pose.bones})
        if clip=='death' and i==len(samples)-1:assert matrices==previous,'Terminal matrices differ'
        previous=matrices;records.append({'clip':clip,'frame':i,'geometry_min_z':round(low,5),'body_min_z':round(bodylow,5),'max_z':round(highest,5),'pilum_collisions':collisions})
    if clip=='death' and bodylow>.18:warnings.append(f'Death body minimum {bodylow:.3f}; inspect contact')
result={'status':'FAIL' if failures else 'PASS','failures':failures,'warnings':warnings,'records':records,'limits':'Shaft centreline/rigid mesh test; not a full cloth/skin collision solver. Authored hem follow through, no cloth simulation.'}
(V/'legionary-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert not failures,'Fix geometry audit failures'

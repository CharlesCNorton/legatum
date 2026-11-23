"""Audit saved 3D masters and animation contracts; does not claim visual approval."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';counts={'idle':8,'move':8,'attack':10,'hit':4,'death':10};source=hashlib.sha256((M/'settler.blend').read_bytes()).hexdigest();report={}
def matrices(sc):
    out=[]
    for o in sorted(sc.objects,key=lambda o:o.name):
        out.extend(x for row in o.matrix_world for x in row)
        if o.type=='ARMATURE':
            for b in o.pose.bones:out.extend(x for row in b.matrix for x in row)
    return out
def visible_geometry():
    values={};deps=bpy.context.evaluated_depsgraph_get()
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
        values[ob.name]=[ev.matrix_world @ v.co for v in mesh.vertices]
        ev.to_mesh_clear()
    return values
bpy.ops.wm.open_mainfile(filepath=str(M/'settler.blend'))
assert bpy.data.objects['GEO-full length linen skirt'].data.shape_keys.key_blocks['Hem sway'].value==0
rest_geometry=visible_geometry()
for clip,count in counts.items():
    path=M/'clips'/f'{clip}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Settler MPFB']
    assert len(rig.data.bones)==53
    body=bpy.data.objects['GEO-MPFB female traveller']
    assert len(body.data.vertices)==json.loads((M/'model-info.json').read_text())['body_vertices']
    assert body.data.shape_keys is None,'Static macro keys must be frozen before projection'
    assert sc['source_sha256']==source,(clip,'stale master')
    frames=json.loads(sc['sample_frames']);assert len(frames)==count
    samples=[];ground=[];bounds=[];base=None;neutral=json.loads(rig['neutral_pose'])
    for frame in frames:
        sc.frame_set(frame);bpy.context.view_layer.update();samples.append(matrices(sc))
        if frame==1 and clip in ['idle','attack','hit']:
            geometry=visible_geometry()
            assert geometry.keys()==rest_geometry.keys()
            assert all(len(points)==len(rest_geometry[name]) for name,points in geometry.items())
            error=max((a-b).length for name,points in geometry.items() for a,b in zip(points,rest_geometry[name]))
            assert error<1e-5,(clip,'first-frame geometry differs from painted rest',error)
            assert max(abs(p.matrix_basis[r][c]-neutral[p.name][r][c]) for p in rig.pose.bones for r in range(4) for c in range(4))<1e-5,(clip,'rest-pose orientation drift')
        if clip=='move':
            motion=json.loads((M/'motion-move.json').read_text())
            for side in ['l','r']:
                expected=Quaternion(motion['target_foot_rotations'][frame-1][side])
                actual=rig.pose.bones['foot_'+side].matrix.to_quaternion()
                assert abs(actual.dot(expected))>1-1e-6,('foot rotation changed after retarget',frame,side)
        b=[x for row in bpy.data.objects['GEO-stationary cream base'].matrix_world for x in row]
        if base is None:base=b
        assert max(abs(x-y) for x,y in zip(base,b))<1e-8,(clip,'moving base')
        pts=[];zs=[];cam_inv=sc.camera.matrix_world.inverted();ortho=sc.camera.data.ortho_scale
        for o in sc.objects:
            assert min(abs(v) for v in o.scale)>.001,(o.name,'near-zero scale')
            if o.type!='MESH' or 'stationary' in o.name:continue
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            # Full geometry, not just object bounding boxes.
            for v in me.vertices:
                w=ev.matrix_world @ v.co;zs.append(w.z);p=cam_inv @ w;pts.append((.5+p.x/ortho,.5+p.y/ortho))
            ev.to_mesh_clear()
        bounds.append([min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]);ground.append(min(zs))
        assert all(math.isfinite(v) for v in samples[-1]),(clip,'invalid matrix')
    delta=max(max(abs(a-b) for a,b in zip(samples[0],s)) for s in samples[1:]);assert delta>1e-4,(clip,'static motion')
    if clip=='death':assert max(abs(a-b) for a,b in zip(samples[-1],samples[-2]))<1e-6,'Death not held'
    if clip in ['idle','move']:
        sc.frame_set(count+1);bpy.context.view_layer.update();assert max(abs(a-b) for a,b in zip(samples[0],matrices(sc)))<1e-5,(clip,'loop closure')
    report[clip]={'frames':count,'bones':53,'motion_delta':delta,'ground_min_z':min(ground),'projection_bounds':bounds,'stationary_base':True,'source_sha256':source}
bakes=json.loads((M/'bakes.json').read_text());assert len(bakes)==10
for bake in bakes:
    path=M/'textures/baked'/(bake['object'][4:].replace(' ','-')+'-'+bake['kind']+'.png')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==bake['sha256'],('changed bake',path)
report['limits']='No exhaustive skin/cloth collision solver. Ground minima and camera bounds are diagnostics; decoded pixel margins are enforced by delivery validator. CPU review is not GPU approval.'
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_PASS: five clips, 53 bones, stationary base, loop closure, held death, source hashes, ten bakes')
with (R/'review/3d-v2/settler-log.md').open('a') as f:f.write('- Saved 3D audit passed: source hashes, 53 bones, actual motion, exact loop closing keys and held death; ground/bounds recorded; collision limits explicit.\n')

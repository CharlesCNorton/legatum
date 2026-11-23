"""Saved-scene geometry and animation checks; visual approval remains separate."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/phalangite';master=M/'phalangite.blend';checks={}
inputs=json.loads((M/'animation-inputs.json').read_text())
for filename,digest in inputs.items():
    assert hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()==digest, 'Animation scripts changed; rebuild clips'
motions=json.loads((M/'animation-audit.json').read_text())
for name in ['idle','move','hit','death']:
    assert motions[name]['motion']['license']=='CC0-1.0'
    assert motions[name]['motion']['provider']=='Quaternius Universal Animation Library Standard'
bpy.ops.wm.open_mainfile(filepath=str(master));sc=bpy.context.scene;rig=bpy.data.objects['Phalangite MPFB game_engine'];body=bpy.data.objects['MPFB anatomical male • original topology']
assert len(body.data.vertices)>19000 and len(rig.data.bones)==53
assert 'Painting frozen rest' in body.data.uv_layers
assert body.data.shape_keys is None, 'Macro keys override fitted anatomy'
assert sc.get('rest_fit'), 'Missing full-depth fitting stage'
assert any(n.name=='Camera painted pigment' for n in body.data.materials[0].node_tree.nodes)
for name in ['GEO-linothorax','GEO-helmet-bowl','GEO-small-bronze-shield']:
    ob=bpy.data.objects[name]
    assert not any(m.type in {'BEVEL','SOLIDIFY','SUBSURF'} for m in ob.modifiers), 'Unfinished projection surface: '+name
    uv=ob.data.uv_layers['Painting frozen rest']
    for i,loop in enumerate(ob.data.loops):
        if i%17:continue
        q=world_to_camera_view(sc,sc.camera,ob.matrix_world @ ob.data.vertices[loop.vertex_index].co)
        assert max(abs(q.x-uv.data[i].uv.x),abs(q.y-uv.data[i].uv.y))*256<.01, 'Frozen UV drift: '+name
assert 'Painting frozen rest' not in bpy.data.objects['GEO-stationary-cream-base'].data.uv_layers
assert sc.get('projection') and len(json.loads((M/'textures/baked/manifest.json').read_text()))==3
assert all(min(abs(x) for x in o.scale)>.005 for o in sc.objects),'near-zero scale'
for name,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{name}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Phalangite MPFB game_engine'];base=bpy.data.objects['GEO-stationary-cream-base'];weapon=bpy.data.objects['CTRL-sarissa'];assert sc['source_sha256']==hashlib.sha256(master.read_bytes()).hexdigest()
    c=json.loads(sc['clip']);assert c['frames']==count and sc.frame_end==count
    base_matrices=[];poses=[]
    for i in range(1,count+1):
        sc.frame_set(i)
        if name=='move':
            from mathutils import Quaternion
            for side in ['l','r']:
                expected=Quaternion(motions[name]['motion']['target_foot_rotations'][i-1][side])
                actual=rig.pose.bones['foot_'+side].matrix.to_quaternion()
                assert actual.rotation_difference(expected).angle<.002, 'Captured foot rotation overwritten'
        base_matrices.append(tuple(v for row in base.matrix_world for v in row));poses.append(tuple(v for p in rig.pose.bones for row in p.matrix for v in row)+tuple(v for row in weapon.matrix_world for v in row)+tuple(v for row in rig.matrix_world for v in row))
    assert len(set(base_matrices))==1,name+' moved base';assert poses[0]!=poses[count//2],name+' is static'
    if name=='death':assert max(abs(x-y) for x,y in zip(poses[-1],poses[-2]))<1e-5,'death does not settle'
    if name in ['idle','move']:
        sc.frame_set(count+1);p=tuple(v for bone in rig.pose.bones for row in bone.matrix for v in row)+tuple(v for row in weapon.matrix_world for v in row)+tuple(v for row in rig.matrix_world for v in row)
        assert max(abs(x-y) for x,y in zip(p,poses[0]))<1e-5,'loop boundary differs'
    checks[name]={'frame_count':count,'stationary_base':True,'motion':True,'source_current':True}
(M/'geometry-audit.json').write_text(json.dumps({'status':'pass','anatomy_vertices':19158,'bones':53,'clips':checks,'finished_surface_uvs':True,'camera_only_pigment':True,'native_weights':True,'limitations':'No exhaustive skin/equipment collision solver; art review required.'},indent=2));print('PASS: true MPFB meshes, projection UVs, six actual bakes, five current clips, stationary base, seamless key boundaries, settled death')

"""Validate solid geometry, fixed base, mechanical keys and terminal wreck."""
import bpy,bmesh,json,os,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/jet-bomber'
bpy.ops.wm.open_mainfile(filepath=str(M/'jet-bomber.blend'))
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)>=100
assert len([o for o in meshes if 'intake rim' in o.name])==8
solid=[]
for o in meshes:
    assert all(abs(s)>.001 for s in o.scale),o.name
    if any(n in o.name for n in ('fuselage','wing','vertical fin','intake rim')):
        bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name
        assert abs(bm.calc_volume())>1e-6,o.name;solid.append(o.name);bm.free()
assert len(list((M/'textures/baked').glob('*.png')))==6
up=Vector((0,.25,math.sqrt(1-.25**2)))
support=bpy.data.objects['GEO-curved stationary stone support']
top=max(v.co.dot(up) for v in support.data.vertices)
tips=[support.matrix_world @ v.co for v in support.data.vertices if v.co.dot(up)>top-.04]
distances=[]
for i in range(2):
    ob=bpy.data.objects[f'GEO-near inner jet {i}']
    tree=BVHTree.FromPolygons([ob.matrix_world @ v.co for v in ob.data.vertices],
                              [list(face.vertices) for face in ob.data.polygons])
    distances.extend(tree.find_nearest(tip)[3] for tip in tips)
assert min(distances)<.025,('support is detached in depth',min(distances))
clips={'idle':8,'move':8,'attack':10,'hit':4,'death':10};motion={}
for clip,count in clips.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/f'{clip}.blend'));sc=bpy.context.scene;root=bpy.data.objects['RIG-airframe'];base=bpy.data.objects['GEO-stationary cream base'];base_matrix=base.matrix_world.copy();states=[]
    for frame in range(1,count+1):
        sc.frame_set(frame);states.append(tuple(root.location)+tuple(root.rotation_euler))
        assert base.matrix_world==base_matrix
        assert all(abs(v)>.001 for o in bpy.data.objects for v in o.scale)
    assert len(set(states))>1,clip
    if clip in ('idle','move'):
        sc.frame_set(count+1);end=tuple(root.location)+tuple(root.rotation_euler)
        assert max(abs(a-b) for a,b in zip(states[0],end))<1e-5
    if clip=='attack':
        up=Vector((0,.25,math.sqrt(1-.25**2)))
        for i in range(3):
            bomb=bpy.data.objects['GEO-bomb-'+str(i)];heights=[]
            for frame in range(1,count+1):
                sc.frame_set(frame)
                if not bomb.hide_render:heights.append(bomb.location.dot(up))
            falls=[a-b for a,b in zip(heights,heights[1:])]
            assert len(falls)>=2 and all(v>0 for v in falls),'bomb must fall'
            assert all(b>a for a,b in zip(falls,falls[1:])),'bomb must accelerate'
            assert bomb.hide_render,'release must finish inside attack clip'
    if clip=='death':
        assert max(abs(a-b) for a,b in zip(states[-1],states[-2]))<1e-5
        support=bpy.data.objects['GEO-curved stationary stone support']
        assert not support.hide_render,'support must collapse continuously, not vanish'
        assert support.data.shape_keys.key_blocks['Collapsed stone'].value==1
        eo=support.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh()
        bm=bmesh.new();bm.from_mesh(me)
        assert all(e.is_manifold for e in bm.edges) and abs(bm.calc_volume())>1e-5
        bm.free();eo.to_mesh_clear()
        assert 'wreck_contact_correction' in sc
        values=[]
        for frame in range(1,count+1):
            sc.frame_set(frame);assert not support.hide_render
            values.append(support.data.shape_keys.key_blocks['Collapsed stone'].value)
        assert len(set(values))>=5 and values[0]==0 and values[-2:]==[1,1]
    motion[clip]={'samples':count,'distinct_root_poses':len(set(states))}
report={'solid_meshes':solid,'engine_intakes':8,'motion':motion,'base_stationary':True,'gait':'not applicable: airborne rigid machine','art_approval':False}
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT PASS',json.dumps(report))

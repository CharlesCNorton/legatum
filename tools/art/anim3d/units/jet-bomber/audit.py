"""Validate solid geometry, fixed base, mechanical keys and terminal wreck."""
import bpy,bmesh,json,os,math
from pathlib import Path
from mathutils import Vector
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
    if clip=='death':
        assert max(abs(a-b) for a,b in zip(states[-1],states[-2]))<1e-5
        assert bpy.data.objects['GEO-curved stationary stone support'].hide_render
        assert 'wreck_contact_correction' in sc
    motion[clip]={'samples':count,'distinct_root_poses':len(set(states))}
report={'solid_meshes':solid,'engine_intakes':8,'motion':motion,'base_stationary':True,'gait':'not applicable: airborne rigid machine','art_approval':False}
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT PASS',json.dumps(report))

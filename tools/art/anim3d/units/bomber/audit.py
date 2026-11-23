"""Audit the actual editable masters independently of atlas pixel checks."""
import bpy,os,json,hashlib
from mathutils import Vector
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/bomber';records={}
bakes=json.loads((M/'textures/baked/manifest.json').read_text());assert len(bakes)==3
for record in bakes:
    assert all(Path(record[key]).exists() for key in ('AO','curvature'))
def base_has_clean_contact(base):
    return ('RestPainting' in base.data.uv_layers
            and base.get('projection')=='masked stone rim, clean support footprint, live AO'
            and any(n.type=='TEX_IMAGE' and n.image and n.image.name.startswith('stone-mask')
                    for n in base.data.materials[0].node_tree.nodes))

for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/(clip+'.blend')));sc=bpy.context.scene;assert sc.camera
    assert sc['master_sha256']==hashlib.sha256((M/'bomber.blend').read_bytes()).hexdigest(),'stale animated blend'
    meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)>=29
    assert all(min(abs(v) for v in o.scale)>.001 for o in meshes),'tiny mesh scale'
    for name in ('GEO-fuselage','GEO-near wing','GEO-far wing'):
        o=bpy.data.objects[name];assert len(o.data.vertices)>100
        assert min(o.dimensions)>.04,('non-volumetric principal geometry',name)
        assert 'RestPainting' in o.data.uv_layers
        assert o.get('surface_finished') and not o.modifiers,'unfinished projection surface'
        material=o.data.materials[0]
        assert material.node_tree.nodes.get('Camera pigment')
        assert material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value==0
    assert base_has_clean_contact(bpy.data.objects['GEO-stationary cream base'])
    base=bpy.data.objects['GEO-stationary cream base'];root=bpy.data.objects['RIG-airframe'];bases=[];poses=[]
    for f in range(1,n+1):
        sc.frame_set(f);bases.append(tuple(v for row in base.matrix_world for v in row));poses.append(tuple(v for row in root.matrix_world for v in row))
    assert len(set(bases))==1,'base moving';assert len(set(poses))>1,'airframe static'
    if clip=='death':
        assert poses[-1]==poses[-2],'death does not settle'
        support=bpy.data.objects['GEO-curved stationary stone support']
        assert not support.hide_render,'support disappears instead of collapsing'
        assert support.data.shape_keys.key_blocks['Crushed stone support'].value==1
        for side in ('near','far'):
            prop=bpy.data.objects['RIG-'+side+' propeller']
            angles=[]
            for f in (7,8,9,10):
                sc.frame_set(f);angles.append(prop.rotation_euler.z)
            assert 0<angles[2]-angles[1]<angles[1]-angles[0]<.3,'propeller stop snaps'
            assert angles[-1]==angles[-2],'terminal propeller not held'
        top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box);points=[];deps=bpy.context.evaluated_depsgraph_get()
        for name in ('GEO-fuselage','GEO-near nacelle'):
            o=bpy.data.objects[name].evaluated_get(deps);me=o.to_mesh()
            for v in me.vertices:
                pt=o.matrix_world @ v.co
                if (pt.xy-base.location.xy).length<.94:points.append(pt.z)
            o.to_mesh_clear()
        assert points and abs(min(points)-top)<.001,'wreck does not contact base'
        sc['verified_wreck_contact_gap']=min(points)-top
    if clip in ('idle','move'):
        sc.frame_set(n+1);closing=tuple(v for row in root.matrix_world for v in row)
        assert max(abs(a-b) for a,b in zip(poses[0],closing))<1e-6,'loop discontinuity'
        import math
        for side in ('near','far'):
            prop=bpy.data.objects['RIG-'+side+' propeller']
            mount=bpy.data.objects['RIG-'+side+' shaft'];assert prop.parent==mount
            axes=[]
            for f in range(1,n+2):
                sc.frame_set(f)
                axis=prop.matrix_local.to_3x3()@Vector((0,0,1))
                axes.append(tuple(axis))
            assert all((Vector(axis)-Vector((0,0,1))).length<1e-6 for axis in axes),'propeller wobbles off shaft'
            sc.frame_set(1);start=prop.rotation_euler.z;sc.frame_set(n+1);end=prop.rotation_euler.z
            assert abs(math.sin(3*(end-start)))<1e-5 and math.cos(3*(end-start))>.99999,'propeller loop discontinuity'
    records[clip]={'frames':n,'meshes':len(meshes),'stationary_base':True,'volumetric_airframe':True,'real_motion':True}
(M/'audit.json').write_text(json.dumps(records,indent=2));print('AUDIT PASS',json.dumps(records))

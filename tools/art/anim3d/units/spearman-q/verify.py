"""Check saved clips against unmodified source geometry, rig and library rotations."""
import hashlib
import json
import os
from pathlib import Path
import struct
import bpy

root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
assets=root/'assets/spearman-q';lane=root/'lanes/spearman-q'

def mesh_hash(o):
    h=hashlib.sha256()
    for v in o.data.vertices:
        h.update(struct.pack('<3f',*v.co))
        for g in v.groups:h.update(struct.pack('<If',g.group,g.weight))
    for p in o.data.polygons:
        h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return h.hexdigest()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(next(assets.rglob('Superhero_Male_FullBody.gltf'))))
original=mesh_hash(bpy.data.objects['SuperHero_Male'])
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rest={b.name:[list(row) for row in b.matrix_local] for b in rig.data.bones}
results={}
for clip in ['attack','idle','walk','hit','death']:
    bpy.ops.wm.open_mainfile(filepath=str(lane/'masters'/f'{clip}.blend'))
    s=bpy.context.scene;body=bpy.data.objects['Quaternius Superhero male original rig']
    assert mesh_hash(bpy.data.objects['SuperHero_Male'])==original
    assert all([list(row) for row in body.data.bones[name].matrix_local]==mat for name,mat in rest.items())
    receipt=json.loads((lane/'frames'/clip/'receipt.json').read_text())
    donor=bpy.data.objects[receipt['library']]
    source=bpy.data.actions[receipt['action']]
    donor.animation_data.action=source;donor.animation_data.action_slot=source.slots[0]
    worst=0.0
    for i,f in enumerate(receipt['source_samples_24fps'],1):
        s.frame_set(i);bpy.context.view_layer.update()
        actual={p.name:p.matrix.to_quaternion() for p in body.pose.bones if p.name in rest}
        for o in s.objects:
            if o.name.startswith('GEO-Rigid'):
                assert o.parent_type=='BONE' and o.parent_bone.startswith('prop_')
                assert not o.vertex_groups and not o.modifiers and o.data.shape_keys is None
                m=o.matrix_world.to_3x3();assert all(abs(m.col[k].length-1)<1e-5 for k in range(3))
                assert all(abs(m.col[k].dot(m.col[j]))<1e-5 for k in range(3) for j in range(k))
        s.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
        for name,q in actual.items():
            d=donor.pose.bones[name]
            expected=d.matrix.to_quaternion()  @  d.bone.matrix_local.to_quaternion().inverted()  @  body.data.bones[name].matrix_local.to_quaternion()
            # Quaternion dot is stable close to identity, unlike float32 acos.
            error=1-abs(q.normalized().dot(expected.normalized()))
            worst=max(worst,error)
    assert worst<2e-6,(clip,worst)
    results[clip]={'body_mesh_and_weights_unchanged':True,'original_rest_bones_unchanged':len(rest),
                   'rigid_props_all_frames':True,'max_rotation_quaternion_dot_error':worst}
(lane/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
print('SPEARMAN_Q_VERIFIED',json.dumps(results))

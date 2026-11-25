"""Verify source integrity, rigid sockets, thrust trajectory and delivered poses."""
import hashlib,json,os,struct,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build,motion
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
lane=root/'lanes/spearman-q-r2'


def mesh_hash(o):
    h=hashlib.sha256()
    for v in o.data.vertices:
        h.update(struct.pack('<3f',*v.co))
        for g in v.groups:h.update(struct.pack('<If',g.group,g.weight))
    for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return h.hexdigest()


def points(o):
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    result=[o.matrix_world @ v.co for v in mesh.vertices];evaluated.to_mesh_clear();return result


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(next((root/'assets/spearman-q').rglob('Superhero_Male_FullBody.gltf'))))
original=mesh_hash(bpy.data.objects['SuperHero_Male'])
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rest={b.name:[list(row) for row in b.matrix_local] for b in rig.data.bones}
results={};attachments={}
for clip in ['attack','idle','walk','hit','death']:
    bpy.ops.wm.open_mainfile(filepath=str(lane/'masters'/f'{clip}.blend'))
    s=bpy.context.scene;body=bpy.data.objects['Quaternius Superhero male original rig'];skin=bpy.data.objects['SuperHero_Male']
    assert mesh_hash(skin)==original
    assert all([list(row) for row in body.data.bones[name].matrix_local]==mat for name,mat in rest.items())
    receipt=json.loads((lane/'frames'/clip/'receipt.json').read_text())
    samples=receipt['source_samples_24fps'];actual=[];hands=[];tips=[];soles=[];radii=[];armour_floor=[];feet=[]
    rigid=[o for o in s.objects if o.type=='MESH' and o.parent==body and o.parent_type=='BONE' and o.name.startswith(('KIT ','GEO-Rigid')) and o.get('look_part') not in ('crest','skirt')]
    attachments[clip]={o.name:[list(row) for row in o.matrix_basis] for o in rigid if o.name.startswith('GEO-Rigid')}
    rigidity={}
    for i in range(1,len(samples)+1):
        s.frame_set(i);bpy.context.view_layer.update()
        actual.append(motion.snapshot(body))
        hands.append(body.matrix_world @ body.pose.bones['hand_r'].head)
        head=bpy.data.objects['GEO-Rigid spear leaf'];tips.append(head.matrix_world @ head.data.vertices[0].co)
        ps=points(skin);soles.append(min(p.z for p in ps));radii.append(max(p.xy.length for p in ps))
        armour=[o for o in s.objects if o.name.startswith('KIT ') and o.type=='MESH' and o.get('look_part')!='shield']
        armour_floor.append(min((p.z for o in armour for p in points(o)),default=1))
        feet.append({side:list(body.matrix_world @ body.pose.bones['foot_'+side].head) for side in ('l','r')})
        for ob in rigid:
            assert not ob.vertex_groups and not any(m.type=='ARMATURE' for m in ob.modifiers) and ob.data.shape_keys is None,(ob.name,len(ob.vertex_groups),[(m.type) for m in ob.modifiers],str(ob.data.shape_keys))
            m=ob.matrix_world.to_3x3()
            metric=[m.col[k].dot(m.col[j]) for k in range(3) for j in range(3)]
            if ob.name not in rigidity:rigidity[ob.name]=metric
            assert max(abs(a-b) for a,b in zip(metric,rigidity[ob.name]))<2e-4,ob.name
    # Reconstruct the documented donor plus small layers independently of its bake.
    body.animation_data.action=None
    donors={tag:bpy.data.objects[tag] for tag in ('ual1','ual2')}
    actions={(tag,a.name.removesuffix('.001')):a for tag in donors for a in bpy.data.actions}
    guard,rotation,start=motion.prepare(body,donors,actions,build.pose)
    source=bpy.data.actions[receipt['action']]
    error=0
    for index,f in enumerate(samples):
        build.pose(body,donors[receipt['library']],source,f)
        motion.layer(body,clip,index,guard,rotation,start);motion.seat_body(body)
        if clip=='attack':motion.solve_arm(body,start+motion.AIM*motion.EXTENSION[index],rotation)
        for name,mat in motion.snapshot(body).items():
            error=max(error,max(abs(mat[r][c]-actual[index][name][r][c]) for r in range(4) for c in range(4)))
    assert error<2e-4,(clip,error)
    assert min(soles)>=.1049,(clip,min(soles))
    assert min(armour_floor)>=.1049,(clip,min(armour_floor))
    perpendicular=max(((p-tips[0])-motion.AIM*(p-tips[0]).dot(motion.AIM)).length for p in tips)
    if clip=='attack':assert perpendicular<.002,perpendicular
    held=1
    for previous in reversed(actual[:-1]):
        if max(abs(previous[n][r][c]-actual[-1][n][r][c]) for n in previous for r in range(4) for c in range(4))>1e-5:break
        held+=1
    if clip=='death':assert held==3,held
    results[clip]={'held_tail_frames':held,'source_mesh_weights_unchanged':True,'rest_bones_unchanged':len(rest),'rigid_meshes':len(rigid),
                   'max_reconstructed_pose_error':error,'body_min_z_m':min(soles),'armour_min_z_m':min(armour_floor),
                   'max_body_radius_m':max(radii),'tip_line_error_m':perpendicular if clip=='attack' else None,
                   'foot_positions_world':feet,'final_held_pose_equal':actual[-1]==actual[-2],
                   'tip_travel_m':max((p-tips[0]).length for p in tips)}
for clip in attachments:assert attachments[clip]==attachments['idle'],f'{clip}: mismatched sockets'
(lane/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
print('SPEARMAN_Q_R2_VERIFIED',json.dumps({k:{n:v for n,v in row.items() if n!='foot_positions_world'} for k,row in results.items()}))

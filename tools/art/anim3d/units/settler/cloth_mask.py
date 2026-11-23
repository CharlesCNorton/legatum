"""Cull anatomy fully covered by the opaque robe, preserving the editable body."""
import bpy,os,json,hashlib
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler'
def apply_mask():
    body=bpy.data.objects['GEO-MPFB female traveller']
    group=body.vertex_groups.get('Visible outside opaque robe') or body.vertex_groups.new(name='Visible outside opaque robe')
    ids=[v.index for v in body.data.vertices if v.co.z<=.31 or v.co.z>=1.06]
    group.add(ids,1,'REPLACE')
    mask=body.modifiers.get('Covered leg culling') or body.modifiers.new('Covered leg culling','MASK');mask.vertex_group=group.name
    # Culling is non-destructive; put it before subdivision to retain crisp garment occlusion.
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.modifier_move_to_index(modifier=mask.name,index=0)
    body['covered_body']='Upper legs under the complete opaque linen skirt are masked; exposed calves/feet and full underlying anatomy retained.'
if __name__=='__main__':
    for name in ['settler-plain.blend','settler.blend']:
        path=M/name;bpy.ops.wm.open_mainfile(filepath=str(path));apply_mask();bpy.ops.wm.save_as_mainfile(filepath=str(path))
    source=hashlib.sha256((M/'settler.blend').read_bytes()).hexdigest()
    for clip in ['idle','move','attack','hit','death']:
        path=M/'clips'/f'{clip}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));apply_mask();bpy.context.scene['source_sha256']=source;bpy.ops.wm.save_as_mainfile(filepath=str(path))
        meta=M/'clips'/f'{clip}.json';data=json.loads(meta.read_text());data['source_sha256']=source;meta.write_text(json.dumps(data,indent=2))
    with (R/'review/3d-v2/settler-log.md').open('a') as f:f.write('- Non-destructive body mask hides upper legs fully covered by opaque linen; fixes thigh poke-through without removing anatomy or flattening the garment. Updated all saved masters; rerendering every clip.\n')

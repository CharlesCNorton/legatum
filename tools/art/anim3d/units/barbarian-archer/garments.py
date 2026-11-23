"""Remove anatomical regions accidentally included by height-only garment selection."""
import bpy
import bmesh


def clean_regions():
    rules = {
        'GEO-Trousers': lambda n: n.startswith(('pelvis','thigh_','calf_')),
        'GEO-Leather bow bracer': lambda n: n == 'lowerarm_l',
        'GEO-Boots': lambda n: n.startswith(('calf_','foot_','ball_')),
    }
    counts = {}
    for name, allowed in rules.items():
        obj = bpy.data.objects[name]
        accepted = {v.index for v in obj.data.vertices
                    if sum(g.weight for g in v.groups
                           if allowed(obj.vertex_groups[g.group].name)) > .65}
        bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
        remove = [v for v in bm.verts if v.index not in accepted]
        counts[name] = len(remove)
        bmesh.ops.delete(bm, geom=remove, context='VERTS')
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
    print('Semantic garment cleanup:', counts)

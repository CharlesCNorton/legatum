"""Keep the real reins attached to the animated bit and rider's rein hand."""
import bpy
from mathutils import Vector


def reins(frame=None):
    body=bpy.data.objects['Rider MPFB CC0 anatomy']
    group=body.vertex_groups['hand_l'].index
    ids=[v.index for v in body.data.vertices if any(g.group==group and g.weight>.8 for g in v.groups)]
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    # Subdivision changes indices: use an evaluation with only skin enabled.
    ev.to_mesh_clear()
    mods=[(m,m.show_viewport) for m in body.modifiers if m.type!='ARMATURE']
    for m,state in mods:m.show_viewport=False
    bpy.context.view_layer.update()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    hand=sum((ev.matrix_world @ me.vertices[i].co for i in ids),Vector())/len(ids)
    ev.to_mesh_clear()
    for m,state in mods:m.show_viewport=state
    for suffix in ['', '.001']:
        rein=bpy.data.objects['Slack leather rein'+suffix]
        bridle=bpy.data.objects['Cheek bridle'+suffix]
        bit=bridle.matrix_world @ bridle.data.splines[0].points[-1].co.xyz
        points=rein.data.splines[0].points
        for i,p in enumerate(points):
            t=i/(len(points)-1)
            world=bit.lerp(hand,t)+Vector((0,0,-.10*4*t*(1-t)))
            p.co=(*(rein.matrix_world.inverted() @ world),1)
            if frame is not None:p.keyframe_insert('co',frame=frame)
    bpy.context.view_layer.update()

"""Hide only anatomy covered by the kilt, retaining original MPFB topology/weights."""
from common import *
def covered_indices(body):
 states=[(m,m.show_viewport) for m in body.modifiers]
 for m,_ in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(body.data.vertices)
 visible=[v.index for v in me.vertices if not .775<(ev.matrix_world@v.co).z<1.235];ev.to_mesh_clear()
 for m,state in states:m.show_viewport=state
 return visible
def apply_coverage(body,visible):
 old=body.vertex_groups.get('Visible outside linen')
 if old:body.vertex_groups.remove(old)
 group=body.vertex_groups.new(name='Visible outside linen');group.add(visible,1,'REPLACE')
 mod=body.modifiers.get('Anatomy under opaque kilt') or body.modifiers.new('Anatomy under opaque kilt','MASK');mod.vertex_group=group.name
 body.modifiers.move(list(body.modifiers).index(mod),1)

"""Round-two full-depth finish, before frozen projection and AO baking."""
import sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view

for name, expected in json.loads(Path(__file__).with_name('assets.lock.json').read_text()).items():
    assert hashlib.sha256((A/name).read_bytes()).hexdigest()==expected, f'Changed input: {name}'
bpy.ops.wm.open_mainfile(filepath=str(M/'peltast-unpainted.blend'))
sc = bpy.context.scene
assert not sc.get('driver_round2_refined'), 'Rebuild before applying refinement again'
rig = bpy.data.objects['RIG-Peltast']
body = bpy.data.objects['GEO-MPFB peltast anatomy']
# Inverse-skin a radial anatomical correction; retain depth, topology and weights.
for vertex in body.data.vertices:
    weights = {body.vertex_groups[g.group].name: g.weight for g in vertex.groups
               if body.vertex_groups[g.group].name in rig.pose.bones}
    total = sum(weights.values())
    if not total:
        continue
    deform = Matrix([[sum(w/total * (rig.pose.bones[n].matrix @
                     rig.data.bones[n].matrix_local.inverted())[r][c]
                     for n, w in weights.items()) for c in range(4)] for r in range(4)])
    point = deform @ vertex.co
    delta = Vector((0, 0, 0))
    for side in ('l', 'r'):
        bone = rig.pose.bones['thigh_'+side]
        axis = bone.tail-bone.head
        t = max(0, min(1, (point-bone.head).dot(axis)/axis.length_squared))
        center = bone.head+t*axis
        weight = weights.get('thigh_'+side, 0)/total
        delta += (point-center)*(.13*weight*sin(pi*t))
    vertex.co = deform.inverted() @ (point+delta)

# Raise and move the fox crown's apex toward the rear of the painted hide.
# Preserve its complete domed depth instead of adding a silhouette plane.
cap=bpy.data.objects['GEO-Fox skin cap crown']
for vertex in cap.data.vertices:
    t=(vertex.index//64)/14*pi/2
    vertex.co+=P(-7*sin(t),-3*sin(t),0)-P(0,0,0)

# The extracted anatomical beard shell previously protruded below the jaw.
beard=bpy.data.objects['GEO-Short sculpted beard']
for vertex in beard.data.vertices:
    weights={beard.vertex_groups[g.group].name:g.weight for g in vertex.groups
             if beard.vertex_groups[g.group].name in rig.pose.bones}
    total=sum(weights.values())
    if not total:continue
    deform=Matrix([[sum(w/total*(rig.pose.bones[n].matrix@
                     rig.data.bones[n].matrix_local.inverted())[r][c]
                     for n,w in weights.items()) for c in range(4)] for r in range(4)])
    point=deform@vertex.co
    q=world_to_camera_view(sc,sc.camera,point)
    y=(1-q.y)*256
    if y>55:
        point+=P(0,-min(3,(y-55)*.65),0)-P(0,0,0)
        vertex.co=deform.inverted()@point

# Spear tips in the painting are fine iron leaves, not broad arrowheads.
for obj in sc.objects:
    if obj.type == 'MESH' and 'iron leaf head' in obj.name:
        a, b = obj.data.vertices[0].co.copy(), obj.data.vertices[5].co.copy()
        axis = (b-a).normalized()
        for v in obj.data.vertices:
            center = a+axis*(v.co-a).dot(axis)
            v.co = center+(v.co-center)*.58

# A tapered stone side and soft bevel, not a perfectly vertical extruded puck.
base = bpy.data.objects['GEO-Stationary cream base']
for vertex in base.data.vertices:
    if vertex.co.z > 0:
        vertex.co.x *= .985
        vertex.co.y *= .985
base.location.z -= .008
bpy.context.view_layer.update()
for modifier in list(base.modifiers):
    bpy.context.view_layer.objects.active=base
    bpy.ops.object.modifier_apply(modifier=modifier.name)
uv = base.data.uv_layers.new(name='Clean stone camera UV')
# Normalize the generated disc's bbox to the actual projected disc footprint.
coords = [world_to_camera_view(sc, sc.camera, base.matrix_world @ v.co)
          for v in base.data.vertices]
x0,x1=min(v.x for v in coords),max(v.x for v in coords)
y0,y1=min(v.y for v in coords),max(v.y for v in coords)
info=json.loads((A/'stone-fill.json').read_text())
bx0,by0,bx1,by1=info['bbox'];w,h=info['size']
for loop in base.data.loops:
    q=coords[loop.vertex_index]
    # Slightly inset samples avoid alpha fringe; geometry defines the silhouette.
    u=.008+.984*(q.x-x0)/(x1-x0)
    v=.008+.984*(q.y-y0)/(y1-y0)
    uv.data[loop.index].uv=((bx0+u*(bx1-bx0))/w,1-(by1-v*(by1-by0))/h)
mat=base.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links
pig=n['Stone camera pigment']
tex=n.new('ShaderNodeTexImage');tex.name='Generated clean stone pigment'
tex.image=bpy.data.images.load(str(A/'stone-fill-source.png'));tex.extension='EXTEND'
uvn=n.new('ShaderNodeUVMap');uvn.uv_map=uv.name;l.new(uvn.outputs[0],tex.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.23
contact=n.new('ShaderNodeMixRGB');contact.blend_type='MULTIPLY';contact.inputs[0].default_value=.66
l.new(tex.outputs['Color'],contact.inputs[1]);l.new(ao.outputs['AO'],contact.inputs[2])
l.new(contact.outputs[0],pig.inputs['Emission Color'])
# Keep grain in camera pigment and real rough stone for noncamera light paths.
l.new(tex.outputs['Color'],n['Principled BSDF'].inputs['Base Color'])
for node in n:
    if node.type=='MATH' and node.operation=='MULTIPLY':node.inputs[1].default_value=.96
sc['driver_round2_refined']=True
save('peltast-unpainted.blend')
log('- Driver round2 geometry: full-depth thigh volume, finer iron tips, tapered/beveled stone with generated clean-stone camera UV and live contact AO. Existing thick folds, straps/buckle, generated fills and product lights retained; projection/bakes rebuilt next.')

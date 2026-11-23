"""Solid leather reins with endpoints sampled from the actual moving surfaces."""
import bpy, json, math
from mathutils import Vector

RINGS = 33
SIDES = 8

def surface_point(name, indices):
    ob = bpy.data.objects[name]
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    point = sum((ev.matrix_world @ me.vertices[i].co for i in indices), Vector()) / len(indices)
    ev.to_mesh_clear()
    return point

def endpoints(ob):
    anchors = json.loads(ob['rein_anchors'])
    return [surface_point(name, indices) for name, indices in anchors]

def tube(a, b):
    points = []
    direction = (b-a).normalized()
    side = direction.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(direction).normalized()
    for j in range(RINGS):
        t = j/(RINGS-1)
        center = a.lerp(b, t) - Vector((0, 0, .09*math.sin(math.pi*t)))
        for k in range(SIDES):
            angle = k*2*math.pi/SIDES
            points.append(center + .007*(side*math.cos(angle)+up*math.sin(angle)))
    return points

def build_reins():
    old = [o for o in bpy.data.objects if o.name.startswith('Slack leather rein')]
    leather = old[0].data.materials[0]
    for ob in old:
        bpy.data.objects.remove(ob, do_unlink=True)
    rider = bpy.data.objects['Rider MPFB CC0 anatomy']
    group = rider.vertex_groups['hand_l'].index
    hand = [v.index for v in rider.data.vertices if any(g.group == group and g.weight > .75 for g in v.groups)]
    assert hand
    for i, bridle in enumerate(['Cheek bridle', 'Cheek bridle.001']):
        ob = bpy.data.objects[bridle]
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        z = [(ev.matrix_world @ v.co).z for v in me.vertices]
        bit = [k for k, value in enumerate(z) if value < min(z)+.018]
        ev.to_mesh_clear()
        anchors = [(bridle, bit), (rider.name, hand)]
        a, b = [surface_point(name, ids) for name, ids in anchors]
        vertices = tube(a, b)
        faces = [(j*SIDES+k, j*SIDES+(k+1)%SIDES, (j+1)*SIDES+(k+1)%SIDES, (j+1)*SIDES+k)
                 for j in range(RINGS-1) for k in range(SIDES)]
        faces += [tuple(reversed(range(SIDES))), tuple((RINGS-1)*SIDES+k for k in range(SIDES))]
        mesh = bpy.data.meshes.new('Continuous rein mesh'); mesh.from_pydata(vertices, [], faces); mesh.update()
        rein = bpy.data.objects.new('GEO-attached rein '+str(i), mesh); bpy.context.collection.objects.link(rein)
        mesh.materials.append(leather)
        for p in mesh.polygons: p.use_smooth = True
        rein['rein_anchors'] = json.dumps(anchors)
        rein['finished_before_projection'] = True

def key_reins(frame):
    bpy.context.view_layer.update()
    for ob in bpy.data.objects:
        if 'rein_anchors' not in ob: continue
        if not ob.data.shape_keys:
            ob.shape_key_add(name='Basis')
            ob.data.shape_keys.use_relative = False
        shape = ob.shape_key_add(name='Attached frame '+str(frame))
        shape.interpolation = 'KEY_LINEAR'
        for vertex, co in zip(shape.data, tube(*endpoints(ob))): vertex.co = co
        keys = ob.data.shape_keys
        keys.eval_time = shape.frame
        keys.keyframe_insert('eval_time', frame=frame)

"""Fit full-depth surfaces in the rest camera before freezing paint UVs.

Executed by paint.py on its fresh plain checkpoint. The smooth fitting
fields move real vertices, undoing the rest skin matrix to keep live weights.
No alpha geometry, per-frame projection, or flattened depth is used.
"""
import bpy
import numpy as np
import json
import bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def refine(master):
    scene = bpy.context.scene
    camera = scene.camera
    right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    scale = camera.data.ortho_scale / 256
    # Source pixels measured on the preceding native 256px rest render; targets
    # on the shipped token. Separate anatomical fields avoid dragging the rider
    # with the horse's much larger leg/stance corrections.
    pairs = {
        'rider': [
            ((159, 29), (159, 27)), ((155, 53), (157, 50)),
            ((147, 66), (142, 52)), ((123, 57), (119, 46)),
            ((97, 45), (96, 43)), ((40, 46), (45, 36)),
            ((158, 88), (159, 83)), ((146, 124), (149, 114)),
            ((140, 169), (147, 156)), ((177, 82), (179, 78)),
        ],
        'horse': [
            ((200, 66), (205, 58)), ((200, 87), (209, 78)),
            ((215, 99), (222, 95)), ((188, 130), (195, 128)),
            ((161, 142), (165, 142)), ((121, 105), (122, 108)),
            ((113, 143), (126, 141)), ((104, 169), (116, 174)),
            ((117, 169), (136, 171)),
            ((100, 207), (123, 207)), ((112, 201), (146, 200)),
            ((176, 226), (177, 212)), ((195, 226), (216, 211)),
            ((173, 180), (179, 177)), ((194, 179), (209, 177)),
        ],
    }
    fields = {}
    for kind, landmarks in pairs.items():
        a = np.array([p[0] for p in landmarks], dtype=float)
        delta = np.array([p[1] for p in landmarks], dtype=float) - a
        def kernel(distance):
            return distance * distance * np.log(np.maximum(distance, 1e-8))
        distances = np.linalg.norm(a[:, None] - a[None, :], axis=2)
        polynomial = np.column_stack((np.ones(len(a)), a))
        system = np.block([[kernel(distances) + np.eye(len(a))*12, polynomial],
                           [polynomial.T, np.zeros((3,3))]])
        coefficients = np.linalg.solve(system, np.vstack((delta, np.zeros((3,2)))))
        fields[kind] = (a, coefficients)

    def fitted(world, kind):
        q = world_to_camera_view(scene, camera, world)
        xy = np.array((q.x * 256, (1-q.y) * 256))
        a, coefficients = fields[kind]
        distance = np.linalg.norm(a-xy, axis=1)
        kernel = distance * distance * np.log(np.maximum(distance, 1e-8))
        delta = np.concatenate((kernel, [1, *xy])) @ coefficients
        return world + right * float(delta[0] * scale) - up * float(delta[1] * scale)

    # Finish curves and rigid kit first. UVs must sample the surface that renders.
    for obj in list(scene.objects):
        if obj.type not in {'MESH', 'CURVE'} or obj.name == 'Stationary cream stone':
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type == 'CURVE':
            if obj.name == 'GEO-pistol steel barrel':
                obj['muzzle_local'] = list(obj.data.splines[0].points[-1].co.xyz)
            bpy.ops.object.convert(target='MESH')
            obj = bpy.context.object
        if obj.name == 'Horse':
            for polygon in obj.data.polygons:
                if polygon.material_index == 8: polygon.material_index = 0
            # Replace the thin source tail with the fully weighted hair locks.
            tail_groups = {g.index for g in obj.vertex_groups if g.name.startswith('Tail')}
            tail_vertices = {v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in tail_groups) > .5}
            bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in tail_vertices], context='VERTS')
            bm.to_mesh(obj.data); bm.free()
        if obj.data.shape_keys:
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        armature = next((m for m in obj.modifiers if m.type == 'ARMATURE'), None)
        if not armature:
            for modifier in list(obj.modifiers):
                bpy.ops.object.modifier_apply(modifier=modifier.name)
        else:
            # Bake bind-space subdivision once, retaining interpolated weights.
            for modifier in list(obj.modifiers):
                if modifier.type == 'SUBSURF' and obj.name == 'Horse':
                    bpy.ops.object.modifier_move_up(modifier=modifier.name)
                    modifier.levels = 2
                    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.context.view_layer.update()
    records = []
    for obj in list(scene.objects):
        if obj.type != 'MESH' or obj.name == 'Stationary cream stone' or obj.name.startswith('Skinned tail hair'):
            continue
        parent = obj.parent
        is_rider = obj.name.startswith('Rider')
        while parent:
            is_rider |= parent.name == 'Rider MPFB game_engine'
            parent = parent.parent
        kind = 'rider' if is_rider else 'horse'
        armature = next((m for m in obj.modifiers if m.type == 'ARMATURE'), None)
        world = obj.matrix_world.copy()
        inv = world.inverted()
        transforms = {}
        if armature:
            rig = armature.object
            to_rig = rig.matrix_world.inverted() @ world
            from_rig = to_rig.inverted()
            transforms = {
                group.index: rig.pose.bones[group.name].matrix @ rig.data.bones[group.name].matrix_local.inverted()
                for group in obj.vertex_groups if group.name in rig.pose.bones
            }
        foot_fits=[]
        for vertex in obj.data.vertices:
            deform = Matrix.Identity(4)
            weights = [(transforms[g.group], g.weight) for g in vertex.groups if g.group in transforms]
            if weights:
                total = sum(w for _, w in weights)
                blend = Matrix([[sum(m[r][c] * w / total for m, w in weights) for c in range(4)] for r in range(4)])
                deform = from_rig @ blend @ to_rig
            posed = world @ deform @ vertex.co
            fitted_world = fitted(posed, kind)
            undo = deform.inverted() @ inv
            vertex.co = undo @ fitted_world
            if obj.name == 'Horse' and posed.z < .65:
                foot_fits.append((vertex, posed, fitted_world, undo, (posed.x>0, posed.y>.2)))
        if foot_fits:
            view = camera.matrix_world.to_quaternion() @ Vector((0,0,1))
            for side in {entry[-1] for entry in foot_fits}:
                members=[entry for entry in foot_fits if entry[-1]==side]
                floor=min(entry[2].z for entry in members)
                old_floor=min(entry[1].z for entry in members)
                for vertex,posed,target,undo,_ in members:
                    weight=max(0,min(1,(.65-posed.z)/(.65-old_floor)))
                    vertex.co=undo @ (target+view*((.112-floor)*weight/view.z))
        obj.data.update()
        if 'muzzle_local' in obj:
            obj['muzzle_local'] = list(inv @ fitted(world @ Vector(obj['muzzle_local']), kind))
        records.append({'object': obj.name, 'vertices': len(obj.data.vertices), 'field': kind})

    # Refit real bridle ribbons to the horse surface, then run the slack reins
    # from the bit to the actual fitted rein hand. Their old endpoints missed
    # the raised head and projected well past the horse's muzzle.
    import ast
    from pathlib import Path
    helpers = {}
    for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name == 'curve':
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<curve>', 'exec'), globals(), helpers)
    curve = helpers['curve']
    view = camera.matrix_world.to_quaternion() @ Vector((0,0,1))
    def pixel_ray(xy, depth_point):
        q = world_to_camera_view(scene,camera,depth_point)
        return depth_point + right*((xy[0]/256-q.x)*camera.data.ortho_scale) + up*((1-xy[1]/256-q.y)*camera.data.ortho_scale)
    horse = bpy.data.objects['Horse']
    hrig = bpy.data.objects['AnimalArmature']
    head = hrig.matrix_world @ hrig.pose.bones['Head'].head
    def surface(xy):
        origin = pixel_ray(xy,head) + view*5
        hit, point, _, _, _, _ = scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,-view)
        return point + view*.012 if hit else pixel_ray(xy,head)
    leather = bpy.data.materials['MAT-scuffed umber leather']
    for obj in list(scene.objects):
        if obj.name.startswith(('Cheek bridle','Nose band','Slack leather rein','Bronze bridle rosette')):
            bpy.data.objects.remove(obj,do_unlink=True)
    paths = [
        ('GEO-fitted cheek strap',[(202,64),(209,79),(220,94)],'Head'),
        ('GEO-fitted brow strap',[(201,64),(211,67),(218,75)],'Head'),
        ('GEO-fitted noseband',[(216,89),(222,91),(226,95)],'Head'),
        ('GEO-fitted rein',[(220,94),(207,108),(189,104),(177,81)],'Torso'),
    ]
    for name,path,bone in paths:
        points=[surface(xy) for xy in path]
        if bone=='Torso':
            # Slack is suspended in front of the coat, not stamped to its skin.
            a,b=points[0],points[-1]
            points=[pixel_ray(xy,a.lerp(b,i/(len(path)-1)))+view*.025 for i,xy in enumerate(path)]
        obj=curve(name,points,.011 if bone=='Head' else .008,leather)
        bpy.context.view_layer.update();world=obj.matrix_world.copy()
        obj.parent=hrig;obj.parent_type='BONE';obj.parent_bone=bone
        bpy.context.view_layer.update();obj.matrix_world=world
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')

    # Keep a circular horizontal stone. Its footprint shifts toward the painted
    # hooves; a taller low step supplies the source's cream rim.
    base = bpy.data.objects['Stationary cream stone']
    base.location += right * (5 * scale)
    away = Vector((-view.x,-view.y,0)).normalized()
    base.location += away * (6*scale/up.dot(away))
    for vertex in base.data.vertices:
        if vertex.co.z < 0:
            vertex.co.z -= .035
    base.modifiers[0].width = .022
    base.modifiers[0].segments = 5
    mat=base.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links
    physical=nodes.get('Principled BSDF');output=nodes.get('Material Output')
    pigment=nodes.new('ShaderNodeEmission');pigment.inputs['Color'].default_value=(.815,.624,.352,1)
    lightpath=nodes.new('ShaderNodeLightPath');factor=nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.55
    links.new(lightpath.outputs['Is Camera Ray'],factor.inputs[0])
    mix=nodes.new('ShaderNodeMixShader');links.new(factor.outputs[0],mix.inputs[0]);links.new(physical.outputs[0],mix.inputs[1]);links.new(pigment.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    for name, energy, color in [
        ('Warm key', 360, (1, .95, .85)),
        ('Cool fill', 72, (.88, .93, 1)),
        ('Cool rim', 108, (.82, .90, 1)),
    ]:
        light = bpy.data.objects[name]
        light.data.energy = energy
        light.data.color = color
    bpy.context.view_layer.update()
    (master/'registration.json').write_text(json.dumps({
        'method': 'rest-camera smooth full-depth vertex fit; inverse skin matrices',
        'camera': list(camera.location), 'landmarks': pairs, 'objects': records,
        'limitation': 'approximate single-view anatomical fit, not exact camera recovery',
    }, indent=2))

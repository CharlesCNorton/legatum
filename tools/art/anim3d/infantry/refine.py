"""Round-four surface registration; called before frozen projection UVs are made.

Edits volumetric mesh coordinates, preserving volume, skin topology and weights.
All coordinates below are landmarks on the padded 256px reference painting.
"""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view


def refine(sc, aim, screen_sculpt):
    # Turn the real feet outward, rather than sampling pale stone onto inward toes.
    aim('foot_l', (.075, -.12, -.035))
    aim('foot_r', (-.075, -.12, -.035))
    aim('ball_l', (.3, -1, 0))
    aim('ball_r', (-.3, -1, 0))
    bpy.context.view_layer.update()

    def pixel(ob, co):
        p = world_to_camera_view(sc, sc.camera, ob.matrix_world @ co)
        return Vector((p.x*256, (1-p.y)*256))

    # Preserve the convex shell and its rim. Register the raised decoration to
    # the painted boss: its previous center sat seven pixels left of the paint.
    boss = bpy.data.objects['Aspis central omphalos']
    center = sum((pixel(boss, v.co) for v in boss.data.vertices), Vector((0, 0)))/len(boss.data.vertices)
    target = Vector((163.0, 139.0))
    shell = bpy.data.objects['Convex bronze aspis']
    shell_tree = BVHTree.FromPolygons(
        [shell.matrix_world @ v.co for v in shell.data.vertices],
        [list(p.vertices) for p in shell.data.polygons])
    view = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    boss_world = sum((boss.matrix_world @ v.co for v in boss.data.vertices), Vector())/len(boss.data.vertices)
    for ob in sc.objects:
        if ob.type != 'MESH':
            continue
        ring = ob.name == 'Aspis turned rim.002'
        if ob.name.startswith(('Aspis central omphalos', 'Sunburst raised ray')) or ring:
            for v in ob.data.vertices:
                original = ob.matrix_world @ v.co
                delta = pixel(ob, v.co)-center
                local = screen_sculpt(ob, v.co, target+Vector((delta.x*.78, delta.y*.87)))
                world = ob.matrix_world @ local
                hit = shell_tree.ray_cast(world+view*5, -view, 10)[0]
                assert hit is not None, f'Relief outside shell: {ob.name}'
                # Screen registration changes the underlying shell depth. Seat
                # each piece on that actual curved surface, keeping a real keel,
                # rounded boss and rim instead of burying them beneath the shell.
                if ob.name.startswith('Sunburst raised ray'):
                    relief = .025 if v.index == 3 else .009
                elif ring:
                    relief = .014+(original-boss_world).dot(view)*.08
                else:
                    relief = .030+(original-boss_world).dot(view)
                v.co = ob.matrix_world.inverted() @ (hit+view*relief)
            ob.data.update()
        if ob.name.startswith(('Horsehair crest tuft', 'Horsehair painted fibre', 'Crest bronze saddle')):
            for v in ob.data.vertices:
                p = pixel(ob, v.co)
                v.co = screen_sculpt(ob, v.co, Vector((131+(p.x-131)*.84, 91+(p.y-91)*.92)))
            ob.data.update()
    # Remove the obsolete secondary UV paint blend in the physical shader. The
    # current rest-camera layer already supplies the same art, correctly aligned.
    shield = bpy.data.objects['Convex bronze aspis']
    for mat in shield.data.materials:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image and node.image.name.startswith('spearman-source'):
                for link in list(node.outputs['Color'].links):
                    if link.to_node.type == 'MIX_RGB':
                        link.to_node.inputs[0].default_value = 0
    # Fine limestone pigment grain; no painted feet or static contact shadows.
    for mat in bpy.data.objects['Stationary cream stone'].data.materials:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        grain = nodes.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 210
        ramp = nodes.new('ShaderNodeValToRGB')
        base = tuple(bsdf.inputs['Base Color'].default_value)
        for el, factor in zip(ramp.color_ramp.elements, (.94, 1.04)):
            el.color = tuple(min(1, c*factor) for c in base[:3])+(1,)
        links.new(grain.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Specular IOR Level'].default_value = .18
    sc['infantry_refinement'] = 4
    bpy.context.view_layer.update()

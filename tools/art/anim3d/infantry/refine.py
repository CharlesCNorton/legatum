"""Infantry surface registration; called before frozen projection UVs are made.

Edits volumetric mesh coordinates, preserving depth, skin topology and weights.
All coordinates below are landmarks on the padded 256px reference painting.
"""
import math
import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view


def refine(sc, aim, screen_sculpt):
    # MPFB retains its macro shape keys. Editing data.vertices while those keys
    # are active does not edit the rendered mixed shape (the prior body fitting
    # was therefore ignored). Bake the current human morph on this disposable
    # projection copy before fitting; keep topology, weights and the rig, with
    # the editable MPFB source preserved in projection-input.blend.
    body = bpy.data.objects['MPFB anatomical male • original topology']
    if body.data.shape_keys:
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    assert len(body.data.vertices) == 19158 and body.data.shape_keys is None
    # Turn the real feet outward, rather than sampling pale stone onto inward toes.
    aim('foot_l', (.075, -.12, -.035))
    aim('foot_r', (-.075, -.12, -.035))
    aim('ball_l', (.3, -1, 0))
    aim('ball_r', (-.3, -1, 0))
    bpy.context.view_layer.update()

    def pixel(ob, co):
        p = world_to_camera_view(sc, sc.camera, ob.matrix_world @ co)
        return Vector((p.x*256, (1-p.y)*256))

    # Register the complete convex shield, including the back and thick rim.
    # The previous outline overhung the painted right and lower edges; shrinking
    # only its ornament cannot repair that silhouette. Camera depth is unchanged.
    for ob in bpy.data.objects['Aspis control'].children:
        if ob.type != 'MESH':
            continue
        for v in ob.data.vertices:
            p = pixel(ob, v.co)
            target = Vector((157+(p.x-157)*.94, 139+(p.y-140)*.94))
            v.co = screen_sculpt(ob, v.co, target)
        ob.data.update()

    # Keep MPFB anatomy and original weights. Apply a small smooth fitting field
    # in the evaluated guard, then invert each vertex's linear skin transform.
    # This seats the pale shoulder cap inside the painting instead of allowing
    # a cream/skin crescent to protrude above its sleeve.
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted()
                  for b in rig.pose.bones}

    def fitted_pixel(p):
        shoulder = math.exp(-((p.x-111)/8)**2-((p.y-108)/10)**2)
        target = p+Vector((5.0, 5.0))*shoulder
        if p.x < 122:
            # Seat the spear-side shin/foot under the painted greave rather
            # than leaving an exposed sliver beyond the painted toe silhouette.
            target.x += 4.5*max(0, min(1, (p.y-179)/30))
            # Match the wider side-on toe box, including all real straps and
            # the MPFB foot. Fitting only the shin left a round, narrow sandal.
            toe = max(0, min(1, (p.y-207)/8))
            target.x += ((target.x-102)*.45-1)*toe
        elif p.x > 137:
            # The other sandal was viewed almost end-on. Broaden its real toe
            # and sole together, keeping the ankle and contact height fixed.
            weight = max(0, min(1, (p.y-207)/9))
            target.x += (p.x-156)*.65*weight
        return target

    def fitted_local(ob, co, p):
        local = screen_sculpt(ob, co, fitted_pixel(p))
        # Lift the fitted feet onto the actual stone top along the view ray.
        # This preserves painted landmarks while correcting the old buried
        # soles. Blend through the ankle; original skin weights remain intact.
        weight = max(0, min(1, (p.y-199)/9))
        view_ray = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        world = ob.matrix_world @ local
        world += view_ray*(.034*weight/view_ray.z)
        # Anatomy must sit INSIDE the sandal, not protrude below its sole.
        # Flatten only the underside of the fitted foot; subdivision smooths
        # the transition and the original topology/weights remain unchanged.
        if ob.name == 'MPFB anatomical male • original topology' and p.y > 199:
            world.z = max(world.z, .123)
        return ob.matrix_world.inverted() @ world

    for name in ['MPFB anatomical male • original topology', 'Linen tunic shoulder sleeves']:
        ob = bpy.data.objects[name]
        for v in ob.data.vertices:
            influences = [(transforms[ob.vertex_groups[g.group].name], g.weight)
                          for g in v.groups if ob.vertex_groups[g.group].name in transforms]
            total = sum(w for _, w in influences)
            if total < .001:
                continue
            skin = sum((m*(w/total) for m, w in influences), Matrix(((0,)*4,)*4))
            posed = skin @ v.co
            p = pixel(ob, posed)
            v.co = skin.inverted_safe() @ fitted_local(ob, posed, p)
        ob.data.update()
    for ob in sc.objects:
        if ob.type != 'MESH' or not ob.name.startswith(('Contoured greave', 'Greave chased', 'Leather sandal', 'Sandal')):
            continue
        # Greaves retain an armature modifier; rigid sandals use bone parenting.
        skinned = any(m.type == 'ARMATURE' for m in ob.modifiers)
        for v in ob.data.vertices:
            skin = Matrix.Identity(4)
            if skinned:
                influences = [(transforms[ob.vertex_groups[g.group].name], g.weight)
                              for g in v.groups if ob.vertex_groups[g.group].name in transforms]
                total = sum(w for _, w in influences)
                if total > .001:
                    skin = sum((m*(w/total) for m, w in influences), Matrix(((0,)*4,)*4))
            posed = skin @ v.co
            v.co = skin.inverted_safe() @ fitted_local(ob, posed, pixel(ob, posed))
        ob.data.update()

    # Preserve the convex shell and its rim. Register the raised decoration to
    # the painted boss: its previous center sat seven pixels left of the paint.
    boss = bpy.data.objects['Aspis central omphalos']
    center = sum((pixel(boss, v.co) for v in boss.data.vertices), Vector((0, 0)))/len(boss.data.vertices)
    target = Vector((163.0, 139.0))
    shell = bpy.data.objects['Convex bronze aspis']
    bpy.context.view_layer.update()
    evaluated_shell = shell.evaluated_get(bpy.context.evaluated_depsgraph_get())
    shell_mesh = evaluated_shell.to_mesh()
    # Intersect the rendered shell, including Solidify. The raw mesh lies
    # inside that surface at oblique angles and buried several raised rays.
    shell_tree = BVHTree.FromPolygons(
        [shell.matrix_world @ v.co for v in shell_mesh.vertices],
        [list(p.vertices) for p in shell_mesh.polygons])
    evaluated_shell.to_mesh_clear()
    view = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    boss_world = sum((boss.matrix_world @ v.co for v in boss.data.vertices), Vector())/len(boss.data.vertices)
    for ob in sc.objects:
        if ob.type != 'MESH':
            continue
        ring = ob.name == 'Aspis turned rim.002'
        if ob.name.startswith(('Aspis central omphalos', 'Sunburst raised ray')) or ring:
            if ob.name.startswith('Sunburst raised ray'):
                # A long flat triangle is a chord through the convex shell:
                # clear endpoints do not imply that its interior clears it.
                # Subdivide and seat the ENTIRE raised surface, interpolating
                # the original keel heights through a real mesh attribute.
                bm = bmesh.new(); bm.from_mesh(ob.data)
                bm.verts.ensure_lookup_table()
                height = bm.verts.layers.float.new('Infantry relief height')
                for v in bm.verts:
                    v[height] = .040 if v.index == 3 else .024
                bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=7, use_grid_fill=True)
                bm.to_mesh(ob.data); bm.free()
                heights = ob.data.attributes['Infantry relief height']
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
                    relief = heights.data[v.index].value
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
    # Seat the disc's actual top at the .105m floor used by the planted spear
    # and footwear. Previously the top was .09m and its bottom hung too low.
    base_object = bpy.data.objects['Stationary cream stone']
    base_object.location.z += .015
    # Fine limestone pigment grain; no painted feet or static contact shadows.
    for mat in base_object.data.materials:
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
        # Camera-only pigment opens the warm stone without making it a lamp.
        # The physical BSDF still receives moving feet's contact shadows.
        links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
        ray = nodes.new('ShaderNodeLightPath')
        pigment = nodes.new('ShaderNodeMath'); pigment.operation = 'MULTIPLY'
        pigment.inputs[1].default_value = .95 if 'rim' in mat.name else .42
        links.new(ray.outputs['Is Camera Ray'], pigment.inputs[0])
        links.new(pigment.outputs[0], bsdf.inputs['Emission Strength'])
    # Painted illumination is already display-referred. AgX compressed it a
    # second time, losing the source's bright bronze edges and dark engraving.
    # Standard preserves those pigment relationships; the fixed rest histogram
    # still calibrates the combined physical/projection result for every clip.
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.world.color = (.19, .19, .19)
    bpy.data.objects['Warm upper-left key'].data.color = (1, .97, .93)
    bpy.data.objects['Soft cool fill'].data.color = (.95, .97, 1)
    # Standard does not roll off overexposure. Keep the product-light ratio but
    # reduce incident energy so the cream pigment is not clipped to white.
    for name in ['Warm upper-left key', 'Soft cool fill', 'Warm back rim']:
        bpy.data.objects[name].data.energy *= .55
    # Freeze the finished rigid kit surfaces BEFORE projecting. UVs made on
    # the raw shell were then offset by Solidify and Bevel, visibly displacing
    # the painted sunburst from its own raised rays. Keep all actual thickness
    # and bevel geometry; bone parenting and the death release stay live.
    # Deforming anatomy and cloth keep their original topology and weights.
    for ob in sc.objects:
        if (ob.type != 'MESH' or ob.name == 'Stationary cream stone'
                or any(m.type in {'ARMATURE', 'CLOTH', 'MASK'} for m in ob.modifiers)):
            continue
        bpy.context.view_layer.objects.active = ob
        for mod in list(ob.modifiers):
            if mod.type in {'SOLIDIFY', 'BEVEL', 'SUBSURF'}:
                bpy.ops.object.modifier_apply(modifier=mod.name)
    sc['infantry_refinement'] = 6
    bpy.context.view_layer.update()

"""Infantry surface registration; called before frozen projection UVs are made.

Edits volumetric mesh coordinates, preserving depth, skin topology and weights.
All coordinates below are landmarks on the padded 256px reference painting.
"""
import math
import bmesh
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.studio import match_lighting
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
    # Match the anatomical rest rotations once, including MPFB bone roll.
    # The locomotion retarget uses this bind; no per-frame toe aiming is allowed.
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    for side in ['l', 'r']:
        for name in ['foot_'+side, 'ball_'+side]:
            bone = rig.pose.bones[name]
            matrix = bone.bone.matrix_local.copy()
            matrix.translation = bone.head
            bone.matrix = matrix
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
        target = p+Vector((.2, 1.1))*shoulder
        # Fit the whole bent arm, not just the shoulder cap. The previous
        # elbow sat too far toward the torso, leaving a gap where the painting
        # has a muscular upper arm. Preserve camera depth and skin weights.
        elbow = math.exp(-((p.x-108)/9)**2-((p.y-123)/7)**2)
        target += Vector((-3.8, -1.3))*elbow
        # The actual closed hand was a horizontal sliver. Broaden its vertical
        # knuckle stack around the shaft without replacing fingers or the rig.
        fist = math.exp(-((p.x-97)/8)**4-((p.y-115)/9)**4)
        target += Vector((.08*(p.x-97), .82*(p.y-115)+.3))*fist
        return target

    def fitted_local(ob, co, p):
        local = screen_sculpt(ob, co, fitted_pixel(p))
        # Preserve anatomical feet and original sandal geometry. Screen-space
        # broadening and camera-ray lifting made a correct bone direction look
        # splayed and displaced the contact point during rotation.
        world = ob.matrix_world @ local
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

    for side in ['l', 'r']:
        sole = bpy.data.objects['Leather sandal sole '+side]
        evaluated=sole.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        lowest = min((sole.matrix_world @ v.co).z for v in mesh.vertices)
        evaluated.to_mesh_clear()
        foot = rig.pose.bones['foot_'+side]
        matrix = foot.matrix.copy()
        matrix.translation += rig.matrix_world.to_3x3().inverted() @ Vector((0, 0, .108-lowest))
        foot.matrix = matrix
        bpy.context.view_layer.update()

    # Lower the squared rear neckline behind the helmet. Work on the actual
    # folded collar and weighted cape, leaving pin weights and thickness intact.
    for ob in sc.objects:
        if ob.type != 'MESH' or not ob.name.startswith(('Crimson collar fold', 'Cloak •')):
            continue
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
            p = pixel(ob, posed)
            right = max(0, min(1, (p.x-138)/7))
            left = max(0, min(1, (127-p.x)/7))
            down = max(0, 105-p.y)*.8*right + max(0, 100-p.y)*.8*left
            v.co = skin.inverted_safe() @ screen_sculpt(ob, posed, p+Vector((0, down)))
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
                crest_target = Vector((131+(p.x-131)*.84, 91+(p.y-91)*.92))
                # The painted fan ends above the cheek, and its forward tip
                # extends slightly farther. Fit real tuft volume, not alpha.
                crest_target.y -= 3*max(0, min(1, (crest_target.y-79)/12))
                crest_target.x += 1.2*max(0, min(1, (crest_target.x-135)/9))
                v.co = screen_sculpt(ob, v.co, crest_target)
            ob.data.update()
        if ob.name == 'Corinthian continuous faceplate':
            # Recover the broad near cheek and eye surround of the painting;
            # keep the nose at its registered position and retain real depth.
            for v in ob.data.vertices:
                p = pixel(ob, v.co)
                weight = max(0, min(1, (141-p.x)/12))
                v.co = screen_sculpt(ob, v.co, p+Vector((-2.8*weight, 0)))
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
    # The painting has a shallower top ellipse and a taller stone edge. The
    # lower camera sets the ellipse; move the ROUND disc back on the ground
    # and deepen its underside while preserving the .105m contact surface.
    back = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    back.z = 0
    base_object.location += back.normalized()*.20
    top = max(v.co.z for v in base_object.data.vertices)
    for v in base_object.data.vertices:
        if v.co.z < top-.001:
            v.co.z -= .065
        v.co.x *= .99
        v.co.y *= .99
    # Round the actual stone edge; the old three-segment bevel and coarse
    # scanned bump left a sawtooth highlight at token size.
    for mod in base_object.modifiers:
        if mod.type == 'BEVEL':
            mod.width = .022
            mod.segments = 5
    # Fine limestone pigment grain; no painted feet or static contact shadows.
    for mat in base_object.data.materials:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        for node in nodes:
            if node.type == 'BUMP':
                node.inputs['Strength'].default_value = .035
                node.inputs['Distance'].default_value = .001
        grain = nodes.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 450
        ramp = nodes.new('ShaderNodeValToRGB')
        base = tuple(bsdf.inputs['Base Color'].default_value)
        # The shared cream inputs are albedo, not final display values. The
        # source stone is paler than this physical material under Standard.
        # Calibrate pigment in linear space while retaining live moving shade.
        lift = (1, 1.05, 1.14) if 'rim' in mat.name else (1.03, 1.07, 1.14)
        for el, factor in zip(ramp.color_ramp.elements, (.94, 1.04)):
            el.color = tuple(min(1, c*factor*k) for c, k in zip(base[:3], lift))+(1,)
        links.new(grain.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Specular IOR Level'].default_value = .18
        # Camera-only pigment opens the warm stone without making it a lamp.
        # The physical BSDF still receives moving feet's contact shadows.
        links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
        ray = nodes.new('ShaderNodeLightPath')
        pigment = nodes.new('ShaderNodeMath'); pigment.operation = 'MULTIPLY'
        pigment.inputs[1].default_value = 1.30 if 'rim' in mat.name else .50
        links.new(ray.outputs['Is Camera Ray'], pigment.inputs[0])
        links.new(pigment.outputs[0], bsdf.inputs['Emission Strength'])
    # Painted illumination is already display-referred. AgX compressed it a
    # second time, losing the source's bright bronze edges and dark engraving.
    # Standard preserves those pigment relationships; the fixed rest histogram
    # still calibrates the combined physical/projection result for every clip.
    match_lighting(sc, 'spearman')
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
    # A leather sandal bends at the ball of the foot. A rigid sole parented to
    # the ankle cannot reproduce the source's toe-off, even with correct rolls.
    # Bind the already-finished real sole/straps to MPFB foot + ball, preserving
    # their exact fitted rest surface and UV topology.
    for ob in sc.objects:
        if ob.type!='MESH' or not ob.name.startswith(('Leather sandal sole','Sandal strap')):continue
        side=ob.parent_bone[-1]
        foot,ball=rig.pose.bones['foot_'+side],rig.pose.bones['ball_'+side]
        transforms={p.name:p.matrix @ p.bone.matrix_local.inverted() for p in [foot,ball]}
        world=ob.matrix_world.copy()
        axis=(ball.tail-ball.head).normalized()
        coordinates=[rig.matrix_world.inverted() @ world @ v.co for v in ob.data.vertices]
        if ob.name.startswith('Leather sandal sole'):
            # Store actual finished-surface landmarks before inverse skinning.
            longitudinal=[(v-ball.head).dot(axis) for v in coordinates]
            lo,hi=min(longitudinal),max(longitudinal)
            ob['toe_vertex']=min((i for i,d in enumerate(longitudinal) if d>hi-.01),key=lambda i:coordinates[i].z)
            ob['heel_vertex']=min((i for i,d in enumerate(longitudinal) if d<lo+.01),key=lambda i:coordinates[i].z)
        ob.vertex_groups.clear()
        groups={name:ob.vertex_groups.new(name=name) for name in transforms}
        for vertex,posed in zip(ob.data.vertices,coordinates):
            t=max(0,min(1,((posed-ball.head).dot(axis)+.025)/.055))
            weight=t*t*(3-2*t)
            skin=transforms[foot.name]*(1-weight)+transforms[ball.name]*weight
            vertex.co=skin.inverted() @ posed
            groups[foot.name].add([vertex.index],1-weight,'REPLACE')
            groups[ball.name].add([vertex.index],weight,'REPLACE')
        ob.parent=rig;ob.parent_type='OBJECT';ob.parent_bone=''
        ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
        modifier=ob.modifiers.new('Anatomical sandal toe flex','ARMATURE');modifier.object=rig
        ob.data.update()
    sc['infantry_refinement'] = 8
    bpy.context.view_layer.update()

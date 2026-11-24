"""Small, synthetic CPU/API checks. Run only in a fresh Blender process.

blender -b --disable-autoexec --factory-startup --python-exit-code 1 \
  --python tools/art/anim3d/scripts/technique_probe.py -- --output /tmp/unit-3d-probe
No external assets, add-on downloads, or production scene edits.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def rgba(rgb):
    return tuple(linear(c / 255) for c in rgb) + (1,)


def material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat, mat.node_tree.nodes, mat.node_tree.links


def emission(mat, color_socket):
    n, links = mat.node_tree.nodes, mat.node_tree.links
    e = n.new('ShaderNodeEmission')
    out = n.new('ShaderNodeOutputMaterial')
    links.new(color_socket, e.inputs['Color'])
    links.new(e.outputs[0], out.inputs['Surface'])


def aim(obj, pos):
    obj.rotation_euler = (Vector(pos) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def camera(name, loc):
    obj = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.data.type = 'ORTHO'
    obj.data.ortho_scale = 2.6
    aim(obj, (0, 0, 0))
    return obj


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument("--mpfb", action="store_true", help="Use already installed MPFB in isolated resources")
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    dest = Path(args.output).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'results.json').unlink(missing_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = 8
    s.cycles.use_denoising = False
    s.cycles.seed = 11
    s.render.resolution_x = s.render.resolution_y = 160
    s.render.resolution_percentage = 100
    s.render.film_transparent = True
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'
    s.render.image_settings.color_depth = '8'
    s.display_settings.display_device = 'sRGB'
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    s.view_settings.exposure = 0
    s.view_settings.gamma = 1
    s.render.dither_intensity = 0
    cam = camera('Study-camera', (0, -4, 0))
    s.camera = cam
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16)
    obj = bpy.context.object
    obj.name = 'Study-sphere'
    for p in obj.data.polygons:
        p.use_smooth = True

    def render(name):
        s.render.filepath = str(dest / (name + '.png'))
        bpy.ops.render.render(write_still=True)

    report = {'blender': bpy.app.version_string,
              'build_hash': bpy.app.build_hash.decode(), 'render_device': 'CPU',
              'eevee_render': 'NOT RUN: Eevee requires a graphics context; CPU task',
              'mpfb_rigify': 'NOT RUN: production MPFB integration not exercised'}

    # Same palette/bump network, two different lighting inputs. Eevee graph is
    # constructed but never misrepresented as a Cycles-compatible shader.
    mat, n, links = material('Study-NPR')
    uv = n.new('ShaderNodeTexCoord')
    mapping = n.new('ShaderNodeVectorMath'); mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (6, 36, 1)
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 2
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .15
    bump.inputs['Distance'].default_value = .003
    links.new(uv.outputs['UV'], mapping.inputs[0])
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    diffuse = n.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
    links.new(bump.outputs['Normal'], diffuse.inputs['Normal'])
    rgb = n.new('ShaderNodeShaderToRGB')
    links.new(diffuse.outputs[0], rgb.inputs[0])
    bw = n.new('ShaderNodeRGBToBW'); links.new(rgb.outputs['Color'], bw.inputs[0])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'EASE'
    stops = [(.12, (67, 37, 24)), (.42, (137, 81, 33)),
             (.70, (202, 151, 65)), (.94, (244, 216, 147))]
    for i, (pos, color) in enumerate(stops):
        el = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(pos)
        el.position, el.color = pos, rgba(color)
    links.new(bw.outputs[0], ramp.inputs['Fac'])
    emission(mat, ramp.outputs['Color'])
    report['eevee_nodes'] = 'PASS: Diffuse -> ShaderToRGB -> RGBToBW -> ramp -> Emission'
    eevee = mat.copy(); eevee.name = 'Study-Eevee-only'; eevee.use_fake_user = True
    # CPU fallback: explicitly directed normals, no simulated scene shadows.
    dot = n.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = Vector((-.5, -.7, .5)).normalized()
    links.new(bump.outputs['Normal'], dot.inputs[0])
    remap = n.new('ShaderNodeMapRange')
    remap.inputs['From Min'].default_value = -1
    remap.inputs['From Max'].default_value = 1
    links.new(dot.outputs['Value'], remap.inputs['Value'])
    links.new(remap.outputs['Result'], ramp.inputs['Fac'])
    # Unsupported nodes are removed from CPU material, even though disconnected.
    n.remove(rgb); n.remove(bw); n.remove(diffuse)
    obj.data.materials.append(mat)
    render('analytic-palette-normal')

    # A display round trip: constant painted colour at strength 1.
    swatch, n, links = material('Study-paint-swatch')
    col = n.new('ShaderNodeRGB'); col.outputs[0].default_value = rgba((233, 207, 160))
    emission(swatch, col.outputs[0]); obj.data.materials[0] = swatch
    for transform in ('Standard', 'AgX', 'Filmic'):
        try:
            s.view_settings.view_transform = transform
            s.view_settings.look = 'None'
        except (TypeError, ValueError):
            report['view_' + transform] = 'unavailable'; continue
        render('swatch-' + transform)
        report['view_' + transform] = 'rendered'
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'

    # Two explicit projector UV layers, not the multi-projector face selector.
    cams = [cam, camera('Study-side', (4, 0, 0))]
    target_uv = obj.data.uv_layers[0]; target_uv.name = 'PaintUV'
    for i, proj_cam in enumerate(cams):
        layer = obj.data.uv_layers.new(name='Project' + str(i))
        mod = obj.modifiers.new('Freeze-projector', 'UV_PROJECT')
        mod.uv_layer = layer.name; mod.projector_count = 1
        mod.projectors[0].object = proj_cam
        activate(obj); bpy.context.view_layer.update()
        bpy.ops.object.modifier_apply(modifier=mod.name)
    before = [tuple(x.uv) for x in obj.data.uv_layers['Project0'].data]
    cam.location.x += .2; bpy.context.view_layer.update()
    after = [tuple(x.uv) for x in obj.data.uv_layers['Project0'].data]
    assert before == after
    cam.location.x -= .2; bpy.context.view_layer.update()
    report['frozen_projection_uv'] = 'PASS: unchanged after camera move'
    proj, n, links = material('Study-two-projection-bake')
    textures = []
    for i, colors in enumerate((((.5, .1, .02, 1), (.8, .5, .1, 1)),
                                ((.12, .03, .02, 1), (.4, .1, .03, 1)))):
        coords = n.new('ShaderNodeUVMap'); coords.uv_map = 'Project' + str(i)
        tex = n.new('ShaderNodeTexChecker'); tex.inputs['Scale'].default_value = 5
        tex.inputs['Color1'].default_value, tex.inputs['Color2'].default_value = colors
        links.new(coords.outputs[0], tex.inputs[0]); textures.append(tex)
    # Synthetic convex sphere: front-to-side facing mask, no visibility solver.
    mask = obj.data.attributes.new('SideWeight', 'FLOAT', 'CORNER')
    for loop in obj.data.loops:
        p = obj.data.vertices[loop.vertex_index].co.normalized()
        a, b = max(0, -p.y)**4, max(0, p.x)**4
        mask.data[loop.index].value = b / (a + b) if a + b > 1e-6 else .5
    attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'SideWeight'
    mix = n.new('ShaderNodeMixRGB')
    links.new(attr.outputs['Fac'], mix.inputs[0])
    links.new(textures[0].outputs['Color'], mix.inputs[1])
    links.new(textures[1].outputs['Color'], mix.inputs[2])
    emission(proj, mix.outputs[0]); obj.data.materials[0] = proj
    target_uv.active_render = True
    obj.data.uv_layers.active_index = 0
    baked = bpy.data.images.new('Study-baked', width=256, height=256, alpha=True)
    baked.colorspace_settings.name = 'sRGB'
    target = n.new('ShaderNodeTexImage'); target.image = baked; n.active = target
    activate(obj)
    s.render.bake.use_selected_to_active = False
    s.render.bake.use_clear = True
    s.render.bake.margin = 8
    s.render.bake.margin_type = 'EXTEND'
    bpy.ops.object.bake(type='EMIT')
    assert max(baked.pixels[:]) > .1
    baked.filepath_raw = str(dest / 'projection-baked.png'); baked.file_format = 'PNG'; baked.save()
    render('projection-before-bake')
    baked_mat, n, links = material('Study-baked-paint')
    tex = n.new('ShaderNodeTexImage'); tex.image = baked
    coords = n.new('ShaderNodeUVMap'); coords.uv_map = 'PaintUV'
    links.new(coords.outputs[0], tex.inputs['Vector']); emission(baked_mat, tex.outputs['Color'])
    obj.data.materials[0] = baked_mat
    render('projection-after-bake')
    obj.rotation_euler.z = math.radians(30)
    render('projection-rotated')
    obj.rotation_euler.z = 0
    report['emit_bake'] = 'PASS: two projection layers -> PaintUV, 256px, margin 8'

    # Native constraint / visual bake preserves roll even with different rests.
    def arm(name, roll):
        data = bpy.data.armatures.new(name)
        rig = bpy.data.objects.new(name, data); bpy.context.collection.objects.link(rig)
        activate(rig); bpy.ops.object.mode_set(mode='EDIT')
        b = data.edit_bones.new('bone'); b.head = (0, 0, 0); b.tail = (0, 0, 1); b.roll = roll
        bpy.ops.object.mode_set(mode='OBJECT')
        return rig
    src, dst = arm('Study-source', 0), arm('Study-target', .7)
    sp, tp = src.pose.bones['bone'], dst.pose.bones['bone']
    rest_offset = sp.matrix.inverted() @ tp.matrix
    helper = bpy.data.objects.new('Study-roll-offset', None)
    bpy.context.collection.objects.link(helper)
    con = tp.constraints.new('COPY_ROTATION'); con.target = helper
    con.owner_space = con.target_space = 'WORLD'
    errors = []
    for angle in (0, .5, 1):
        sp.rotation_mode = 'XYZ'; sp.rotation_euler = (.3 * angle, angle, .2 * angle)
        bpy.context.view_layer.update()
        desired = src.matrix_world @ sp.matrix @ rest_offset
        helper.matrix_world = desired; bpy.context.view_layer.update()
        visual = tp.matrix.copy()
        basis = tp.bone.convert_local_to_pose(visual, tp.bone.matrix_local, invert=True)
        con.mute = True; tp.matrix_basis = basis; bpy.context.view_layer.update()
        errors.append(tp.matrix.to_quaternion().rotation_difference(desired.to_quaternion()).angle)
        con.mute = False
    assert max(errors) < 1e-5, errors
    report['retarget_rotation_max_error_rad'] = max(errors)
    con.mute = True
    # Minimal corrective driver evaluation. This does not prove anatomical quality.
    activate(obj); obj.shape_key_add(name='Basis')
    key = obj.shape_key_add(name='bend_corrective')
    key.data[0].co.x += .02
    fc = key.driver_add('value'); d = fc.driver; d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = 'bend'; v.type = 'TRANSFORMS'
    v.targets[0].id = dst; v.targets[0].bone_target = 'bone'
    v.targets[0].transform_type = 'ROT_X'; v.targets[0].transform_space = 'LOCAL_SPACE'
    d.expression = 'min(1,max(0,bend/1.57079632679))'
    tp.rotation_mode = 'XYZ'; tp.rotation_euler = (math.pi/4, 0, 0)
    bpy.context.view_layer.update()
    report['corrective_driver_value_at_45deg'] = key.value
    assert abs(key.value - .5) < 1e-5
    # A two-bone leg with a separate rotation lock preserves synthetic contacts.
    leg = arm('Study-leg', 0)
    activate(leg); bpy.ops.object.mode_set(mode='EDIT')
    thigh = leg.data.edit_bones['bone']; thigh.name = 'thigh'
    thigh.head = (0, 0, 2); thigh.tail = (0, -.15, 1)
    calf = leg.data.edit_bones.new('calf'); calf.head = thigh.tail; calf.tail = (0, 0, .1)
    calf.parent = thigh; calf.use_connect = True
    foot = leg.data.edit_bones.new('foot'); foot.head = calf.tail; foot.tail = (0, -.3, .1)
    foot.parent = calf; foot.use_connect = True
    bpy.ops.object.mode_set(mode='OBJECT')
    lock = bpy.data.objects.new('Study-foot-lock', None); bpy.context.collection.objects.link(lock)
    lock.matrix_world = leg.pose.bones['foot'].matrix.copy()
    pole = bpy.data.objects.new('Study-knee-pole', None); bpy.context.collection.objects.link(pole)
    pole.location = (0, -2, 1)
    ik = leg.pose.bones['calf'].constraints.new('IK')
    ik.target = lock; ik.pole_target = pole; ik.chain_count = 2
    ik.use_stretch = False; ik.iterations = 128
    rotation = leg.pose.bones['foot'].constraints.new('COPY_ROTATION')
    rotation.target = lock; rotation.owner_space = rotation.target_space = 'WORLD'
    contacts = []
    for dx in (0, .03, .06):
        leg.location.x = dx; bpy.context.view_layer.update()
        foot = leg.pose.bones['foot']
        contacts.append([leg.matrix_world @ foot.head, leg.matrix_world @ foot.tail])
    slip = max((p - q).length for frame in contacts for p, q in zip(frame, contacts[0]))
    assert slip < .002, slip
    report['synthetic_ik_contact_drift_m'] = slip
    # Rigify generation API alone; MPFB weights and topology are a separate check.
    bpy.ops.preferences.addon_enable(module='rigify')
    bpy.ops.object.armature_human_metarig_add()
    meta = bpy.context.object; meta.name = 'Study-metarig'
    bpy.ops.pose.rigify_generate()
    generated = bpy.context.object
    assert any(b.name.startswith('DEF-') for b in generated.data.bones)
    report['stock_rigify_generation'] = {'status': 'PASS', 'bones': len(generated.data.bones)}
    if args.mpfb:
        bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
        from bl_ext.user_default.mpfb.services.rigservice import RigService
        human = HumanService.create_human()
        meta = HumanService.add_builtin_rig(human, 'rigify.human', import_weights=True)
        bpy.context.view_layer.update()
        rig = RigService.generate_rigify_rig(meta, name='Study-MPFB-rig', meta_rig_action='hide')
        assert rig is not None
        mods = [m for m in human.modifiers if m.type == 'ARMATURE']
        assert mods and all(m.object == rig for m in mods)
        assert any(not m.use_multi_modifier for m in mods)
        for m in mods[1:]:
            assert m.use_multi_modifier and m.vertex_group == 'mhmask-preserve-volume'
        deform = {g.index for g in human.vertex_groups if
                  g.name in rig.data.bones and rig.data.bones[g.name].use_deform}
        totals = [sum(g.weight for g in v.groups if g.group in deform) for v in human.data.vertices]
        # Original indices survive the helper Mask (no subdivision in this test).
        attr = human.data.attributes.new('StudyVertexID', 'INT', 'POINT')
        for vertex in human.data.vertices:
            attr.data[vertex.index].value = vertex.index
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        evaluated = human.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        visible = {mesh.attributes['StudyVertexID'].data[i].value
                   for polygon in mesh.polygons for i in polygon.vertices}
        evaluated.to_mesh_clear()
        visible_zero = [i for i in visible if totals[i] < 1e-6]
        visible_error = max(abs(totals[i] - 1) for i in visible)
        assert not visible_zero
        raw_visible_error = visible_error
        # Demonstrate explicit normalization of deform groups only. The source
        # weights have small rounding errors; this is not a visible-art failure.
        for vertex in human.data.vertices:
            if vertex.index not in visible:
                continue
            total = totals[vertex.index]
            for group in list(vertex.groups):
                if group.group in deform:
                    human.vertex_groups[group.group].add([vertex.index], group.weight / total, 'REPLACE')
        normalized = {v.index: sum(g.weight for g in v.groups if g.group in deform)
                      for v in human.data.vertices if v.index in visible}
        normalized_error = max(abs(t - 1) for t in normalized.values())
        assert normalized_error < 1e-4
        report['mpfb_rigify'] = {
            'status': 'PASS: generated rig is body modifier target',
            'vertices': len(totals), 'bones': len(rig.data.bones),
            'armature_modifiers': [{'name': m.name, 'multi': m.use_multi_modifier,
                                   'mask': m.vertex_group} for m in mods],
            'zero_deform_weight_vertices': sum(t < 1e-6 for t in totals),
            'max_deform_weight_sum_error': max(abs(t - 1) for t in totals),
            'visible_zero_deform_weight_vertices': len(visible_zero),
            'visible_raw_max_deform_weight_sum_error': raw_visible_error,
            'visible_normalized_max_deform_weight_sum_error': normalized_error,
            'note': 'Default body only; production kit, joint deformation and masks not certified',
        }
    bpy.ops.wm.save_as_mainfile(filepath=str(dest / 'technique-study.blend'))
    (dest / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('TECHNIQUE_PROBE', json.dumps(report))


if __name__ == '__main__':
    main()

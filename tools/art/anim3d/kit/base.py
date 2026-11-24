"""The shared cream stone base every unit stands on.

One stationary round disc: top #E9CFA0, side #B68A51 (sRGB), roughness 0.86,
fine low-contrast grain, contact surface at z = 0.105 m. It keeps a physical
BSDF so moving feet cast real contact shadows, plus camera-only pigment so the
warm stone reads as painted without lighting the figure. The figure painting
is never projected onto it (painted feet and shadows would stay behind).

Rebuilt from the Spearman's base as it stood after round 8 (scene.py,
project.py and infantry/refine.py). The Spearman also layers a CC0 Travertine
scan as faint bump; that asset is optional and not wired here.
NOT YET RUN FROM THE KIT IN BLENDER: check `audit.check_base` and a rest
render against the painting on first use, then update kit/README.md.

Open review item (art director, Spearman round 10): the rendered top was
(245,206,154) against the painting's (249,217,176) and the rim (219,172,114)
against (226,181,126). Measure the rendered base with
`python -m kit.regions --stats` and adjust `lift` rather than the shared hex
values.
"""
import bpy
from mathutils import Vector

NAME = 'Stationary cream stone'
TOP_HEX, RIM_HEX = 'E9CFA0', 'B68A51'
TOP_Z = .105


def linear(c):
    return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4


def colour(hex_value):
    """sRGB hex -> linear RGBA for a shader input."""
    return (*[linear(int(hex_value[i:i+2], 16)/255) for i in (0, 2, 4)], 1)


def _stone(name, hex_value, lift, camera_pigment, grain_scale=450):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat['sRGB_base'] = '#'+hex_value
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = colour(hex_value)
    bsdf.inputs['Roughness'].default_value = .86
    bsdf.inputs['Metallic'].default_value = 0
    bsdf.inputs['Specular IOR Level'].default_value = .18
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = grain_scale
    ramp = nodes.new('ShaderNodeValToRGB')
    # The hex values are albedo, not display values: under Standard the lit
    # stone renders darker than the painting, so pigment is lifted in linear
    # space while the BSDF keeps live shading.
    for element, factor in zip(ramp.color_ramp.elements, (.94, 1.04)):
        element.color = tuple(min(1, c*factor*k) for c, k in zip(base[:3], lift))+(1,)
    links.new(grain.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
    ray = nodes.new('ShaderNodeLightPath')
    pigment = nodes.new('ShaderNodeMath')
    pigment.operation = 'MULTIPLY'
    pigment.inputs[1].default_value = camera_pigment
    links.new(ray.outputs['Is Camera Ray'], pigment.inputs[0])
    links.new(pigment.outputs[0], bsdf.inputs['Emission Strength'])
    return mat


def build(scene, radius=.594, thickness=.155, top_z=TOP_Z, centre=(0, 0),
          top_lift=(1.03, 1.07, 1.14), rim_lift=(1, 1.05, 1.14),
          top_pigment=.50, rim_pigment=1.30):
    """Create the disc with its two materials and cloth collision.

    Defaults are the Spearman's measured values. `centre` is the disc centre
    on the ground; the Spearman's sits 0.20 m behind the origin along the
    camera's ground direction (see `centre_behind`) so the top ellipse matches
    its painting.
    """
    assert NAME not in bpy.data.objects, 'One base per scene'
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=radius, depth=thickness,
                                        location=(centre[0], centre[1], top_z-thickness/2))
    base = bpy.context.object
    base.name = NAME
    bevel = base.modifiers.new('Rounded stone edge', 'BEVEL')
    bevel.width, bevel.segments = .022, 5
    base.modifiers.new('Stone cloth collision', 'COLLISION')
    base.data.materials.append(_stone('Cream limestone', TOP_HEX, top_lift, top_pigment))
    base.data.materials.append(_stone('Cream limestone darker rim', RIM_HEX, rim_lift, rim_pigment))
    for poly in base.data.polygons:
        poly.material_index = 1 if abs(poly.normal.z) < .5 else 0
    if base.name not in scene.collection.all_objects:
        scene.collection.objects.link(base)
    return base


def centre_behind(camera, distance=.20):
    """Ground point `distance` metres behind the origin as seen from `camera`."""
    back = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    back.z = 0
    back = back.normalized()*distance
    return back.x, back.y

"""The shared cream stone base every unit stands on.

One stationary round disc: top #E9CFA0, side #B68A51 (sRGB), contact surface
at z = 0.105 m. The figure painting is never projected onto it (painted feet
and shadows would stay behind when the real feet move).

Dimensions are the Spearman's after its disc was measured against the painted
one row by row (round 12/13): radius 0.573 m (0.594 x 0.965) and a 163 mm
side band put rows 210-242 within 1 px of the painting at 256 px. A unit whose
painting shows the disc from the same camera can keep them; measure first
(`python -m kit.regions --rows`). The Spearman's disc also sits 0.20 m behind
the origin along the camera's ground direction (`centre_behind`).

Materials here are the Cycles fallback: a physical BSDF for real contact
shadows plus camera-only pigment. Under the standard Eevee painted look the
unit's look script replaces them at render time with a stone shaded from
colours measured on the painted disc (light lip, sandier wall, ground shadow
anchored to the ankles); see units/spearman/look.py `stone`.

NOT YET RUN FROM THE KIT IN BLENDER: check `audit.check_base` and a rest
render against the painting on first use, then update kit/README.md.
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


def build(scene, radius=.573, thickness=.163, top_z=TOP_Z, centre=(0, 0),
          top_lift=(1.03, 1.07, 1.14), rim_lift=(1, 1.05, 1.14),
          top_pigment=.50, rim_pigment=1.30):
    """Create the disc with its two materials and cloth collision.

    Defaults are the Spearman's values after its disc was fitted to the painting. `centre` is the disc centre
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


class SupportSurface:
    """World-space floor from evaluated faces, never a mesh's widest vertex.

    A lower skirt, bevel, translated mesh origin or loose vertex is not a
    stone top. Cast down onto actual faces so both fitting and auditing use
    the same support, including the rounded edge. Build once per static base;
    rebuild after changing its geometry or transform.
    """
    def __init__(self, base):
        from mathutils.bvhtree import BVHTree
        evaluated = base.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            faces = [list(p.vertices) for p in mesh.polygons]
            used = {i for face in faces for i in face}
            assert used, 'Base has no support faces'
            self.top = max(points[i].z for i in used)
            self.bottom = min(points[i].z for i in used)
            self.tree = BVHTree.FromPolygons(points, faces)
        finally:
            evaluated.to_mesh_clear()

    def stone_height(self, point):
        hit, normal, _, _ = self.tree.ray_cast(
            Vector((point.x, point.y, self.top+1)), Vector((0, 0, -1)),
            self.top-self.bottom+2)
        if hit is None or normal.z <= 0:
            return None
        # Ray intersection roundoff must not re-key a flat planted foot.
        return self.top if abs(hit.z-self.top) < 1e-6 else hit.z

    def height(self, point, ground=0., clearance=0.):
        stone = self.stone_height(point)
        return max(ground, stone+clearance) if stone is not None else ground

"""Pose audit for saved clips: camera bounds, ground and base contact, weapon
crossings, grip and clip-to-clip arm continuity.

Generalised from tools/art/anim3d/audit.py (Spearman rounds 4-10: 40 poses,
zero findings required). Lessons built in:
- Test contact against the REAL disc footprint plus world ground, not an
  infinite plane (round 6: a spearhead outside the disc was a false finding;
  a foot below the sole inside it was a real one).
- Read the base in its own local frame, so a translated base still tests its
  own footprint (round 7).
- Check a weapon shaft against armour with a ray along the shaft on evaluated
  geometry; an in-frame check alone misses visible crossings.
- A clip that starts or ends in idle must match idle's arm joints (2 mm), or
  the transition pops.

Run through the `blender` gate with one clip .blend open. Each function
returns findings as strings; an empty list is a pass. Tighten a limit when it
misses something; never loosen one to pass.
"""
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree

BASE_PALETTE = ['#E9CFA0', '#B68A51']


def check_base(base, palette=BASE_PALETTE, projection_uv='Painting camera rest'):
    """The shared cream base contract: no projected figure paint, shared palette,
    physical shading kept so moving feet cast real contact shadows.
    """
    findings = []
    if base.data.uv_layers.get(projection_uv) is not None:
        findings.append('base carries the figure projection (painted feet and shadows would stay behind)')
    if [m.get('sRGB_base') for m in base.data.materials] != palette:
        findings.append('shared cream base palette changed')
    for mat in base.data.materials:
        output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        if output.inputs['Surface'].links[0].from_node.type != 'BSDF_PRINCIPLED':
            findings.append(f'{mat.name}: base must keep physical contact shading')
    return findings


def base_frame(base, inset=.015):
    """(top z in world, inverse world matrix, footprint radius) of a round base."""
    top = max((base.matrix_world @ v.co).z for v in base.data.vertices)
    radius = max((v.co.x*v.co.x+v.co.y*v.co.y)**.5 for v in base.data.vertices)-inset
    return top, base.matrix_world.inverted(), radius


def check_bounds_and_contact(scene, base, label, tolerance=.01, ground=0.0):
    """One sampled frame: everything inside the camera, nothing through the
    base top inside its footprint, nothing below world ground outside it.
    """
    top, inverse, radius = base_frame(base)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bounds = [1., 1., 0., 0.]
    low, lowest, disc_low, disc_lowest = 100, None, 100, None
    for ob in scene.objects:
        if ob.type not in ('MESH', 'CURVE') or ob == base or ob.hide_render:
            continue
        evaluated = ob.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for v in mesh.vertices:
            w = ob.matrix_world @ v.co
            if w.z < low:
                low, lowest = w.z, ob.name
            local = inverse @ w
            if local.x*local.x+local.y*local.y <= radius**2 and w.z < disc_low:
                disc_low, disc_lowest = w.z, ob.name
            p = world_to_camera_view(scene, scene.camera, w)
            bounds = [min(bounds[0], p.x), min(bounds[1], p.y), max(bounds[2], p.x), max(bounds[3], p.y)]
        evaluated.to_mesh_clear()
    findings = []
    if min(bounds[:2]) < 0 or max(bounds[2:]) > 1:
        findings.append(f'{label}: geometry outside camera {bounds}')
    if disc_low < top-tolerance:
        findings.append(f'{label}: {disc_lowest} intersects base, z={disc_low:.4f}, top={top:.4f}')
    if low < ground:
        findings.append(f'{label}: {lowest} below ground, z={low:.4f}')
    return findings, {'camera_bounds': bounds, 'min_z': low, 'lowest_object': lowest,
                      'disc_min_z': disc_low, 'disc_lowest_object': disc_lowest}


def check_shaft(start, end, hand, blockers, label, released=False, grip_limit=.10):
    """A held shaft (spear, pike, musket): the hand stays on its axis and the
    segment start-end crosses none of the `blockers` (armour, shield, helmet).
    Points are world-space Vectors. Skip the grip test once it is released.
    """
    axis = (end-start).normalized()
    length = (end-start).length
    depsgraph = bpy.context.evaluated_depsgraph_get()
    findings = []
    distance = ((hand-start)-axis*(hand-start).dot(axis)).length
    if not released and distance > grip_limit:
        findings.append(f'{label}: hand is {distance:.3f} m from shaft')
    crossings = []
    for ob in blockers:
        evaluated = ob.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        tree = BVHTree.FromPolygons([ob.matrix_world @ v.co for v in mesh.vertices],
                                    [list(p.vertices) for p in mesh.polygons])
        if tree.ray_cast(start, axis, length)[0] is not None:
            crossings.append(ob.name)
        evaluated.to_mesh_clear()
    if crossings:
        findings.append(f'{label}: shaft intersects {", ".join(crossings)}')
    return findings


ARM_BONES = ('upperarm_r', 'lowerarm_r', 'hand_r', 'upperarm_l', 'lowerarm_l', 'hand_l')


def arm_joints(rig, bones=ARM_BONES):
    """World joint positions; record at idle's first sample and at each clip's
    first (and, for attack/hit, last) sample, then compare with `check_transition`.
    """
    return {name: rig.matrix_world @ rig.pose.bones[name].head for name in bones}


def check_transition(idle, other, label, limit=.002):
    """Elbows as well as hands must match the idle guard (round 7: matching
    hand targets alone left the elbow poles different).
    """
    return [f'{label}: {name} differs from idle by {(other[name]-point).length:.4f} m'
            for name, point in idle.items() if (other[name]-point).length > limit]

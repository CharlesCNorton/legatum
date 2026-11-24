"""Blender regression: widened bottom/loose vertices cannot create a top."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.base import SupportSurface
from kit.audit import base_frame

bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=.58, depth=.10)
base = bpy.context.object
for v in base.data.vertices:
    if v.co.z < 0:
        v.co.x *= .77/.58
        v.co.y *= .77/.58
base.data.vertices.add(1)
base.data.vertices[-1].co = (2, 2, 3)  # unrelated loose vertex is not support
base.location = (1.3, -.8, .055)
base.scale.y = .8
base.data.update()
bpy.context.view_layer.update()
support = SupportSurface(base)
assert abs(support.top-.105) < 1e-6
assert abs(support.height(Vector((1.3, -.8, -1)))-.105) < 1e-6
assert support.height(Vector((2.1, -.8, 0)), ground=.006) == .006
assert 0 < support.height(Vector((2, -.8, 0))) < .07  # sloping rim, not top
assert support.stone_height(Vector((1.3, -.15, 0))) is None  # ellipse, not circle
top, inverse, radius = base_frame(base, inset=0)
assert abs(top-.105) < 1e-6 and abs(radius-.464) < 1e-5
print('SUPPORT_OK: transformed ellipse, wider bottom, loose vertex, rim height, world ground')
print('WIDE_RING_HEIGHT', {'old_infinite_top_m': .105,
    'evaluated_surface_m': support.height(Vector((2, -.8, 0)))})

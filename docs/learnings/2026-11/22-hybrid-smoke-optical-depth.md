# Hybrid smoke: grid occupancy is not rendered transparency

The lead's v6 render showed a box-like opaque column despite a nonuniform
Mantaflow cache and density-linked boundary fades. Python reads of the MNT3 noise
grids at frames 1, 72 and 144 found maximum densities of 7.51–8.11. Integrating
density through the 28-world-unit depth with the existing feathers and gain 3.4
puts 86–90% of occupied columns above optical depth 3 (less than 5% transmission).
This supports optical saturation as the primary diagnosis; render verification
of the correction remains with the lead.

Use gain 0.035, explicit world-position normalization for the domain feathers,
and Volume Info scalar outputs. Blender's generic Attribute Fac averages RGB;
Volume Info extracts the scalar R channel directly. Principled Volume's density
scales both scattering and absorption; color alone is not a density-independent
fog term. Its explicit emission is independent of density, so retain the flame
grid gate and boundary envelope on emission. Leave internal density/color
attributes empty to avoid an additional multiplier, and built-in blackbody off.

Primary implementation references:
- https://raw.githubusercontent.com/blender/blender/main/source/blender/gpu/shaders/material/gpu_shader_material_attribute.bsl.hh
- https://raw.githubusercontent.com/blender/blender/main/source/blender/gpu/shaders/material/gpu_shader_material_volume_principled.bsl.hh

The scholars use emission-painted geometry; their spill is a masked color add,
so halving its 0.48 coefficient to 0.24 changes the tint without dimming the point
light that warms the actual volume. Preserve the lead's height warnings.

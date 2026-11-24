"""Restrained wool follow-through for the accepted walk and authored attack.

Configure a fresh master before its per-clip bake. Only wool pins and solver
settings change; body actions, donor rotations, geometry and paint stay intact.
"""


def configure(cloak, clip):
    if clip not in ('move', 'attack'):
        return None
    cloth = cloak.modifiers['Cloth per clip']
    pins = cloak.vertex_groups['Shoulder pins']
    # Lower pins retain the fitted silhouette while the centre can lag. Full
    # shoulder pins remain exactly one; never free a corner to get more motion.
    factor = 1.8 if clip == 'move' else .85
    for vertex in cloak.data.vertices:
        for group in vertex.groups:
            if group.group == pins.index and group.weight < .99:
                pins.add([vertex.index], min(.80, group.weight * factor), 'REPLACE')
    cloth.settings.bending_stiffness = 2.0 if clip == 'move' else 1.2
    cloth.settings.air_damping = 6.0 if clip == 'move' else 5.0
    return {'method': 'shoulder-pinned wool, restrained lower pins and air damping',
            'lower_pin_factor': factor,
            'bending_stiffness': cloth.settings.bending_stiffness,
            'air_damping': cloth.settings.air_damping}

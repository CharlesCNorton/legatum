"""Restrained wool follow-through for the accepted walk and authored attack.

Configure a fresh master before its per-clip bake. Only wool pins and solver
settings change; body actions, donor rotations, geometry and paint stay intact.
"""


def configure(cloak, clip):
    if clip not in ('move', 'attack'):
        return None
    from kit.cloth import configure as configure_cloth
    return configure_cloth(cloak, pin_group='Shoulder pins', modifier='Cloth per clip',
                           lower_pin_factor=1.8 if clip == 'move' else .85,
                           bending=2.0 if clip == 'move' else 1.2,
                           air=6.0 if clip == 'move' else 5.0)

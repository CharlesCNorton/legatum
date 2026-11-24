"""Configure secondary cloth before baking a fresh master.

Keep full attachment pins; unit presets supply the measured response. This
changes neither rig actions nor geometry, and is deliberately not cumulative.
"""


def configure(ob, *, pin_group, modifier, lower_pin_factor, bending, air,
              attachment_threshold=.99, lower_pin_cap=.80):
    cloth = ob.modifiers[modifier]
    pins = ob.vertex_groups[pin_group]
    for vertex in ob.data.vertices:
        for group in vertex.groups:
            if group.group == pins.index and group.weight < attachment_threshold:
                pins.add([vertex.index], min(lower_pin_cap, group.weight * lower_pin_factor), 'REPLACE')
    cloth.settings.bending_stiffness = bending
    cloth.settings.air_damping = air
    return {'method': 'shoulder-pinned wool, restrained lower pins and air damping',
            'lower_pin_factor': lower_pin_factor,
            'bending_stiffness': cloth.settings.bending_stiffness,
            'air_damping': cloth.settings.air_damping}

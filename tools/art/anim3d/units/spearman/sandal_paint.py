"""Keep the painting's instep bands and toes together across leather/skin IDs.

The fine leather IDs are narrower than the painted bands. Eroding each ID and
then filling the neighbouring skin from that leather discarded the light toes
and most strap edges. Share original pigment inside the combined foot footprint;
retain the existing continuation elsewhere. This never changes geometry/alpha.
"""
import numpy as np


def foot_regions(ids, parts):
    y = 12 + (np.arange(ids.shape[0]) + .5 - 9) * 232 / 1236
    x = 75 + (np.arange(ids.shape[1]) + .5 - 349) * 105 / 556
    skin = ids == parts.index('skin')
    regions = {}
    for side, lo, hi in [('r', 88, 115), ('l', 144, 169)]:
        box = (y[:, None] >= 204) & (y[:, None] < 222) & (x[None, :] >= lo) & (x[None, :] < hi)
        regions['sandal_'+side] = box & (skin | (ids == parts.index('sandal_'+side)))
    return regions

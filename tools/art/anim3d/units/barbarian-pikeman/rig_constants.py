"""One registered straight pike axis for geometry, motion and audits."""
import math


def painting_point(x, y, depth=-.26):
    return ((x / 256 - .5) * 2.6, depth,
            1.105 + ((.5 - y / 256) * 2.6 - depth * math.sin(.22)) / math.cos(.22))


PIKE_START = painting_point(12.5, 221.8)
PIKE_END = painting_point(243.5, 16)
PIKE_ORIGIN = (-.24, -.26, 1.06)

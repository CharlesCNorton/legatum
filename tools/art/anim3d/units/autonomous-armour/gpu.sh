#!/usr/bin/env bash
# Complete, serial host pass. The Blender PATH shim owns CPU/GPU scheduling.
set -euo pipefail
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU
export SAMPLES="${SAMPLES:-96}" RESOLUTION=512
export ROUND="${ROUND:-1}"
exec tools/art/anim3d/units/autonomous-armour/render.sh final

#!/usr/bin/env bash
# Host-only final rerender, followed by fresh packing/validation. No rebuilding.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
export UNIT=archer RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-64}"
for stage in c c-details d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "$stage"
done
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/archer/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/archer/validate.py
tools/art/anim3d/render.sh audit

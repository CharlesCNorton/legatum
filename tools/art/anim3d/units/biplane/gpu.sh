#!/usr/bin/env bash
# Complete lead-side pass; run from repo root, no arguments, ROUND supplied by driver.
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/biplane
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-96}"
export ROUND="${ROUND:-1}" REQUIRE_GPU=1
PY="$ANIM_ROOT/venv/bin/python"
# Preserve build/paint/rig work; regenerate every review stage and all 40 final frames.
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  "$UNIT/render.sh" "$stage"
  "$PY" "$UNIT/review.py" "$stage"
done
"$PY" "$UNIT/deliver.py"
"$PY" "$UNIT/check.py"

"$UNIT/render.sh" audit

#!/usr/bin/env bash
# Driver entry point, no arguments, invoked from repo root. ROUND is supplied by driver.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/crossbowman
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-1}"
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
# Rebuild source and all five actions before final renders; Blender stays behind PATH gate.
"$unit/render.sh" build
"$unit/render.sh" bake
"$unit/render.sh" animate
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  STAGE="$stage" "$unit/render.sh" render
  "$ANIM_ROOT/venv/bin/python" "$unit/post.py" review "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" video
"$unit/render.sh" audit
# Technical success never writes the visual PASS marker; review the split-screen and clips.

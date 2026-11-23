#!/usr/bin/env bash
# No arguments. Run from repo root. The Blender PATH gate serializes GPU work.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/peltast
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  "$unit/render.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$unit/pack.py"
"$ANIM_ROOT/venv/bin/python" "$unit/validate.py"
"$unit/render.sh" audit
"$ANIM_ROOT/venv/bin/python" "$unit/mp4.py"
printf '%s\n' '- GPU pass: all review stages, 512/256 masters, trimmed 160 px atlas, validation, audit and round MP4 completed. Art verdict remains manual.' >> "$REVIEW/peltast-log.md"

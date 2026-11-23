#!/usr/bin/env bash
# No arguments; run from repo root. Host driver provides ROUND.
set -euo pipefail
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-64}"
unit_dir=tools/art/anim3d/units/medjay
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
 "$unit_dir/render.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" pack
"$unit_dir/render.sh" audit
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" video

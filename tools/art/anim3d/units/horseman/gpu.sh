#!/usr/bin/env bash
# No arguments; run from the repository root. ROUND is supplied by the driver.
set -euo pipefail
source tools/art/anim3d/env.sh
export UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU
export SAMPLES="${SAMPLES:-64}" RESOLUTION=512
python="$ANIM_ROOT/venv/bin/python"
# Rebuild from the preserved baked master, so the handoff includes current source edits.
"$python" tools/art/anim3d/mounted/prepare.py
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh animate
tools/art/anim3d/render.sh audit
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "$stage"
done
"$python" tools/art/anim3d/mounted/pack.py
"$python" tools/art/anim3d/mounted/validate.py
"$python" tools/art/anim3d/units/horseman/movie.py

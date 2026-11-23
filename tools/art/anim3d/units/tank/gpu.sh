#!/usr/bin/env bash
# Complete lead-side pass; invoke without arguments from the repository root.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-256}"
export ROUND="${ROUND:-2}"
for stage in b c details d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "vehicles-$stage"
done
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/archive.py --require-512
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/deliver.py
tools/art/anim3d/render.sh vehicles-audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/video.py

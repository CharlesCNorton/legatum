#!/usr/bin/env bash
# Run from repo root, no arguments. ROUND is provided by the overnight driver.
set -euo pipefail
export CYCLES_DEVICE=GPU RENDER_ENGINE=CYCLES RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
tools/art/anim3d/units/artillery/render.sh final
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/deliver.py

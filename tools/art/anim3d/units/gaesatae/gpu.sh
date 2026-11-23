#!/usr/bin/env bash
# No arguments; called by the overnight driver from the repository root.
set -euo pipefail
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU CYCLES_BACKEND=METAL RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
unit=tools/art/anim3d/units/gaesatae
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/render.py" -- all
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" --movie

#!/usr/bin/env bash
# No arguments; run from the repository root. ROUND is supplied by the driver.
set -euo pipefail
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/cataphract/audit.py
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/cataphract/render.py -- all
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cataphract/deliver.py

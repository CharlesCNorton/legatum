#!/usr/bin/env bash
# No arguments. Run from the repository root after the model/clip build.
set -euo pipefail
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-1}"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES="${SAMPLES:-48}" RESOLUTION=512
export STAGES=b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death
tools/art/anim3d/units/cuirassier/render.sh audit
tools/art/anim3d/units/cuirassier/render.sh render
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/validate.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/video.py

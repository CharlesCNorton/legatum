#!/usr/bin/env bash
# No arguments. Run from the repository root; ROUND is supplied by the driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-1}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
unit=tools/art/anim3d/units/barbarian-musketman
python="$ANIM_ROOT/venv/bin/python"
"$python" "$unit/prepare.py"
# Rebuild guarantees that all stages and clips use this checkout's exact source.
"$unit/render.sh" build
"$unit/render.sh" animate
"$unit/render.sh" render
"$unit/render.sh" audit
"$python" "$unit/finish.py" pack
"$python" "$unit/finish.py" validate

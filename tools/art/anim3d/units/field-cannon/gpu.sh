#!/usr/bin/env bash
# No arguments. Run from this checkout; the overnight driver provides ROUND.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512
export SIEGE_REUSE_MASTER=1 SIEGE_STAGES=b,c,detail,d,e-idle,e-move,e-attack,e-hit,e-death
export ROUND="${ROUND:-3}"
test -f "$ANIM_ROOT/masters/field-cannon/field-cannon.blend"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/siege/round.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/validate.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/video.py
# Size/geometry success is not art approval: never manufacture a PASS marker here.

#!/usr/bin/env bash
# No arguments. Run from this checkout's repository root on the lead's Metal host.
set -euo pipefail
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-64}"
export ROUND="${ROUND:-1}"
unit_dir=tools/art/anim3d/units/phalangite
"$unit_dir/run.sh" audit
"$unit_dir/run.sh" all
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" movie
printf '%s\n' "Phalangite GPU round $ROUND rendered, packed and validated; visual review still required."

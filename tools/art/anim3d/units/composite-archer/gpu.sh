#!/usr/bin/env bash
# Complete host GPU pass. No arguments; ROUND is supplied by the driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" UNIT=composite-archer
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unit_dir=tools/art/anim3d/units/composite-archer
master="$ANIM_ROOT/masters/composite-archer"
receipt="$ANIM_ROOT/review/3d-v2/composite-archer-gpu-round${ROUND}.json"
exec >> "$ANIM_ROOT/gpu-logs-composite-archer-r${ROUND}.log" 2>&1
trap 'code=$?; echo "FAILED exit=$code command=$BASH_COMMAND"; exit "$code"' ERR
rm -f "$receipt"
echo "Starting composite archer GPU round $ROUND"
git rev-parse HEAD
command -v blender
test -s "$master/composite-archer.blend"
test -s "$master/registered.blend"
tools/art/anim3d/render.sh animate
tools/art/anim3d/render.sh plain_views
tools/art/anim3d/render.sh final
tools/art/anim3d/render.sh feet
"$ANIM_ROOT/venv/bin/python" "$unit_dir/gpu_check.py"
"$ANIM_ROOT/venv/bin/python" "$unit_dir/movie.py"
"$ANIM_ROOT/venv/bin/python" "$unit_dir/gpu_check.py" --receipt
echo 'GPU delivery complete; visual approval remains separate.'

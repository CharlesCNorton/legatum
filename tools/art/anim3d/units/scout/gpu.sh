#!/usr/bin/env bash
# Complete driver entry point, from this checkout; never creates the art PASS marker.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
export UNIT=scout RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
log="$ANIM_ROOT/review/3d-v2/scout-gpu-round${ROUND}.log"
receipt="$ANIM_ROOT/review/3d-v2/scout-gpu-round${ROUND}.json"
rm -f "$receipt"
exec > "$log" 2>&1
trap 'echo "FAILED line=$LINENO command=$BASH_COMMAND exit=$?"' ERR
echo "Scout GPU round $ROUND; checkout $(pwd); revision $(git rev-parse HEAD)"
command -v blender
test -s "$ANIM_ROOT/masters/scout/scout.blend"
test -s "$ANIM_ROOT/masters/scout/scout-unpainted.blend"
tools/art/anim3d/render.sh animate
tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh final
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/scout/check_delivery.py
tools/art/anim3d/render.sh pack
tools/art/anim3d/render.sh validate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/scout/video.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/scout/check_delivery.py --receipt
echo "Complete; visual review still required."

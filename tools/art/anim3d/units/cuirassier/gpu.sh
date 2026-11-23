#!/usr/bin/env bash
# Complete no-argument host pass. GPU unavailable is a failure, never CPU fallback.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
log="$ANIM_ROOT/gpu-logs-cuirassier-r${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/cuirassier-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/cuirassier-gpu-round${ROUND}.json"
rm -f "$receipt"
exec >> "$log" 2>&1
stage=preflight
trap 'code=$?; echo "failed: $stage (exit $code)" > "$status"; exit "$code"' ERR
echo "running round $ROUND: $PWD" > "$status"
git rev-parse HEAD
git status --short
command -v blender
test -s "$ANIM_ROOT/masters/cuirassier/cuirassier-plain.blend"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES="${SAMPLES:-64}" RESOLUTION=512
export STAGES=b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death
unit=tools/art/anim3d/units/cuirassier
stage=gpu-check
"$unit/render.sh" gpu_check
for stage in paint animate audit render; do "$unit/render.sh" "$stage"; done
for stage in pack validate video; do "$ANIM_ROOT/venv/bin/python" "$unit/$stage.py"; done
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$unit/gpu_receipt.py"
echo "complete round $ROUND; visual review pending, no art PASS" > "$status"

#!/usr/bin/env bash
# Complete no-argument driver handoff; technical success is never visual approval.
set -eEuo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/barbarian-crossbowman
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-3}"
status="$ANIM_ROOT/review/3d-v2/barbarian-crossbowman-gpu-status.txt"
log="$ANIM_ROOT/gpu-logs-barbarian-crossbowman-r${ROUND}.log"
exec >> "$log" 2>&1
stage=source-inputs
trap 'code=$?; printf "round=%s failed stage=%s exit=%s\n" "$ROUND" "$stage" "$code" > "$status"; exit "$code"' ERR
trap 'printf "round=%s interrupted stage=%s\n" "$ROUND" "$stage" > "$status"; exit 130' INT TERM
printf 'round=%s running\n' "$ROUND" > "$status"
printf 'checkout=%s round=%s blender=%s\n' "$PWD" "$ROUND" "$(command -v blender)"
git rev-parse HEAD
git status --short -- "$unit"
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
stage=preflight
# Device discovery does not render; use the CPU slot rather than queueing for the GPU.
CYCLES_DEVICE=CPU "$unit/render.sh" gpu-check
for stage in build bake animate audit; do "$unit/render.sh" "$stage"; done
stage=feet
"$unit/render.sh" feet
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  STAGE="$stage" "$unit/render.sh" render
  "$ANIM_ROOT/venv/bin/python" "$unit/post.py" review "$stage"
done
stage=verify-masters
"$ANIM_ROOT/venv/bin/python" "$unit/check_delivery.py" gpu
for stage in pack validate video; do "$ANIM_ROOT/venv/bin/python" "$unit/post.py" "$stage"; done
stage=verify-video
"$ANIM_ROOT/venv/bin/python" "$unit/check_delivery.py" video
printf 'round=%s complete GPU512/gallery256; atlas/video verified; visual review pending\n' "$ROUND" > "$status"

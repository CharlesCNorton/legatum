#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/byzantine-heir
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
: "${ROUND:=2}"
export ROUND
LOG="$ANIM_ROOT/masters/byzantine-heir/gpu-round${ROUND}.log"
STATUS="$ANIM_ROOT/review/3d-v2/byzantine-heir-gpu-status.txt"
mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1
stage=preflight
trap 'code=$?; printf "round %s failed: %s (exit %s); log %s\n" "$ROUND" "$stage" "$code" "$LOG" > "$STATUS"; exit "$code"' ERR
printf 'round %s running; log %s\n' "$ROUND" "$LOG" > "$STATUS"
printf 'Round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
test -f "$ANIM_ROOT/masters/byzantine-heir/byzantine-heir.blend"
test ! -f "$ANIM_ROOT/masters/byzantine-heir/bake-required"
blender -b --disable-autoexec --python-exit-code 1 --gpu-backend metal --python "$UNIT/render.py" -- check-gpu
stage=finish
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/refine.py"
stage=animate
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/render.py" -- animate
for stage in b c e-idle e-move e-attack e-hit e-death g-feet; do
  blender -b --disable-autoexec --python-exit-code 1 --gpu-backend metal --python "$UNIT/render.py" -- "$stage"
  "$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" review "$stage"
done
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/audit.py"
stage=verify-gpu
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" verify-gpu
for stage in pack validate video; do
  "$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" "$stage"
done
printf 'round %s complete: GPU512/48, gallery256, atlas, validation and MP4; pending visual review; log %s\n' "$ROUND" "$LOG" > "$STATUS"

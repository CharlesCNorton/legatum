#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/byzantine-heir
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
: "${ROUND:=3}"
export ROUND
LOG="$ANIM_ROOT/masters/byzantine-heir/gpu-round${ROUND}.log"
STATUS="$ANIM_ROOT/review/3d-v2/byzantine-heir-gpu-status.txt"
mkdir -p "$(dirname "$LOG")"
run_pass() {
stage=preflight
trap 'code=$?; printf "round %s failed: %s (exit %s); log %s\n" "$ROUND" "$stage" "$code" "$LOG" > "$STATUS"; exit "$code"' ERR
printf 'round %s running; log %s\n' "$ROUND" "$LOG" > "$STATUS"
printf 'Round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
test -f "$ANIM_ROOT/masters/byzantine-heir/projection-input.blend"
test -f "$UNIT/finish_geometry.py"
test -f "$UNIT/garment.py"
test ! -f "$ANIM_ROOT/masters/byzantine-heir/bake-required"
blender -b --disable-autoexec --python-exit-code 1 --gpu-backend metal --python "$UNIT/render.py" -- check-gpu
stage=finish
printf 'Stage %s\n' "$stage"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/refine.py"
stage=animate
printf 'Stage %s\n' "$stage"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/render.py" -- animate
for stage in b c e-idle e-move e-attack e-hit e-death g-feet; do
  printf 'Stage %s\n' "$stage"
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
}
# Ordinary pipes work in the sandbox too; process-substitution /dev/fd does not.
run_pass 2>&1 | tee -a "$LOG"

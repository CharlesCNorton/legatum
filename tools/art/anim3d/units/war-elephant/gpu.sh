#!/usr/bin/env bash
# Lead/driver entry point. Only serialized host GPU renders, no hidden CPU fallback.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-3}"
log="$ANIM_ROOT/gpu-logs-war-elephant-r${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/war-elephant-gpu-status.txt"
exec >> "$log" 2>&1
stage=preflight
trap 'code=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
date -u
git rev-parse HEAD
git status --short
command -v blender
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE=GPU
export RESOLUTION=512
export SAMPLES="${SAMPLES:-64}"
unit=tools/art/anim3d/units/war-elephant
test -s "$ANIM_ROOT/masters/war-elephant/sculpt-input.blend"
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
if [[ "$RENDER_ENGINE" == CYCLES ]]; then
  # Device inventory does not render; use a CPU slot so missing Metal is
  # reported without waiting behind an unrelated long GPU render.
  CYCLES_DEVICE=CPU blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/check_gpu.py"
fi
for stage in project animate audit b c d g e-idle e-move e-attack e-hit e-death; do
  printf 'running round=%s stage=%s\n' "$ROUND" "$stage" > "$status"
  printf '\nROUND %s STAGE %s\n' "$ROUND" "$stage"
  "$unit/run.sh" "$stage"
done
stage=masters
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" masters
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
stage=video
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" video
printf 'complete round=%s GPU512; visual review pending; no art PASS\n' "$ROUND" > "$status"

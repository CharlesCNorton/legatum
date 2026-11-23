#!/usr/bin/env bash
# Complete no-argument host GPU pass. ROUND is supplied by the overnight driver.
set -euo pipefail
cd "$(cd "$(dirname "$0")/../../../../.." && pwd)"
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
unit=tools/art/anim3d/units/cataphract
status="$ANIM_ROOT/review/3d-v2/cataphract-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/cataphract-gpu-round${ROUND}.json"
mkdir -p "$(dirname "$status")"
exec >> "$ANIM_ROOT/gpu-logs-cataphract-r${ROUND}.log" 2>&1
stage=preflight
trap 'code=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
rm -f "$receipt"
test -s "$ANIM_ROOT/masters/cataphract/cataphract.blend"
test -s "$ANIM_ROOT/masters/cataphract/plain.blend"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/gpu_preflight.py"
stage=animate
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/animate.py"
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
stage=render
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/render.py" -- all
stage=delivery
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py"
stage=verify
"$ANIM_ROOT/venv/bin/python" "$unit/verify.py" --gpu
printf 'complete round=%s GPU512/64; pending visual review\n' "$ROUND" > "$status"

#!/usr/bin/env bash
# Complete no-argument host pass. Every Blender process uses the PATH gate.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
unit=tools/art/anim3d/units/barbarian-musketman
python="$ANIM_ROOT/venv/bin/python"
status="$ANIM_ROOT/review/3d-v2/barbarian-musketman-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/barbarian-musketman-round${ROUND}-gpu.json"
log="$ANIM_ROOT/gpu-logs-barbarian-musketman-r${ROUND}.log"
exec > "$log" 2>&1
stage=preflight
trap 'code=$?; printf "failed stage=%s exit=%s round=%s\n" "$stage" "$code" "$ROUND" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
rm -f "$receipt"
printf 'Round %s, checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
(( SAMPLES >= 48 ))
"$unit/render.sh" preflight
stage=prepare
"$python" "$unit/prepare.py"
stage=build
"$unit/render.sh" build
stage=animate
"$unit/render.sh" animate
stage=render
"$unit/render.sh" render
stage=audit
"$unit/render.sh" audit
stage=pack
"$python" "$unit/finish.py" pack
stage=validate
"$python" "$unit/finish.py" validate
stage=regressions
"$python" "$unit/test_delivery.py"
stage=gpu_receipt
"$python" "$unit/finish.py" gpu-receipt
printf 'complete round=%s; GPU512 and delivery verified; visual review pending\n' "$ROUND" > "$status"

#!/usr/bin/env bash
# Complete no-argument host GPU pass. ROUND is provided by the overnight driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" CYCLES_DEVICE=GPU RENDER_ENGINE=CYCLES RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
log="$ANIM_ROOT/artillery-gpu-pass-r${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/artillery-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/artillery-gpu-receipt-r${ROUND}.json"
rm -f "$receipt"
exec > "$log" 2>&1
stage=preflight
trap 'code=$?; printf "failed: round %s, stage %s, exit %s; log %s\n" "$ROUND" "$stage" "$code" "$log" > "$status"; exit "$code"' ERR
printf 'running: round %s\n' "$ROUND" > "$status"
printf 'checkout: %s\n' "$PWD"
git rev-parse HEAD
git status --short
command -v blender
for file in painting-source.png painted-olive.png; do
  test -s "$ANIM_ROOT/assets/artillery/$file"
done
stage=build-bake-render
tools/art/anim3d/units/artillery/render.sh final
stage=verify-gpu-masters
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/check.py --require-gpu
stage=pack-validate-video
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/deliver.py
stage=receipt
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/check.py --require-gpu --receipt
printf 'complete: round %s; GPU masters, atlas and MP4 verified; visual review pending\n' "$ROUND" > "$status"

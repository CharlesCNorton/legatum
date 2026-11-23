#!/usr/bin/env bash
# Complete no-argument host pass. Technical success never creates an art PASS.
set -Eeuo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export UNIT=archer ROUND="${ROUND:-2}"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unit=tools/art/anim3d/units/archer
receipt="$REVIEW/archer-gpu-round${ROUND}.json"
status="$REVIEW/archer-gpu-status.txt"
transcript="$ANIM_ROOT/gpu-logs-archer-r${ROUND}.log"
rm -f "$receipt"
printf 'running round=%s\n' "$ROUND" > "$status"
exec >> "$transcript" 2>&1
trap 'code=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$code" > "$status"; exit "$code"' ERR
stage=preflight
printf 'Archer GPU round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
command -v blender
test -s "$ANIM_ROOT/masters/archer/archer.blend"
test -s "$ANIM_ROOT/assets/archer/painting-aligned.png"
for clip in idle move attack hit death; do
  test -s "$ANIM_ROOT/masters/archer/clips/$clip.blend"
done
stage=audit
tools/art/anim3d/render.sh audit
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "$stage"
done
stage=master-validation
"$ANIM_ROOT/venv/bin/python" "$unit/check_gpu.py"
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit/pack.py"
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit/validate.py"
stage=video
"$ANIM_ROOT/venv/bin/python" "$unit/video.py"
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$unit/check_gpu.py" --receipt
printf 'complete round=%s GPU512/64; pending visual review\n' "$ROUND" > "$status"

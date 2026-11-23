#!/usr/bin/env bash
# Complete host-only pass. No arguments; ROUND is supplied by the driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" UNIT=settler
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unset PREVIEW CLIP
review="$ANIM_ROOT/review/3d-v2"
status="$review/settler-gpu-status.txt"
receipt="$review/settler-gpu-round${ROUND}.json"
rm -f "$receipt"
exec > >(tee "$ANIM_ROOT/settler-gpu-round${ROUND}.log") 2>&1
stage=preflight
git rev-parse HEAD
git status --short
trap 'code=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
test -s "$ANIM_ROOT/masters/settler/settler.blend"
test -s "$ANIM_ROOT/masters/settler/settler-plain.blend"
command -v blender
command -v ffmpeg
command -v ffprobe
# render.py verifies a real Metal device and refuses CPU fallback.
for stage in b c c-details animate d e-idle e-move e-attack e-hit e-death g audit; do
  tools/art/anim3d/units/settler/render.sh "$stage"
done
stage=master-gate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/settler/check_delivery.py
stage=pack
tools/art/anim3d/units/settler/render.sh pack
stage=validate
tools/art/anim3d/units/settler/render.sh validate
stage=video
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/settler/video.py
stage=receipt
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/settler/check_delivery.py --receipt
printf 'complete round=%s; pending visual review\n' "$ROUND" > "$status"

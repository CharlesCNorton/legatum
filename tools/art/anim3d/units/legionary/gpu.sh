#!/usr/bin/env bash
# Complete host pass; the PATH Blender gate serializes the GPU work.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
log="$ANIM_ROOT/gpu-logs-legionary-r${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/legionary-gpu-status.txt"
exec >>"$log" 2>&1
trap 'code=$?; printf "FAILED round=%s exit=%s command=%s\n" "$ROUND" "$code" "$BASH_COMMAND" >"$status"; exit "$code"' ERR
printf 'RUNNING round=%s\n' "$ROUND" >"$status"
date -u
git rev-parse HEAD
git status --short
command -v blender
test -s "$ANIM_ROOT/masters/legionary/legionary.blend"
export UNIT=legionary RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
unset CLIP
export STAGES=animate,b,c,d,e-idle,e-move,e-attack,e-hit,e-death,audit
tools/art/anim3d/units/legionary/run.sh round
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/check_delivery.py --gpu
tools/art/anim3d/units/legionary/run.sh pack
tools/art/anim3d/units/legionary/run.sh validate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/video.py
printf 'COMPLETE round=%s GPU512/gallery256 atlas/video validated; visual acceptance pending\n' "$ROUND" >"$status"

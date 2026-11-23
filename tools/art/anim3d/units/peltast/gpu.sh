#!/usr/bin/env bash
# No arguments. Run from repo root. The Blender PATH gate serializes GPU work.
set -Eeuo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/peltast
export ROUND="${ROUND:-2}"
transcript="$ANIM_ROOT/gpu-logs-peltast-r${ROUND}.log"
status="$REVIEW/peltast-gpu-status.txt"
receipt="$REVIEW/peltast-gpu-round${ROUND}.json"
exec >> "$transcript" 2>&1
stage=preflight
trap 'code=$?; printf "failed: %s (exit %s)\n" "$stage" "$code" > "$status"; exit "$code"' ERR
rm -f "$receipt"
printf 'running round %s\n' "$ROUND" > "$status"
date -u
git rev-parse HEAD
git status --short -- "$unit"
command -v blender
test -f "$ANIM_ROOT/masters/peltast/peltast.blend"
test -f "$ANIM_ROOT/masters/peltast/peltast-unpainted.blend"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
stage=animate
"$unit/render.sh" animate
stage=audit
"$unit/render.sh" audit
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  "$unit/render.sh" "$stage"
done
stage=verify-gpu-masters
"$ANIM_ROOT/venv/bin/python" "$unit/check_gpu.py"
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit/pack.py"
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit/validate.py"
stage=video
"$ANIM_ROOT/venv/bin/python" "$unit/mp4.py"
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$unit/check_gpu.py" --receipt
printf 'complete: round %s; pending visual review\n' "$ROUND" > "$status"
printf '%s\n' '- GPU pass: all review stages, 512/256 masters, trimmed 160 px atlas, validation, audit and round MP4 completed. Art verdict remains manual.' >> "$REVIEW/peltast-log.md"

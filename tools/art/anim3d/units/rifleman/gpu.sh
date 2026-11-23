#!/usr/bin/env bash
# One complete host GPU pass. Art approval remains a visual decision.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-1}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
unit=tools/art/anim3d/units/rifleman
status="$REVIEW/rifleman-gpu-status.txt"
mkdir -p "$ANIM_ROOT/masters/rifleman"
exec >> "$ANIM_ROOT/masters/rifleman/gpu-round${ROUND}.log" 2>&1
stage=preflight
trap 'rc=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$rc" > "$status"; exit "$rc"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
git rev-parse HEAD
git status --short
command -v blender
stage=build
"$unit/render.sh" build
stage=animate
"$unit/render.sh" animate
stage=clips
"$unit/render.sh" preview
stage=feet
"$unit/render.sh" feet
stage=audit
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/audit.py"
stage=pack_validate_video
"$ANIM_ROOT/venv/bin/python" "$unit/finish.py"
stage=verify_gpu
"$ANIM_ROOT/venv/bin/python" "$unit/verify_gpu.py"
printf 'complete round=%s; pending visual review\n' "$ROUND" > "$status"

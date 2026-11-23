#!/usr/bin/env bash
# Complete host pass. Success receipt is technical evidence, never art approval.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
unit=tools/art/anim3d/units/arquebusier
status="$ANIM_ROOT/review/3d-v2/arquebusier-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/arquebusier-gpu-round${ROUND}.json"
log="$ANIM_ROOT/gpu-logs-arquebusier-r${ROUND}.log"
exec >> "$log" 2>&1
stage=preflight
trap 'rc=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$rc" > "$status"; exit "$rc"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
rm -f "$receipt"
printf 'checkout=%s\n' "$PWD"
git rev-parse HEAD
git status --short
command -v blender
test -s "$ANIM_ROOT/masters/arquebusier/arquebusier.blend"
test -s "$ANIM_ROOT/masters/arquebusier/plain.blend"
python="$ANIM_ROOT/venv/bin/python"
stage=prepare
"$python" "$unit/prepare.py"
stage=animate
"$unit/render.sh" animate
stage=audit
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/audit.py"
stage=render
"$unit/render.sh" render
stage=verify-masters
"$python" "$unit/check_delivery.py"
stage=pack-validate-video
"$python" "$unit/finish.py"
stage=receipt
"$python" "$unit/check_delivery.py" --receipt
printf 'complete round=%s; pending visual review\n' "$ROUND" > "$status"

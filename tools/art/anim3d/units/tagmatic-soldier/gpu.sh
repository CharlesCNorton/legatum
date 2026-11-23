#!/usr/bin/env bash
# Complete no-argument host pass; run from any directory, never bypass the gate.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
UNIT=tools/art/anim3d/units/tagmatic-soldier
status="$ANIM_ROOT/review/3d-v2/tagmatic-soldier-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/tagmatic-soldier-gpu-round${ROUND}.json"
log="$ANIM_ROOT/gpu-logs-tagmatic-soldier-r${ROUND}.log"
rm -f "$receipt"
exec >> "$log" 2>&1
stage=preflight
trap 'code=$?; if (( code != 0 )); then printf "failed stage=%s exit=%s log=%s\n" "$stage" "$code" "$log" > "$status"; fi; exit "$code"' EXIT
printf 'running round=%s log=%s\n' "$ROUND" "$log" > "$status"
printf 'round=%s checkout=%s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short -- "$UNIT" tools/art/anim3d/PLAYBOOK.md
command -v blender
"$ANIM_ROOT/venv/bin/python" "$UNIT/prepare.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$UNIT/check_gpu.py"
for stage in build bake animate audit b c d e-idle e-move e-attack e-hit e-death g; do
 printf 'STAGE %s\n' "$stage"
 "$UNIT/render.sh" "$stage"
done
stage=master-verification
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" gpu-masters
for stage in pack validate video; do
 "$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" "$stage"
done
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" receipt
printf 'complete round=%s; visual review pending; log=%s\n' "$ROUND" "$log" > "$status"
printf '%s\n' "- GPU round $ROUND: GPU512/48 stages and 256 derivatives verified; atlas, geometry and decoded MP4 validated. Visual approval remains separate." >> "$ANIM_ROOT/review/3d-v2/tagmatic-soldier-log.md"

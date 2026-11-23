#!/usr/bin/env bash
# Complete lead-side pass. No arguments; the overnight driver supplies ROUND.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
UNIT_DIR=tools/art/anim3d/units/eagle-warrior
LOG="$ANIM_ROOT/gpu-logs-eagle-warrior-r${ROUND}.log"
STATUS="$ANIM_ROOT/review/3d-v2/eagle-warrior-gpu-status.txt"
RECEIPT="$ANIM_ROOT/review/3d-v2/eagle-warrior-gpu-round${ROUND}.json"
printf 'GPU transcript: %s\n' "$LOG"
exec >>"$LOG" 2>&1
stage=preflight
trap 'code=$?; printf "failed: %s (exit %s)\n" "$stage" "$code" > "$STATUS"; exit "$code"' ERR
printf 'running: round %s\n' "$ROUND" > "$STATUS"
rm -f "$RECEIPT"
printf 'round=%s checkout=%s blender=%s\n' "$ROUND" "$PWD" "$(command -v blender)"
git rev-parse HEAD
git status --short -- "$UNIT_DIR"
for file in plain.blend eagle-warrior.blend; do test -s "$ANIM_ROOT/masters/eagle-warrior/$file"; done
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
export STAGES=b-plain,c-textured-lit,c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death
stage=animation
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/animate.py"
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/audit.py"
stage=render
"$UNIT_DIR/render.sh"
stage=master-check
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/check_delivery.py" --gpu
stage=pack
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/deliver.py" --resolution 512
stage=validate
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/validate.py"
stage=movie
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/mp4.py"
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/check_delivery.py" --gpu --receipt
printf 'complete: round %s; visual approval pending\n' "$ROUND" > "$STATUS"

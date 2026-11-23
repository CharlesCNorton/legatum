#!/usr/bin/env bash
# Run from repo root, no arguments. Driver sets ROUND; all heavy stages are serial.
set -Eeuo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
status="$ANIM_ROOT/review/3d-v2/barbarian-pikeman-gpu-status.txt"
receipt="$ANIM_ROOT/review/3d-v2/barbarian-pikeman-gpu-round${ROUND}.json"
log="$ANIM_ROOT/gpu-logs-barbarian-pikeman-r${ROUND}.log"
exec >> "$log" 2>&1
stage=preflight
trap 'code=$?; printf "failed: %s (exit %s)\n" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running: round %s\n' "$ROUND" > "$status"
rm -f "$receipt"
date -u
git rev-parse HEAD
git status --short
command -v blender
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
export STAGES=b-plain,c-textured-lit,c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death
UNIT_DIR=tools/art/anim3d/units/barbarian-pikeman
test -s "$ANIM_ROOT/masters/barbarian-pikeman/barbarian-pikeman.blend"
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/check_scene.py"
stage=animation
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/animate.py"
stage=rig-audit
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/audit.py"
stage=render
"$UNIT_DIR/render.sh"
stage=pack
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/deliver.py" --resolution 512
stage=validate
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/validate.py"
stage=movie
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/mp4.py"
stage=gpu-receipt
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/check_delivery.py"
printf 'complete: round %s; GPU512, gallery256, atlas and movie verified; pending visual review\n' "$ROUND" > "$status"

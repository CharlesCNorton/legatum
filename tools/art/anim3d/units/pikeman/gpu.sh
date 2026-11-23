#!/usr/bin/env bash
# Complete unit-local GPU handoff; no arguments, ROUND supplied by driver.
set -Eeuo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
unit=tools/art/anim3d/units/pikeman
status="$REVIEW/pikeman-gpu-status.txt"
exec >> "$ANIM_ROOT/gpu-logs-pikeman-r${ROUND}.log" 2>&1
stage=preflight
trap 'code=$?; printf "failed: %s (exit %s)\n" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running: round %s\n' "$ROUND" > "$status"
rm -f "$REVIEW/pikeman-gpu-round${ROUND}.json"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
"$ANIM_ROOT/venv/bin/python" "$unit/provenance.py"
CHECK_GPU=1 CYCLES_DEVICE=CPU blender -b --disable-autoexec --python-exit-code 1 --python "$unit/check_scene.py"
stage=animation
CYCLES_DEVICE=CPU blender -b --disable-autoexec --python-exit-code 1 --python "$unit/animate.py"
stage=audit
CYCLES_DEVICE=CPU blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
stage=render
STAGES=b-plain,c-textured-lit,c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death "$unit/render.sh"
stage=feet
blender -b --disable-autoexec --gpu-backend metal --python-exit-code 1 --python "$unit/feet.py"
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" --resolution 512
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit/validate.py"
stage=movie
"$ANIM_ROOT/venv/bin/python" "$unit/mp4.py"
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$unit/check_delivery.py"
printf 'complete: GPU512, gallery256, 160px atlas and movie verified; pending visual review\n' > "$status"

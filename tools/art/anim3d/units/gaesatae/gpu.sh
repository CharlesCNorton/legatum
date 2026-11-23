#!/usr/bin/env bash
# Complete no-argument host pass; all Blender jobs use the shared PATH gate.
set -euo pipefail
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
unit=tools/art/anim3d/units/gaesatae
status="$ANIM_ROOT/review/3d-v2/gaesatae-gpu-status.txt"
log="$ANIM_ROOT/gpu-logs-gaesatae-r${ROUND}.log"
exec >> "$log" 2>&1
trap 'rc=$?; printf "failed: %s (exit %s)\n" "$BASH_COMMAND" "$rc" > "$status"; exit "$rc"' ERR
printf 'running round %s\n' "$ROUND" > "$status"
export CYCLES_DEVICE=GPU CYCLES_BACKEND=METAL RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
# Fail early without modifying masters when required input is absent.
test -s "$ANIM_ROOT/assets/gaesatae/painting-source.png"
test -s "$ANIM_ROOT/assets/gaesatae/painting-aligned.png"
test -s "$ANIM_ROOT/masters/gaesatae/plain.blend"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/preflight.py"
# Use the saved editable rest scene, then finish/project and regenerate dependent clips.
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/project.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/animate.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/audit.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/render.py" -- all
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/feet.py"
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" --movie
"$ANIM_ROOT/venv/bin/python" "$unit/check_delivery.py" --gpu
"$ANIM_ROOT/venv/bin/python" "$unit/test_delivery.py"
printf 'complete round %s: GPU512, gallery256, atlas and MP4 verified; visual review pending\n' "$ROUND" > "$status"

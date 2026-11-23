#!/usr/bin/env bash
# No arguments; run from the repository root. All Blender jobs pass the PATH gate.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/jet-bomber
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 REQUIRE_GPU=1
export SAMPLES="${SAMPLES:-96}" ROUND="${ROUND:-1}"
status="$REVIEW/jet-bomber-gpu-status.txt"
stage=preflight
trap 'printf "FAILED round %s stage %s\n" "$ROUND" "$stage" > "$status"' ERR
"$ANIM_ROOT/venv/bin/python" "$unit/preflight.py"
CYCLES_DEVICE=CPU blender -b --disable-autoexec --python-exit-code 1 --python "$unit/devices.py"
for stage in b c d e-idle e-move e-attack e-hit e-death g; do
  "$unit/render.sh" "$stage"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
done
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
stage=delivery
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
printf 'GPU round %s: all stages rendered at 512; 256 masters, validated 160 atlas and 8-second MP4. Visual review pending.\n' "$ROUND" | tee "$status" >> "$REVIEW/jet-bomber-log.md"

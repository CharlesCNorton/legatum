#!/usr/bin/env bash
# Complete no-argument host pass. ROUND is set by the overnight driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
HERE=tools/art/anim3d/units/barbarian-scout
export ROUND="${ROUND:-2}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
STATUS="$ANIM_ROOT/review/3d-v2/barbarian-scout-gpu-status.txt"
LOG="$ANIM_ROOT/gpu-logs-barbarian-scout-r${ROUND}.log"
exec >> "$LOG" 2>&1
stage=preflight
trap 'code=$?; printf "round=%s failed stage=%s exit=%s log=%s\n" "$ROUND" "$stage" "$code" "$LOG" > "$STATUS"; exit "$code"' ERR
printf 'round=%s running log=%s\n' "$ROUND" "$LOG" > "$STATUS"
printf 'Checkout: %s\n' "$PWD"
git rev-parse HEAD
git status --short
command -v blender
for asset in painting-source.png painted-fur.png painted-linen.png; do
  test -s "$ANIM_ROOT/assets/barbarian-scout/$asset"
done
# Check the actual host device before touching any preserved editable masters.
stage=gpu-device
blender -b --disable-autoexec --python-exit-code 1 --python-expr "import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices(); assert any(d.type=='METAL' for d in p.devices), 'No Metal GPU; refusing CPU fallback'"
stage=rebuild
"$HERE/rebuild.sh"
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/audit.py"
stage=render-all
blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/render.py" -- all
stage=masters
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" gpu-check
stage=delivery-tests
"$ANIM_ROOT/venv/bin/python" "$HERE/test_post.py"
stage=pack
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" pack
stage=validate
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" validate
stage=video
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" video
printf 'round=%s complete GPU512/gallery256 atlas validated MP4 verified; visual review pending; log=%s\n' "$ROUND" "$LOG" > "$STATUS"
# Technical success never creates a visual PASS marker.

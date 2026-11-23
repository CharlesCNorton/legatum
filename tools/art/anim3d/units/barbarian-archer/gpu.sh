#!/usr/bin/env bash
# Complete lead-side pass; no arguments, run from repository root.
set -euo pipefail
cd "$(cd "$(dirname "$0")/../../../../.." && pwd)"
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unit=tools/art/anim3d/units/barbarian-archer
status="$REVIEW/barbarian-archer-gpu-status.txt"
exec > "$ANIM_ROOT/gpu-logs-barbarian-archer-r${ROUND}.log" 2>&1
stage=preflight
trap 'code=$?; echo "Failed: $stage (exit $code)" > "$status"; exit "$code"' ERR
echo "Running round $ROUND in $PWD" > "$status"
git rev-parse HEAD
command -v blender
test -f "$ANIM_ROOT/masters/barbarian-archer/master.blend"
test -f "$ANIM_ROOT/masters/barbarian-archer/refined-plain.blend"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/gpu_probe.py"
stage=animate
"$unit/run.sh" animate
stage=audit
"$unit/run.sh" audit
for stage in b c d e-idle e-move e-attack e-hit e-death g-feet; do
  "$unit/run.sh" "$stage"
done
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/check.py"
stage=movie
"$ANIM_ROOT/venv/bin/python" "$unit/video.py"
echo "Complete round $ROUND: GPU512/64, atlas and movie validated; visual review pending" > "$status"

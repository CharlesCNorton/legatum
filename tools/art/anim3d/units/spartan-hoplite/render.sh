#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ANIM_MASTER="${ANIM_MASTER:-$ANIM_ROOT/masters/spartan-hoplite/round2-3d}"
export ANIM_ATTACK_SLIDE=.43
export ANIM_SHIELD_SETTLE=1
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
export SAMPLES="${SAMPLES:-12}"
export RESOLUTION="${RESOLUTION:-256}"
stage="${1:-c}"
unit=tools/art/anim3d/units/spartan-hoplite
if [[ "$stage" == pack || "$stage" == validate || "$stage" == prepare || "$stage" == video || "$stage" == verify-gpu ]]; then
  exec "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
fi
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/pipeline.py" -- "$stage"

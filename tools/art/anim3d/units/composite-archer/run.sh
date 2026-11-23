#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}" CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
unit_dir=tools/art/anim3d/units/composite-archer
stage="${1:-c}"
case "$stage" in
  prepare) exec "$ANIM_ROOT/venv/bin/python" "$unit_dir/prepare.py" ;;
  pack) exec "$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" ;;
  validate) exec "$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" --validate-only ;;
  c|c-details|detail) export STAGE=c; script=render ;;
  d) export STAGE=e-attack; script=render ;;
  e-idle|e-move|e-attack|e-hit|e-death) export STAGE="$stage"; script=render ;;
  build|paint|animate|round|final|audit|refresh|plain_views) script="$stage" ;;
  *) echo "Unknown composite archer stage: $stage" >&2; exit 2 ;;
esac
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
blender "${args[@]}" --python "$unit_dir/$script.py"
if [[ "$stage" == build ]]; then "$ANIM_ROOT/venv/bin/python" "$unit_dir/review.py" b-plain; fi
if [[ "$stage" == final || "$stage" == round ]]; then "$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py"; fi

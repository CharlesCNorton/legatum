#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/autonomous-armour
py="$ANIM_ROOT/venv/bin/python"
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}" CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
export RESOLUTION="${RESOLUTION:-256}" SAMPLES="${SAMPLES:-8}"
run() { blender -b --disable-autoexec --python-exit-code 1 --python "$unit/$1.py" -- "${@:2}"; }
case "${1:-}" in
  build) "$py" "$unit/prepare.py"; run scene ;;
  finish) run finish; run animate ;;
  b|c|details|d|e-idle|e-move|e-attack|e-hit|e-death)
    run render "$1"; "$py" "$unit/deliver.py" review "$1" ;;
  final)
    for stage in b c details d e-idle e-move e-attack e-hit e-death; do
      run render "$stage"
      "$py" "$unit/deliver.py" review "$stage"
    done
    run audit
    "$py" "$unit/deliver.py" pack
    "$py" "$unit/deliver.py" validate
    "$py" "$unit/deliver.py" movie ;;
  pack|validate|movie) "$py" "$unit/deliver.py" "$1" ;;
  audit) run audit ;;
  *) echo 'Use build, finish, b, c, details, d, e-<clip>, final, pack, validate, movie, audit' >&2; exit 2 ;;
esac

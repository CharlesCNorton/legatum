#!/usr/bin/env bash
# Unit entry point; every Blender invocation uses the machine-wide PATH gate.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/crossbowman
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
step="${1:-render}"
printf '%s\n' "- Started $step ${STAGE:-} ($CYCLES_DEVICE)." >> "$REVIEW/crossbowman-log.md"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/$step.py"
printf '%s\n' "- Completed $step ${STAGE:-} ($CYCLES_DEVICE)." >> "$REVIEW/crossbowman-log.md"

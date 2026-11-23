#!/usr/bin/env bash
# Re-render the reviewed external master on the lead's host GPU, then pack and verify.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
source tools/art/anim3d/env.sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512
export SIEGE_REUSE_MASTER=1
test -f "$ANIM_ROOT/masters/field-cannon/field-cannon.blend"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/siege/round.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/validate.py

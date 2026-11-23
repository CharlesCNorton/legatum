#!/usr/bin/env bash
# Complete no-argument host pass. Run from repo root; never silently use CPU.
set -euo pipefail
cd "$(cd "$(dirname "$0")/../../../../.." && pwd)"
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/stealth-bomber
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-96}" ROUND="${ROUND:-1}"
log="$REVIEW/stealth-bomber-gpu-round${ROUND}.log"
receipt="$REVIEW/stealth-bomber-gpu-round${ROUND}.json"
status="$REVIEW/stealth-bomber-gpu-status.txt"
exec >> "$log" 2>&1
rm -f "$receipt"
trap 'code=$?; printf "failed round=%s exit=%s command=%s\n" "$ROUND" "$code" "$BASH_COMMAND" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
printf 'Round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
for input in stealth-bomber.blend plain.blend textures/baked/manifest.json; do
  test -f "$ANIM_ROOT/masters/stealth-bomber/$input"
done
for stage in b c d g e-idle e-move e-attack e-hit e-death; do
  "$unit/render.sh" "$stage"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" gpu-check
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" receipt
printf 'complete round=%s; pending visual review\n' "$ROUND" > "$status"
printf '%s\n' "GPU round ${ROUND}: all stages GPU512, verified 256 copies, trimmed atlas, geometry/alpha/clip checks and decoded-atlas MP4; visual acceptance remains manual." >> "$REVIEW/stealth-bomber-log.md"

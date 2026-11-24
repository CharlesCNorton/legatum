#!/usr/bin/env bash
# Complete no-argument host pass. Run from repo root; never silently use CPU.
set -euo pipefail
cd "$(cd "$(dirname "$0")/../../../../.." && pwd)"
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/bomber
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-96}" ROUND="${ROUND:-3}"
log="$REVIEW/bomber-gpu-round${ROUND}.log"
receipt="$REVIEW/bomber-gpu-round${ROUND}.json"
status="$REVIEW/bomber-gpu-status.txt"
# Retain a driver output descriptor without /dev/fd process substitution,
# which is unavailable in some sandbox shells.
exec 3>&1
printf 'GPU round %s transcript: %s\n' "$ROUND" "$log" >&3
exec >> "$log" 2>&1
rm -f "$receipt"
failure() {
  printf 'failed round=%s exit=%s command=%s\n' "$ROUND" "$1" "$2" > "$status"
  cat "$status" >&3
  exit "$1"
}
trap 'failure "$?" "$BASH_COMMAND"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
printf 'Round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
for input in bomber.blend plain.blend textures/baked/manifest.json; do
  test -f "$ANIM_ROOT/masters/bomber/$input"
done
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" inputs-check
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
cat "$status" >&3
printf '%s\n' "GPU round ${ROUND}: all stages GPU512, verified 256 copies, trimmed atlas, geometry/alpha/clip checks and decoded-atlas MP4; visual acceptance remains manual." >> "$REVIEW/bomber-log.md"

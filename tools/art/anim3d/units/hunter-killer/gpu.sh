#!/usr/bin/env bash
# Complete, serial host pass. The Blender PATH shim owns CPU/GPU scheduling.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU
export SAMPLES="${SAMPLES:-96}" RESOLUTION=512
export ROUND="${ROUND:-1}"
unit=tools/art/anim3d/units/hunter-killer
status="$REVIEW/hunter-killer-gpu-status.txt"
receipt="$REVIEW/hunter-killer-gpu-round${ROUND}.json"
transcript="$ANIM_ROOT/gpu-logs-hunter-killer-r${ROUND}.log"
rm -f "$receipt"
printf 'running round %s; transcript %s\n' "$ROUND" "$transcript" > "$status"
# Direct redirection works in restricted callers where /dev/fd process
# substitution is unavailable. Keep the original stderr for failure notices.
exec 3>&2
exec >> "$transcript" 2>&1
stage=preflight
trap 'rc=$?; printf "failed round %s stage %s exit %s\n" "$ROUND" "$stage" "$rc" > "$status"; cat "$status" >&3; exit "$rc"' ERR
date -u
git rev-parse HEAD
git status --short -- "$unit" tools/art/anim3d/PLAYBOOK.md
command -v blender
for file in model.blend plain.blend finished.blend clips/idle.blend clips/move.blend clips/attack.blend clips/hit.blend clips/death.blend; do
  test -s "$ANIM_ROOT/masters/hunter-killer/$file"
done
test ! -e "$ANIM_ROOT/masters/hunter-killer/build-pending"
stage=input-hashes
"$ANIM_ROOT/venv/bin/python" - <<'CHECK'
import hashlib,json
from pathlib import Path
for name,digest in json.loads(Path('tools/art/anim3d/units/hunter-killer/assets.lock.json').read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest, 'Changed input: '+name
CHECK
stage=scene-audit
"$unit/render.sh" audit
stage=gpu-renders-and-delivery
"$unit/render.sh" final
stage=independent-gpu-provenance
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" verify-gpu
printf 'complete round %s; GPU512, gallery256, atlas and MP4 verified; visual review pending\n' "$ROUND" > "$status"

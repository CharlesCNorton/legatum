#!/usr/bin/env bash
# One complete host GPU pass; no positional arguments.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}" RESOLUTION=512
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND="${CYCLES_BACKEND:-METAL}"
export SAMPLES="${SAMPLES:-64}"
if [[ "$CYCLES_BACKEND" == METAL ]]; then export GPU_ARGS='--gpu-backend metal'; fi
UNIT=tools/art/anim3d/units/fighter
MASTER="$ANIM_ROOT/masters/fighter"
REVIEW="$ANIM_ROOT/review/3d-v2"
mkdir -p "$REVIEW"
LOG="$REVIEW/fighter-gpu-round${ROUND}.log"
STATUS="$REVIEW/fighter-gpu-status.txt"
RECEIPT="$REVIEW/fighter-gpu-round${ROUND}.json"
exec >> "$LOG" 2>&1
stage=preflight
fail() { printf 'failed stage=%s exit=%s round=%s\n' "$stage" "$1" "$ROUND" > "$STATUS"; exit "$1"; }
trap 'fail $?' ERR
rm -f "$RECEIPT"
printf 'running round=%s\n' "$ROUND" > "$STATUS"
printf '\nFighter GPU round %s\n' "$ROUND"
git rev-parse HEAD
git status --short
command -v blender
if [[ $# -ne 0 || ! -s "$MASTER/fighter.blend" || ! -s "$MASTER/plain.blend" ]]; then
  printf 'Missing saved fighter/plain master, or unexpected arguments\n'
  fail 1
fi
# Saved final master is the reviewed input; rebuild clips so stale WIP clips cannot pass.
stage=animate
"$UNIT/render.sh" animate || fail $?
stage=audit
"$UNIT/render.sh" audit || fail $?
for stage in b c e-idle e-move e-attack e-hit e-death g; do
  "$UNIT/render.sh" "$stage" || fail $?
done
stage=verify-gpu
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" verify-gpu || fail $?
stage=pack
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" pack || fail $?
stage=movie
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" movie || fail $?
stage=receipt
"$ANIM_ROOT/venv/bin/python" - <<'PY' || fail $?
import hashlib,json,os
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/fighter';v=r/'review/3d-v2'
receipt={'round':os.environ['ROUND'],'source_sha256':hashlib.sha256((m/'fighter.blend').read_bytes()).hexdigest(),'validation':json.loads((m/'validation.json').read_text()),'audit':json.loads((m/'audit.json').read_text()),'movie_sha256':hashlib.sha256((v/f'fighter-round{os.environ["ROUND"]}.mp4').read_bytes()).hexdigest(),'art_approved':False}
(v/f'fighter-gpu-round{os.environ["ROUND"]}.json').write_text(json.dumps(receipt,indent=2)+'\n')
PY
printf 'complete round=%s; pending visual review\n' "$ROUND" > "$STATUS"
printf '%s\n' "- GPU round $ROUND: verified GPU512/256 masters, all stages, trimmed atlas, validation and MP4 complete; visual review still required." >> "$REVIEW/fighter-log.md"

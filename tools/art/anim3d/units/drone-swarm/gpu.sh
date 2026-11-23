#!/usr/bin/env bash
# Complete no-argument host GPU pass; preserves the finished art master.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/drone-swarm
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-96}" ROUND="${ROUND:-2}"
log="$ANIM_ROOT/drone-swarm-gpu-round${ROUND}.log"
status="$REVIEW/drone-swarm-gpu-status.txt"
receipt="$REVIEW/drone-swarm-gpu-round${ROUND}.json"
exec >> "$log" 2>&1
step=preflight
trap 'code=$?; printf "failed round=%s stage=%s exit=%s log=%s\n" "$ROUND" "$step" "$code" "$log" > "$status"; exit "$code"' ERR
rm -f "$receipt"
printf 'running round=%s log=%s\n' "$ROUND" "$log" > "$status"
printf 'Checkout: %s\nBlender gate: %s\n' "$PWD" "$(command -v blender)"
git rev-parse HEAD
git status --short -- "$unit" app/src/assets/units/anim/drone-swarm.json app/src/assets/units/anim/drone-swarm.webp
test -s "$ANIM_ROOT/masters/drone-swarm/drone-swarm.blend"
test -s "$ANIM_ROOT/masters/drone-swarm/plain.blend"
"$ANIM_ROOT/venv/bin/python" "$unit/provenance.py"
for stage in b c d e-idle e-move e-attack e-hit e-death g; do
  step="render-$stage"
  "$unit/render.sh" "$stage"
  step="review-$stage"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
done
step=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
step=collisions
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/collisions.py"
step=gpu-provenance
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" gpu-check
step=pack-validate-video
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
step=verify-video
"$ANIM_ROOT/venv/bin/python" "$unit/check_video.py"
step=delivery-regressions
"$ANIM_ROOT/venv/bin/python" "$unit/test_delivery.py"
step=receipt
"$ANIM_ROOT/venv/bin/python" - <<'PY'
import os,json,hashlib
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/drone-swarm';v=r/'review/3d-v2';round_=os.environ['ROUND']
report={'round':round_,'status':'complete','master_sha256':hashlib.sha256((m/'drone-swarm.blend').read_bytes()).hexdigest(),'device':'GPU','resolution':512,'validation':json.loads((m/'validation.json').read_text()),'video':json.loads((m/'video-validation.json').read_text()),'collisions':json.loads((m/'collisions.json').read_text()),'build_inputs':json.loads((m/'build-inputs.json').read_text()),'art_approval':False}
(v/f'drone-swarm-gpu-round{round_}.json').write_text(json.dumps(report,indent=2)+'\n')
PY
printf 'complete round=%s; pending visual review; log=%s\n' "$ROUND" "$log" > "$status"
printf 'GPU round %s: all stages GPU512, 256 masters, audited, trimmed atlas validated, decoded MP4 verified. Art verdict remains manual.\n' "$ROUND" >> "$REVIEW/drone-swarm-log.md"

#!/usr/bin/env bash
# No arguments; run from the repository root. ROUND is supplied by the driver.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-3}"
review="$ANIM_ROOT/review/3d-v2"
mkdir -p "$review"
status="$review/horseman-gpu-status.txt"
receipt="$review/horseman-gpu-round${ROUND}.json"
rm -f "$receipt"
printf 'running round %s\n' "$ROUND" > "$status"
exec > "$ANIM_ROOT/gpu-logs-horseman-r${ROUND}.log" 2>&1
trap 'code=$?; printf "failed round %s exit %s command %s\n" "$ROUND" "$code" "$BASH_COMMAND" > "$status"; exit "$code"' ERR
printf 'Horseman round %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
export UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU
export SAMPLES="${SAMPLES:-64}" RESOLUTION=512
python="$ANIM_ROOT/venv/bin/python"
test "$SAMPLES" -ge 64
test -f "$ANIM_ROOT/masters/horseman-3d/horseman-unpainted.blend"
# Fail before expensive rebuilds when called without a host Metal device.
blender -b --disable-autoexec --factory-startup --gpu-backend metal --python-exit-code 1 --python-expr "import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.get_devices(); assert any(d.type=='METAL' for d in p.devices), 'No Metal GPU; no CPU fallback'"
# Rebuild from the preserved baked master, so the handoff includes current source edits.
"$python" tools/art/anim3d/mounted/prepare.py
tools/art/anim3d/render.sh paint
tools/art/anim3d/render.sh animate
tools/art/anim3d/render.sh audit
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/horseman/test_source_pose.py
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/horseman/check_motion.py
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "$stage"
done
# Diagnostic copies isolate the real lower limbs; production geometry is untouched.
FEET_RESOLUTION=256 blender -b --disable-autoexec --factory-startup --gpu-backend metal --python-exit-code 1 --python tools/art/anim3d/mounted/feet.py
"$python" tools/art/anim3d/mounted/feet_review.py
"$python" tools/art/anim3d/units/horseman/check_masters.py
"$python" tools/art/anim3d/mounted/pack.py
"$python" tools/art/anim3d/mounted/validate.py
"$python" tools/art/anim3d/units/horseman/movie.py
"$python" - <<'PY'
import hashlib, json, os
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']); review=r/'review/3d-v2'
pack=json.loads((review/'horseman-pack.json').read_text())
validation=json.loads((review/'horseman-validation.json').read_text())
feet=json.loads((review/'horseman-g-feet-check.json').read_text())
assert feet['device']=='GPU' and feet['resolution']==256 and len(feet['frames'])==8
assert feet['blend_sha256']==hashlib.sha256((r/'masters/horseman-3d/clips/move.blend').read_bytes()).hexdigest()
receipt={'round':os.environ['ROUND'],'status':'complete; pending visual review','art_pass':False,
 'blend_sha256':hashlib.sha256((r/'masters/horseman-3d/horseman.blend').read_bytes()).hexdigest(),
 'bytes':pack['bytes'],'quality':pack['quality'],'validation':validation,'feet_review':feet,
 'movie':json.loads((review/f"horseman-round{os.environ['ROUND']}.json").read_text())}
(review/f"horseman-gpu-round{os.environ['ROUND']}.json").write_text(json.dumps(receipt,indent=2))
PY
printf 'complete round %s; GPU512, atlas and MP4 verified; pending visual review\n' "$ROUND" > "$status"

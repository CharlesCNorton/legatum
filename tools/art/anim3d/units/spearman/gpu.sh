#!/usr/bin/env bash
# Complete host pass. Run from repo root, no arguments; ROUND comes from driver.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-8}"
[[ "$ROUND" =~ ^[0-9]+$ ]] || { echo 'ROUND must be an integer' >&2; exit 2; }
# Keep the exact requested log even if the overnight driver's redirection changes.
# Avoid a second writer when the driver already redirects to this exact file.
log="$ANIM_ROOT/gpu-logs-spearman-r${ROUND}.log"
if ! [[ /dev/fd/1 -ef "$log" ]]; then
  exec > >(tee -a "$log") 2>&1
fi
stage=preflight
status="$REVIEW/spearman-gpu-status.txt"
failed() {
  result=$?
  printf 'round=%s status=failed stage=%s exit=%s\n' "$ROUND" "$stage" "$result" > "$status"
  printf '%s\n' "- GPU round $ROUND failed at $stage (exit $result); inspect gpu-logs-spearman-r${ROUND}.log before judging this pass." >> "$REVIEW/spearman-log.md"
  exit "$result"
}
trap failed ERR
printf 'round=%s status=running started=%s\n' "$ROUND" "$(date -u +%FT%TZ)" > "$status"
printf 'Spearman GPU round %s | %s | checkout %s\n' "$ROUND" "$(date -u +%FT%TZ)" "$PWD"
printf 'Revision %s | Blender gate %s\n' "$(git rev-parse HEAD)" "$(command -v blender)"
git status --short -- tools/art/anim3d app/src/assets/units/anim/spearman.json app/src/assets/units/anim/spearman.webp
printf '%s\n' "- GPU round $ROUND started: full Cycles GPU pass requested." >> "$REVIEW/spearman-log.md"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND="${CYCLES_BACKEND:-METAL}"
export RESOLUTION=512 SAMPLES="${SAMPLES:-64}" GRADE=1
# Fail before expensive cloth baking if the host cannot expose a GPU.
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman/preflight.py
stage=project
tools/art/anim3d/render.sh project
stage=scene-checks
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/spearman/check_scene.py
# Regenerate every clip from the current master before final renders/audit.
for clip in idle move attack hit death; do
  stage="animate-$clip"
  tools/art/anim3d/render.sh "animate-$clip"
done
# Plain geometry review uses the same calibrated camera and no texture shaders.
stage=b
SPEARMAN_PLAIN=1 tools/art/anim3d/render.sh b
stage=c
tools/art/anim3d/render.sh c
stage=detail
tools/art/anim3d/render.sh detail
stage=d
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  stage="e-$clip"
  tools/art/anim3d/render.sh "e-$clip"
done
stage=audit
tools/art/anim3d/render.sh audit
stage=delivery
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/details.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/test_pipeline.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py validate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py movie
printf '%s\n' "- GPU round $ROUND finished: all stages, masters, atlas validation and movie complete; visual review pending." >> "$REVIEW/spearman-log.md"
printf 'round=%s status=complete finished=%s visual_review=pending\n' "$ROUND" "$(date -u +%FT%TZ)" > "$status"
# PASS is a visual judgment after reviewing these outputs; never write it here.
printf '%s\n' "GPU handoff complete: spearman round $ROUND; visual review still required."

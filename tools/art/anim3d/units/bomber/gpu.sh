#!/usr/bin/env bash
# Complete no-argument lead handoff, from repository root. Never rebuild art.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/bomber
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-96}" ROUND="${ROUND:-1}"
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  "$unit/render.sh" "$stage"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
ffprobe -v error -show_entries stream=codec_name,pix_fmt,width,height,nb_frames -show_entries format=duration -of json "$REVIEW/bomber-round${ROUND}.mp4"
printf '%s\n' "GPU round ${ROUND}: rendered every stage at 512; retained 256 masters; packed/validated 160 atlas and wrote round MP4. Art verdict remains manual." >> "$REVIEW/bomber-log.md"

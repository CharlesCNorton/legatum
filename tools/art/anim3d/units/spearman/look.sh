#!/usr/bin/env bash
# Painted Eevee look, end to end, for one master folder (spearman.blend, clips/, spearman-source.png).
#   look.sh MASTER_DIR OUT_DIR [LOOK_DIR] [CLIP_RES]
# 1. flat ID pass (CPU slot)        2. part paint textures      3. ramp-input pass (Eevee)
# 4. ramps fitted to the painting   5. rest at 1280 + all five clips (Eevee)   6. masters, atlas, sheet, movie
# Every Blender call goes through the gate; Eevee calls take the machine-wide GPU lock.
# Nothing is saved into the .blend files and nothing is written under app/.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
master="$1"; out="$2"; look="${3:-$master/look}"; res="${4:-640}"
gate="${BLENDER_GATE:-$HOME/LegatumRuns/anim-pilot/bin/blender-slot}"
here=tools/art/anim3d/units/spearman
py="$ANIM_ROOT/venv/bin/python"
run() { "$gate" --factory-startup --disable-autoexec --python-exit-code 1 "$@"; }
mkdir -p "$out" "$look"
run --python $here/look.py -- "$master/spearman.blend" "$look" --mode id --look "$look"
"$py" $here/look_textures.py "$master/spearman-source.png" "$look/id.png" "$look"
run --gpu-backend metal --python $here/look.py -- "$master/spearman.blend" "$look" --name light --set debug=6 --look "$look"
"$py" $here/look_textures.py "$master/spearman-source.png" "$look/id.png" "$look" "$look/light.png"
run --gpu-backend metal --python $here/look.py -- "$master/spearman.blend" "$out/frames" --look "$look"
for clip in idle move attack hit death; do
  run --gpu-backend metal --python $here/look.py -- "$master/clips/$clip/$clip.blend" "$out/frames/$clip" --frames clip --res "$res" --look "$look"
done
"$py" $here/look_deliver.py "$out/frames" "$out" --tag spearman-look
"$py" $here/look_compare.py "$out/frames/rest.png" "$out/spearman-look-rest-compare.png"

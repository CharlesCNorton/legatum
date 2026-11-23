#!/usr/bin/env bash
# No arguments. Run from this checkout; the overnight driver provides ROUND.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512
export SIEGE_REUSE_MASTER=1 SIEGE_STAGES=b,c,detail,d,e-idle,e-move,e-attack,e-hit,e-death
export ROUND="${ROUND:-4}"
test -f "$ANIM_ROOT/masters/field-cannon/field-cannon.blend"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/siege/round.py
# Refuse to label preview-sized or stale files as the required GPU masters.
"$ANIM_ROOT/venv/bin/python" - <<'VERIFY_MASTERS'
import json, os
from pathlib import Path
from PIL import Image
root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/field-cannon'
counts = {'b': 3, 'c': 1, 'detail': 1, 'd': 4,
          'e-idle': 8, 'e-move': 8, 'e-attack': 10, 'e-hit': 4, 'e-death': 10}
for stage, expected in counts.items():
    folder = master / 'renders' / stage
    provenance = json.loads((folder / 'render.json').read_text())
    assert (provenance['device'], provenance['resolution'], provenance['samples']) == ('GPU', 512, 64), stage
    files = sorted(folder.glob('*.png'))
    assert len(files) == expected, (stage, len(files))
    for path in files:
        assert Image.open(path).size == (512, 512), path
        assert Image.open(master / 'gallery256' / stage / path.name).size == (256, 256), path
print('PASS: all stages GPU64, 40 animation masters at512, corresponding gallery256 copies')
VERIFY_MASTERS
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/validate.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/video.py
# Size/geometry success is not art approval: never manufacture a PASS marker here.

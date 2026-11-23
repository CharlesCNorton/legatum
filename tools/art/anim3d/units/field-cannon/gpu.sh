#!/usr/bin/env bash
# No arguments. Run from this checkout; the overnight driver provides ROUND.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ANIM_FAMILY=siege RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64 RESOLUTION=512
export SIEGE_REUSE_MASTER=1 SIEGE_STAGES=b,c,detail,d,e-idle,e-move,e-attack,e-hit,e-death
export ROUND="${ROUND:-5}"
test -f "$ANIM_ROOT/masters/field-cannon/field-cannon.blend"
# Keep a unit-owned transcript even when the driver's outer log path is missing.
exec > >(tee "$REVIEW/field-cannon-round${ROUND}-gpu.log") 2>&1
printf 'Field cannon round %s: Cycles GPU64 at 512 px; begin %s\n' "$ROUND" "$(date -u +%FT%TZ)"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/siege/round.py
# Refuse to label preview-sized or stale files as the required GPU masters.
"$ANIM_ROOT/venv/bin/python" - <<'VERIFY_MASTERS'
import json, os, hashlib
from pathlib import Path
from PIL import Image
root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/field-cannon'
counts = {'b': 3, 'c': 1, 'detail': 1, 'd': 4,
          'e-idle': 8, 'e-move': 8, 'e-attack': 10, 'e-hit': 4, 'e-death': 10}
for stage, expected in counts.items():
    folder = master / 'renders' / stage
    provenance = json.loads((folder / 'render.json').read_text())
    assert provenance['engine'] == 'CYCLES', stage
    blend = master / ('field-cannon-plain.blend' if stage == 'b' else 'field-cannon.blend')
    if stage.startswith('e-') or stage == 'd':
        blend = master / 'clips' / (('attack' if stage == 'd' else stage[2:]) + '.blend')
    assert provenance['blend_sha256'] == hashlib.sha256(blend.read_bytes()).hexdigest(), stage
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
"$ANIM_ROOT/venv/bin/python" - <<'RECEIPT'
import datetime, hashlib, json, os
from pathlib import Path
root = Path(os.environ['ANIM_ROOT'])
review = root / 'review/3d-v2'
atlas = Path('app/src/assets/units/anim/field-cannon.webp')
round_id = os.environ['ROUND']
receipt = {
    'round': round_id, 'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'engine': 'CYCLES', 'device': 'GPU', 'samples': 64, 'master_size': 512, 'gallery_size': 256,
    'atlas_bytes': atlas.stat().st_size, 'atlas_sha256': hashlib.sha256(atlas.read_bytes()).hexdigest(),
    'pack': json.loads((review / 'field-cannon-pack.json').read_text()),
    'validation': json.loads((review / 'field-cannon-validation.json').read_text()),
    'video': json.loads((review / f'field-cannon-round{round_id}-video.json').read_text()),
    'art_approved': False,
}
assert receipt['validation']['contract'] == 'PASS'
assert receipt['video']['atlas_sha256'] == receipt['atlas_sha256']
(review / f'field-cannon-round{round_id}-gpu-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('GPU pass complete; receipt saved. Visual art review remains required.')
RECEIPT
# Size/geometry success is not art approval: never manufacture a PASS marker here.

# Jet bomber, round 2

Original solid eight-engine swept-wing aircraft registered to its own painting.
The vehicles/aircraft chapter in `../../PLAYBOOK.md` documents the method and
trimmed atlas format. `SOURCES.md` and `inputs.json` pin the consumed images.

Build with `tools/art/anim3d/units/jet-bomber/render.sh build`. CPU previews use
`RESOLUTION=256 SAMPLES=8 .../render.sh <stage>` followed immediately by
`.../deliver.py <stage>` using the external Python venv. Stages: b, c, d,
e-idle, e-move, e-attack, e-hit, e-death, g.

Lead handoff: **`ROUND=2 tools/art/anim3d/units/jet-bomber/gpu.sh`**, no arguments,
from repo root. It renders all stages at GPU512, exports 512/256 masters,
produces all reviews, audits, validates the 160px trimmed WebP/JSON and writes
the 8-second five-clip H.264 movie. Requires existing external masters and
Metal; no silent CPU fallback. No build, upload, push or PASS is implicit.

Round-two art remains a candidate pending GPU review. Full-depth fuselage and
pod contours, the stone rim, solid finned bombs and continuous support/wing
damage have been revised from the successful round-one GPU output. Identity
reads clearly at 64; wing contours and projected lighting still differ at 256.
See `~/LegatumRuns/anim-pilot/review/3d-v2/jet-bomber-log.md` for actual evidence.
